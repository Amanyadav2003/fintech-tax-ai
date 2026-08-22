from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models import Expense, User
from ..utils.database import get_db
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/api/expenses", tags=["expenses"])
VALID_CATEGORIES = {"80C Investment", "Medical/Insurance", "Rent", "Home Loan", "Donations", "Other"}


class ExpenseCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str
    description: Optional[str] = Field(default=None, max_length=300)
    date: datetime


def _serialize(expense: Expense):
    return {"id": expense.id, "amount": expense.amount, "category": expense.category, "description": expense.description, "date": expense.date, "created_at": expense.created_at}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid expense category")
    expense = Expense(user_id=current_user.id, amount=payload.amount, category=payload.category, description=payload.description, date=payload.date)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _serialize(expense)


@router.get("")
def list_expenses(month: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}$"), category: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    if month:
        year, month_number = map(int, month.split("-"))
        start = datetime(year, month_number, 1)
        end = datetime(year + (month_number == 12), 1 if month_number == 12 else month_number + 1, 1)
        query = query.filter(Expense.date >= start, Expense.date < end)
    if category:
        query = query.filter(Expense.category == category)
    return [_serialize(expense) for expense in query.order_by(Expense.date.desc(), Expense.created_at.desc()).all()]


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted"}