"""Rating schemas."""
from datetime import datetime
from typing import Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class RatingCreate(BaseSchema):
    booking_id: int
    stars: int = Field(..., ge=1, le=5)
    review: Optional[str] = Field(None, max_length=2000)


class RatingOut(BaseSchema):
    id: int
    booking_id: int
    user_id: int
    vehicle_id: int
    partner_id: int
    stars: int
    review: Optional[str]
    created_at: datetime
