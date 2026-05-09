"""Vehicle inventory model."""
from datetime import datetime
import enum
from sqlalchemy import String, Boolean, DateTime, Float, Integer, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class VehicleType(str, enum.Enum):
    BIKE = "BIKE"
    CAR = "CAR"
    AUTO = "AUTO"


class FuelType(str, enum.Enum):
    PETROL = "PETROL"
    DIESEL = "DIESEL"
    ELECTRIC = "ELECTRIC"
    CNG = "CNG"


class TransmissionType(str, enum.Enum):
    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"


class VehicleStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    INACTIVE = "INACTIVE"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    partner_id: Mapped[int] = mapped_column(Integer, ForeignKey("partners.id", ondelete="CASCADE"), index=True)

    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    registration_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)

    fuel_type: Mapped[FuelType] = mapped_column(Enum(FuelType), default=FuelType.PETROL)
    transmission: Mapped[TransmissionType] = mapped_column(Enum(TransmissionType), default=TransmissionType.MANUAL)
    seats: Mapped[int] = mapped_column(Integer, default=2)

    # Pricing
    hourly_rate: Mapped[float] = mapped_column(Float, nullable=False)
    daily_rate: Mapped[float] = mapped_column(Float, nullable=False)
    weekly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    security_deposit: Mapped[float] = mapped_column(Float, default=2000.0)

    # Pickup location
    pickup_address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    pickup_lat: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    pickup_lng: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    pickup_city: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    # Media + extras
    images: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated URLs
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    features: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated

    status: Mapped[VehicleStatus] = mapped_column(Enum(VehicleStatus), default=VehicleStatus.AVAILABLE, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_bookings: Mapped[int] = mapped_column(Integer, default=0)

    # Vehicle docs
    rc_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    rc_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    insurance_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    insurance_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    insurance_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pollution_cert_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    partner = relationship("Partner", back_populates="vehicles")
    bookings = relationship("Booking", back_populates="vehicle")
    ratings = relationship("Rating", back_populates="vehicle", cascade="all, delete-orphan")
