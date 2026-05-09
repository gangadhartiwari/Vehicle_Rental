"""User (rider/customer) model."""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    profile_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # KYC for renting (driver's licence)
    dl_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    dl_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dl_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Default location (last known)
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    ratings_given = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
