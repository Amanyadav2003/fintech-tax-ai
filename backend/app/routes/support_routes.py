"""Authenticated user support tickets and server-authorized support access."""

import os
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models import SupportMessage, SupportTicket, User
from ..utils.database import get_db
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/api/support", tags=["support"])
VALID_CATEGORIES = {"Tax Calculation", "Tax Regime", "Deduction", "Document Upload", "Filing Question", "Account/Login Assistance", "Technical Issue", "Other"}
VALID_STATUSES = {"Open", "In Progress", "Resolved"}


class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=160)
    category: str
    description: str = Field(..., min_length=1, max_length=5000)


class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class StatusUpdate(BaseModel):
    status: str


def _serialize_message(message: SupportMessage) -> dict:
    return {"id": message.id, "sender_type": message.sender_type, "sender_user_id": message.sender_user_id, "message": message.message, "created_at": message.created_at}


def _serialize_ticket(ticket: SupportTicket, messages=None, owner=None) -> dict:
    result = {"id": ticket.id, "ticket_code": ticket.ticket_code, "subject": ticket.subject, "description": ticket.description, "category": ticket.category, "status": ticket.status, "created_at": ticket.created_at, "updated_at": ticket.updated_at}
    if owner:
        result["owner"] = {"id": owner.id, "name": owner.name, "email": owner.email}
    if messages is not None:
        result["messages"] = [_serialize_message(item) for item in messages]
    return result


def _ticket_or_404(ticket_id: int, current_user: User, db: Session) -> SupportTicket:
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id, SupportTicket.user_id == current_user.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    return ticket


def _is_support_admin(user: User) -> bool:
    configured = {email.strip().lower() for email in os.getenv("SUPPORT_ADMIN_EMAILS", "").split(",") if email.strip()}
    return user.email.strip().lower() in configured


def _require_support_admin(current_user: User = Depends(get_current_user)) -> User:
    if not _is_support_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Support admin access required")
    return current_user


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="Invalid support category")
    ticket = SupportTicket(ticket_code=f"TM-{datetime.utcnow().year}-{uuid4().hex[:8].upper()}", user_id=current_user.id, subject=payload.subject.strip(), description=payload.description.strip(), category=payload.category, status="Open")
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return _serialize_ticket(ticket, messages=[])


@router.get("/tickets")
def list_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [_serialize_ticket(ticket) for ticket in db.query(SupportTicket).filter(SupportTicket.user_id == current_user.id).order_by(SupportTicket.updated_at.desc()).all()]


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = _ticket_or_404(ticket_id, current_user, db)
    messages = db.query(SupportMessage).filter(SupportMessage.ticket_id == ticket.id).order_by(SupportMessage.created_at.asc()).all()
    return _serialize_ticket(ticket, messages=messages)


@router.post("/tickets/{ticket_id}/messages")
def add_user_message(ticket_id: int, payload: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = _ticket_or_404(ticket_id, current_user, db)
    ticket.status = "Open" if ticket.status == "Resolved" else ticket.status
    ticket.updated_at = datetime.utcnow()
    message = SupportMessage(ticket_id=ticket.id, sender_user_id=current_user.id, sender_type="user", message=payload.message.strip())
    db.add(message)
    db.commit()
    db.refresh(message)
    return _serialize_message(message)


@router.get("/admin/tickets")
def admin_list_tickets(status_filter: str | None = None, current_user: User = Depends(_require_support_admin), db: Session = Depends(get_db)):
    query = db.query(SupportTicket)
    if status_filter:
        if status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=422, detail="Invalid ticket status")
        query = query.filter(SupportTicket.status == status_filter)
    return [_serialize_ticket(ticket, owner=db.query(User).filter(User.id == ticket.user_id).first()) for ticket in query.order_by(SupportTicket.updated_at.desc()).all()]


@router.get("/admin/tickets/{ticket_id}")
def admin_get_ticket(ticket_id: int, current_user: User = Depends(_require_support_admin), db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    messages = db.query(SupportMessage).filter(SupportMessage.ticket_id == ticket.id).order_by(SupportMessage.created_at.asc()).all()
    return _serialize_ticket(ticket, messages=messages, owner=db.query(User).filter(User.id == ticket.user_id).first())


@router.patch("/admin/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: int, payload: StatusUpdate, current_user: User = Depends(_require_support_admin), db: Session = Depends(get_db)):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid ticket status")
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    ticket.status = payload.status
    ticket.updated_at = datetime.utcnow()
    db.commit()
    return _serialize_ticket(ticket)


@router.post("/admin/tickets/{ticket_id}/messages")
def add_admin_message(ticket_id: int, payload: MessageCreate, current_user: User = Depends(_require_support_admin), db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    message = SupportMessage(ticket_id=ticket.id, sender_user_id=current_user.id, sender_type="support", message=payload.message.strip())
    ticket.status = "In Progress"
    ticket.updated_at = datetime.utcnow()
    db.add(message)
    db.commit()
    db.refresh(message)
    return _serialize_message(message)