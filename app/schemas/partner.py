"""Partner schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema
from app.models.partner import KYCStatus, DocumentType


class PartnerProfileUpdate(BaseSchema):
    business_name: Optional[str] = Field(None, max_length=150)
    contact_person: Optional[str] = Field(None, max_length=120)
    email: Optional[EmailStr] = None
    address_line: Optional[str] = Field(None, max_length=300)
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = Field(None, max_length=10)
    hub_lat: Optional[float] = None
    hub_lng: Optional[float] = None


class PartnerBankUpdate(BaseSchema):
    bank_account_number: str = Field(..., min_length=6, max_length=40)
    bank_ifsc: str = Field(..., min_length=4, max_length=20)
    bank_holder_name: str = Field(..., min_length=2, max_length=120)


class DocumentOut(BaseSchema):
    id: int
    doc_type: DocumentType
    doc_number: Optional[str]
    file_url: str
    is_verified: bool
    uploaded_at: datetime


class PartnerOut(BaseSchema):
    id: int
    phone: str
    email: Optional[str]
    business_name: Optional[str]
    contact_person: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    address_line: Optional[str]
    hub_lat: Optional[float]
    hub_lng: Optional[float]
    kyc_status: KYCStatus
    kyc_remarks: Optional[str]
    is_active: bool
    phone_verified: bool
    total_earnings: float
    total_bookings: int
    avg_rating: float
    created_at: datetime


class PartnerDetailOut(PartnerOut):
    documents: List[DocumentOut] = []
    bank_account_number: Optional[str]
    bank_ifsc: Optional[str]
    bank_holder_name: Optional[str]


class KYCReviewRequest(BaseSchema):
    status: KYCStatus
    remarks: Optional[str] = None
