"""Vehicle schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import Field, field_validator
from app.schemas.common import BaseSchema
from app.models.vehicle import VehicleType, FuelType, TransmissionType, VehicleStatus


class VehicleCreate(BaseSchema):
    vehicle_type: VehicleType
    brand: str = Field(..., max_length=80)
    model: str = Field(..., max_length=120)
    year: int = Field(..., ge=1990, le=2100)
    color: Optional[str] = None
    registration_number: str = Field(..., min_length=4, max_length=20)
    fuel_type: FuelType = FuelType.PETROL
    transmission: TransmissionType = TransmissionType.MANUAL
    seats: int = Field(2, ge=1, le=20)
    hourly_rate: float = Field(..., gt=0)
    daily_rate: float = Field(..., gt=0)
    weekly_rate: Optional[float] = Field(None, gt=0)
    security_deposit: float = Field(2000.0, ge=0)
    pickup_address: Optional[str] = None
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    pickup_city: Optional[str] = None
    description: Optional[str] = None
    features: Optional[str] = None

    @field_validator("registration_number")
    @classmethod
    def upper_reg(cls, v: str) -> str:
        return v.upper().replace(" ", "")


class VehicleUpdate(BaseSchema):
    color: Optional[str] = None
    hourly_rate: Optional[float] = Field(None, gt=0)
    daily_rate: Optional[float] = Field(None, gt=0)
    weekly_rate: Optional[float] = Field(None, gt=0)
    security_deposit: Optional[float] = Field(None, ge=0)
    pickup_address: Optional[str] = None
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    pickup_city: Optional[str] = None
    description: Optional[str] = None
    features: Optional[str] = None
    status: Optional[VehicleStatus] = None


class VehicleOut(BaseSchema):
    id: int
    partner_id: int
    vehicle_type: VehicleType
    brand: str
    model: str
    year: int
    color: Optional[str]
    registration_number: str
    fuel_type: FuelType
    transmission: TransmissionType
    seats: int
    hourly_rate: float
    daily_rate: float
    weekly_rate: Optional[float]
    security_deposit: float
    pickup_address: Optional[str]
    pickup_lat: Optional[float]
    pickup_lng: Optional[float]
    pickup_city: Optional[str]
    images: Optional[str]
    description: Optional[str]
    features: Optional[str]
    status: VehicleStatus
    is_verified: bool
    avg_rating: float
    total_bookings: int
    distance_km: Optional[float] = None  # populated by search endpoint
    created_at: datetime


class VehicleSearch(BaseSchema):
    vehicle_type: Optional[VehicleType] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: float = Field(10.0, gt=0, le=100)
    pickup_at: Optional[datetime] = None
    dropoff_at: Optional[datetime] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    fuel_type: Optional[FuelType] = None
    transmission: Optional[TransmissionType] = None
