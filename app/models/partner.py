"""Partner (vehicle provider) and their KYC documents."""
from datetime import datetime
import enum
from sqlalchemy import String, Boolean, DateTime, Float, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class KYCStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentType(str, enum.Enum):
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    GST = "GST"
    BUSINESS_LICENSE = "BUSINESS_LICENSE"
    BANK_PROOF = "BANK_PROOF"
    ADDRESS_PROOF = "ADDRESS_PROOF"


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    business_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Address / hub
    address_line: Mapped[str | None] = mapped_column(String(300), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    hub_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    hub_lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    # KYC
    kyc_status: Mapped[KYCStatus] = mapped_column(Enum(KYCStatus), default=KYCStatus.PENDING)
    kyc_remarks: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Bank
    bank_account_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    bank_ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_holder_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Earnings (denormalised for fast dashboard reads)
    total_earnings: Mapped[float] = mapped_column(Float, default=0.0)
    total_bookings: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("PartnerDocument", back_populates="partner", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="partner", cascade="all, delete-orphan")


class PartnerDocument(Base):
    __tablename__ = "partner_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    partner_id: Mapped[int] = mapped_column(Integer, ForeignKey("partners.id", ondelete="CASCADE"), index=True)
    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    doc_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    partner = relationship("Partner", back_populates="documents")
