"""User schemas."""
from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema


class UserUpdate(BaseSchema):
    full_name: Optional[str] = Field(None, max_length=120)
    email: Optional[EmailStr] = None
    last_lat: Optional[float] = None
    last_lng: Optional[float] = None


class UserDLUpdate(BaseSchema):
    dl_number: str = Field(..., min_length=4, max_length=40)


class UserOut(BaseSchema):
    id: int
    phone: str
    email: Optional[str]
    full_name: Optional[str]
    profile_image: Optional[str]
    dl_number: Optional[str]
    dl_verified: bool
    phone_verified: bool
    is_active: bool
    created_at: datetime


class UserAdminOut(UserOut):
    is_blocked: bool
    last_lat: Optional[float]
    last_lng: Optional[float]
