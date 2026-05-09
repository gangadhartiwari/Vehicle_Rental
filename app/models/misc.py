"""OTP, Rating, and Admin models."""
from datetime import datetime
import enum
from sqlalchemy import String, Boolean, DateTime, Float, Integer, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class OTPPurpose(str, enum.Enum):
    USER_LOGIN = "USER_LOGIN"
    PARTNER_LOGIN = "PARTNER_LOGIN"
    USER_REGISTER = "USER_REGISTER"
    PARTNER_REGISTER = "PARTNER_REGISTER"
    BOOKING_PICKUP = "BOOKING_PICKUP"
    BOOKING_DROPOFF = "BOOKING_DROPOFF"


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(15), index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[OTPPurpose] = mapped_column(Enum(OTPPurpose), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), unique=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    partner_id: Mapped[int] = mapped_column(Integer, ForeignKey("partners.id", ondelete="CASCADE"), index=True)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="rating")
    user = relationship("User", back_populates="ratings_given")
    vehicle = relationship("Vehicle", back_populates="ratings")


class AdminRole(str, enum.Enum):
    SUPERADMIN = "SUPERADMIN"
    OPERATIONS = "OPERATIONS"
    SUPPORT = "SUPPORT"


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[AdminRole] = mapped_column(Enum(AdminRole), default=AdminRole.OPERATIONS)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
