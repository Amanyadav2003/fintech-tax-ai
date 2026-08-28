"""Authenticated document storage and conservative field extraction."""

import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..models import Document, User
from ..utils.database import get_db
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/api/documents", tags=["documents"])
UPLOADS_DIR = Path("/app/uploads/documents")
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {"form16", "bank_interest", "80c", "80d", "home_loan", "rent", "other"}
DOCUMENT_LABELS = {
    "form16": "Form 16",
    "bank_interest": "Bank interest certificates",
    "80c": "80C investment proofs",
    "80d": "80D health receipts",
    "home_loan": "Home loan certificate",
    "rent": "Rent receipts",
    "other": "Other Documents",
}

CLASSIFICATION_HINTS = {
    "form16": ("form 16", "form16", "salary certificate"),
    "bank_interest": ("interest certificate", "interest earned", "fixed deposit"),
    "80c": ("ppf", "elss", "lic premium", "section 80c", "80c"),
    "80d": ("health insurance", "medical insurance", "section 80d", "80d"),
    "home_loan": ("home loan", "housing loan", "section 24"),
    "rent": ("rent receipt", "rent paid", "section 80gg"),
}


def _suggest_category(text: str) -> dict:
    normalized = text.lower()
    matches = [category for category, hints in CLASSIFICATION_HINTS.items() if any(hint in normalized for hint in hints)]
    if len(matches) == 1:
        category = matches[0]
        return {"category": category, "label": DOCUMENT_LABELS[category], "confidence": "possible", "message": f"This looks like {DOCUMENT_LABELS[category]}. Please confirm before applying."}
    return {"category": None, "label": None, "confidence": "unknown", "message": "Couldn't determine document type - please categorize manually or leave in Other Documents."}


def _extract_pages(contents: bytes, filename: str) -> list[str]:
    if not filename.lower().endswith(".pdf"):
        return []
    try:
        from pypdf import PdfReader
        import io
        return [page.extract_text() or "" for page in PdfReader(io.BytesIO(contents)).pages]
    except Exception:
        return []


def _section_suggestions(contents: bytes, filename: str) -> list[dict]:
    pages = _extract_pages(contents, filename)
    if len(pages) < 2:
        return []
    sections = []
    for page_number, text in enumerate(pages, start=1):
        suggestion = _suggest_category(text)
        if not sections or suggestion["category"] != sections[-1]["suggested_category"]:
            sections.append({"pages": [page_number], "suggested_category": suggestion["category"], "suggested_label": suggestion["label"], "message": suggestion["message"]})
        else:
            sections[-1]["pages"].append(page_number)
    return sections if len(sections) > 1 else []


def _extract_text(contents: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(contents)).pages)
        except Exception:
            # Recover visible parenthesized text from simple or damaged PDFs.
            raw = contents.decode("latin1", errors="ignore")
            return "\n".join(re.findall(r"\(([^()]*)\)", raw))
    try:
        from PIL import Image
        import io
        import pytesseract
        return pytesseract.image_to_string(Image.open(io.BytesIO(contents)))
    except Exception:
        return ""


def _amount(text: str, labels: list[str]) -> float | None:
    for label in labels:
        match = re.search(rf"{label}[^0-9₹]{{0,80}}₹?\s*([0-9][0-9,]*(?:\.\d+)?)", text, re.I)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def extract_values(document_type: str, text: str) -> dict:
    values = {}
    if document_type == "form16":
        salary = _amount(text, ["gross salary", "gross total income", "salary"])
        tds = _amount(text, ["total tax deducted", "tds deducted", "tax deducted"])
        employer = re.search(r"(?:employer|name of employer)\s*[:\-]?\s*([^\n]{3,80})", text, re.I)
        if salary is not None: values["salary"] = salary
        if tds is not None: values["tds_deducted"] = tds
        if employer: values["employer_name"] = employer.group(1).strip()
    elif document_type == "bank_interest":
        value = _amount(text, ["total interest", "interest earned", "interest amount"])
        if value is not None: values["interest"] = value
    elif document_type == "80c":
        value = _amount(text, ["total invested", "investment amount", "amount invested"])
        if value is not None: values["investments_80c"] = value
    elif document_type == "80d":
        value = _amount(text, ["premium paid", "premium amount", "health insurance premium"])
        if value is not None: values["health_insurance_80d"] = value
    elif document_type == "home_loan":
        value = _amount(text, ["interest paid", "interest component", "section 24"])
        if value is not None: values["home_loan_interest_24b"] = value
    elif document_type == "rent":
        value = _amount(text, ["annual rent", "total rent", "rent paid"])
        if value is not None: values["rent_paid_80gg"] = value
    return values


@router.post("/upload")
async def upload_document(
    document_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if document_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported document type")
    if file.content_type not in {"application/pdf", "image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail="Only PDF, JPG, and PNG files are supported")
    contents = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(contents) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Documents must be 5MB or smaller")
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "document").suffix.lower()
    destination = UPLOADS_DIR / f"{current_user.id}_{uuid4().hex}{suffix}"
    destination.write_bytes(contents)
    text = _extract_text(contents, file.filename or "")
    extracted = extract_values(document_type, text) if document_type != "other" else {}
    metadata = {"reviewed": False, "classification": _suggest_category(text) if document_type == "other" else None, "sections": _section_suggestions(contents, file.filename or "")}
    extracted_payload = {"values": extracted, "metadata": metadata}
    document = Document(user_id=current_user.id, document_type=document_type, file_path=str(destination), original_filename=file.filename or "document", extracted_data=extracted_payload)
    db.add(document)
    db.commit()
    db.refresh(document)
    return {"id": document.id, "document_type": document.document_type, "label": DOCUMENT_LABELS[document_type], "original_filename": document.original_filename, "extracted_data": extracted, "metadata": metadata, "uploaded_at": document.uploaded_at.isoformat(), "extraction_note": "Values were suggested from PDF text or image OCR. Review every value before using it; extraction can miss or misread fields."}


@router.get("")
def list_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = []
    for item in db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.uploaded_at.desc()).all():
        payload = item.extracted_data or {}
        values = payload.get("values", payload) if isinstance(payload, dict) else {}
        metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
        result.append({"id": item.id, "document_type": item.document_type, "label": DOCUMENT_LABELS.get(item.document_type, item.document_type), "original_filename": item.original_filename, "extracted_data": values, "metadata": metadata, "uploaded_at": item.uploaded_at.isoformat()})
    return result


@router.get("/{document_id}/download")
def download_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not item or not Path(item.file_path).exists():
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(item.file_path, filename=item.original_filename)


@router.delete("/{document_id}")
def delete_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")
    path = Path(item.file_path)
    if path.exists(): path.unlink()
    db.delete(item)
    db.commit()
    return {"deleted": True}