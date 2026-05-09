"""Partner profile, bank, and KYC document endpoints."""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_partner
from app.db.session import get_db
from app.models import Partner, PartnerDocument, KYCStatus, DocumentType
from app.schemas import (
    PartnerProfileUpdate, PartnerBankUpdate, PartnerDetailOut, DocumentOut,
    MessageResponse,
)
from app.services.file_service import save_upload

router = APIRouter(prefix="/partners", tags=["Partner Profile"])


@router.get("/me", response_model=PartnerDetailOut)
def get_me(partner: Partner = Depends(get_current_partner)):
    return partner


@router.patch("/me", response_model=PartnerDetailOut)
def update_profile(payload: PartnerProfileUpdate, partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(partner, k, v)
    db.commit()
    db.refresh(partner)
    return partner


@router.post("/me/bank", response_model=PartnerDetailOut)
def update_bank(payload: PartnerBankUpdate, partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    partner.bank_account_number = payload.bank_account_number
    partner.bank_ifsc = payload.bank_ifsc.upper()
    partner.bank_holder_name = payload.bank_holder_name
    db.commit()
    db.refresh(partner)
    return partner


@router.post("/me/documents", response_model=DocumentOut)
def upload_document(
    doc_type: DocumentType = Form(...),
    doc_number: str | None = Form(None),
    file: UploadFile = File(...),
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    rel = save_upload(file, "kyc")
    # Replace existing doc of same type
    db.query(PartnerDocument).filter(
        PartnerDocument.partner_id == partner.id,
        PartnerDocument.doc_type == doc_type,
    ).delete()
    doc = PartnerDocument(
        partner_id=partner.id,
        doc_type=doc_type,
        doc_number=doc_number,
        file_url=rel,
    )
    db.add(doc)

    # Auto-set KYC to SUBMITTED on first upload
    if partner.kyc_status == KYCStatus.PENDING:
        partner.kyc_status = KYCStatus.SUBMITTED
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/me/documents", response_model=list[DocumentOut])
def list_my_documents(partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    return db.query(PartnerDocument).filter(PartnerDocument.partner_id == partner.id).all()


@router.delete("/me/documents/{doc_id}", response_model=MessageResponse)
def delete_document(doc_id: int, partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    doc = db.query(PartnerDocument).filter(
        PartnerDocument.id == doc_id, PartnerDocument.partner_id == partner.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    db.delete(doc)
    db.commit()
    return MessageResponse(message="Deleted")


@router.post("/me/submit-kyc", response_model=PartnerDetailOut)
def submit_kyc(partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    required = {DocumentType.AADHAAR, DocumentType.PAN}
    have = {d.doc_type for d in partner.documents}
    if not required.issubset(have):
        missing = required - have
        raise HTTPException(400, f"Missing required docs: {[d.value for d in missing]}")
    if partner.kyc_status not in (KYCStatus.REJECTED, KYCStatus.PENDING, KYCStatus.SUBMITTED):
        raise HTTPException(400, f"KYC already {partner.kyc_status.value}")
    partner.kyc_status = KYCStatus.SUBMITTED
    db.commit()
    db.refresh(partner)
    return partner
