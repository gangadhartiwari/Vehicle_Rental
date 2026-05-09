"""Auth schemas."""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from app.schemas.common import BaseSchema, TokenPair


PHONE_REGEX = r"^\+?[1-9]\d{7,14}$"


class OTPRequest(BaseModel):
    phone: str = Field(..., description="E.164 format e.g. +919876543210")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not v.startswith("+"):
            # auto-prepend India code if 10 digits
            if v.isdigit() and len(v) == 10:
                v = "+91" + v
        if len(v) < 9 or len(v) > 16:
            raise ValueError("Invalid phone number")
        return v


class OTPVerify(BaseModel):
    phone: str
    otp: str = Field(..., min_length=4, max_length=8)

    @field_validator("phone")
    @classmethod
    def normalize(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not v.startswith("+") and v.isdigit() and len(v) == 10:
            v = "+91" + v
        return v


class OTPSentResponse(BaseSchema):
    message: str
    phone: str
    expires_in_seconds: int
    # In dev mode (no Twilio), we return the OTP for easy testing.
    debug_otp: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseSchema):
    tokens: TokenPair
    user_id: int
    role: str
    is_new_user: bool = False
