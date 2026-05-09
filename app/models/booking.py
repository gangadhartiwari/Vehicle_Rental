"""Booking model."""
from datetime import datetime
import enum
from sqlalchemy import String, DateTime, Float, Integer, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class BookingStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    ONGOING = "ONGOING"           # vehicle picked up
    COMPLETED = "COMPLETED"       # vehicle returned
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="RESTRICT"), index=True)
    partner_id: Mapped[int] = mapped_column(Integer, ForeignKey("partners.id", ondelete="RESTRICT"), index=True)

    pickup_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dropoff_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    actual_pickup_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_dropoff_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    pickup_location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    dropoff_location: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Pricing breakdown
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False)
    base_amount: Mapped[float] = mapped_column(Float, nullable=False)
    gst_amount: Mapped[float] = mapped_column(Float, default=0.0)
    security_deposit: Mapped[float] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)

    # Late fees / damages applied at completion
    late_fee: Mapped[float] = mapped_column(Float, default=0.0)
    damage_charges: Mapped[float] = mapped_column(Float, default=0.0)
    final_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.PENDING_PAYMENT, index=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancelled_by: Mapped[str | None] = mapped_column(String(20), nullable=True)  # user/partner/admin
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # OTPs for handover (start) and return (end)
    pickup_otp: Mapped[str | None] = mapped_column(String(8), nullable=True)
    dropoff_otp: Mapped[str | None] = mapped_column(String(8), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    vehicle = relationship("Vehicle", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    rating = relationship("Rating", back_populates="booking", uselist=False, cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), unique=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str | None] = mapped_column(String(40), nullable=True)  # upi, card, netbanking, wallet, cod
    transaction_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    gateway: Mapped[str | None] = mapped_column(String(40), nullable=True)
    gateway_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="payment")
