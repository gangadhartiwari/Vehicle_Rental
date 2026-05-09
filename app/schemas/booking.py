"""Booking schemas."""
from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator, model_validator
from app.schemas.common import BaseSchema
from app.models.booking import BookingStatus, PaymentStatus


class BookingCreate(BaseSchema):
    vehicle_id: int
    pickup_at: datetime
    dropoff_at: datetime
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_window(self):
        if self.dropoff_at <= self.pickup_at:
            raise ValueError("dropoff_at must be after pickup_at")
        delta = (self.dropoff_at - self.pickup_at).total_seconds() / 3600
        if delta < 1:
            raise ValueError("Minimum rental duration is 1 hour")
        if delta > 24 * 30:
            raise ValueError("Maximum rental duration is 30 days")
        return self


class FareEstimateRequest(BaseSchema):
    vehicle_id: int
    pickup_at: datetime
    dropoff_at: datetime


class FareEstimateOut(BaseSchema):
    duration_hours: float
    base_amount: float
    gst_amount: float
    security_deposit: float
    total_amount: float
    pricing_basis: str  # 'hourly' or 'daily' or 'weekly'


class BookingOut(BaseSchema):
    id: int
    booking_code: str
    user_id: int
    vehicle_id: int
    partner_id: int
    pickup_at: datetime
    dropoff_at: datetime
    actual_pickup_at: Optional[datetime]
    actual_dropoff_at: Optional[datetime]
    pickup_location: Optional[str]
    dropoff_location: Optional[str]
    duration_hours: float
    base_amount: float
    gst_amount: float
    security_deposit: float
    discount_amount: float
    total_amount: float
    late_fee: float
    damage_charges: float
    final_amount: Optional[float]
    status: BookingStatus
    payment_status: PaymentStatus
    cancellation_reason: Optional[str]
    pickup_otp: Optional[str] = None  # only shown to user before pickup
    dropoff_otp: Optional[str] = None
    notes: Optional[str]
    created_at: datetime


class BookingCancel(BaseSchema):
    reason: str = Field(..., min_length=3, max_length=500)


class BookingPickupVerify(BaseSchema):
    otp: str = Field(..., min_length=4, max_length=8)


class BookingDropoffVerify(BaseSchema):
    otp: str = Field(..., min_length=4, max_length=8)
    damage_charges: Optional[float] = Field(0.0, ge=0)
    notes: Optional[str] = None


class PaymentInitiate(BaseSchema):
    booking_id: int
    method: str = Field("upi", max_length=40)


class PaymentConfirm(BaseSchema):
    booking_id: int
    transaction_id: str
    method: str
    success: bool = True
