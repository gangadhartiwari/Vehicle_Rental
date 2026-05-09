"""Auth: OTP-based login for users & partners, refresh tokens, admin login."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.core.security import (
    create_access_token, create_refresh_token, decode_token, verify_password,
)
from app.models import User, Partner, OTPPurpose, AdminUser
from app.schemas import (
    OTPRequest, OTPVerify, OTPSentResponse, TokenRefreshRequest,
    LoginResponse, TokenPair, AdminLoginRequest, MessageResponse,
)
from app.services.otp_service import OTPService

router = APIRouter(prefix="/auth", tags=["Auth"])


def _build_tokens(subject: int, role: str) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(subject, role),
        refresh_token=create_refresh_token(subject, role),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ------------- USER -------------
@router.post("/user/request-otp", response_model=OTPSentResponse)
def user_request_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    _, code = OTPService.request_otp(db, payload.phone, OTPPurpose.USER_LOGIN)
    return OTPSentResponse(
        message="OTP sent",
        phone=payload.phone,
        expires_in_seconds=settings.OTP_EXPIRE_MINUTES * 60,
        debug_otp=code if not settings.use_twilio else None,
    )


@router.post("/user/verify-otp", response_model=LoginResponse)
def user_verify_otp(payload: OTPVerify, db: Session = Depends(get_db)):
    if not OTPService.verify_otp(db, payload.phone, payload.otp, OTPPurpose.USER_LOGIN):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired OTP")

    user = db.query(User).filter(User.phone == payload.phone).first()
    is_new = False
    if not user:
        user = User(phone=payload.phone, phone_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new = True
    else:
        user.phone_verified = True
        db.commit()

    return LoginResponse(
        tokens=_build_tokens(user.id, "user"),
        user_id=user.id,
        role="user",
        is_new_user=is_new,
    )


# ------------- PARTNER -------------
@router.post("/partner/request-otp", response_model=OTPSentResponse)
def partner_request_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    _, code = OTPService.request_otp(db, payload.phone, OTPPurpose.PARTNER_LOGIN)
    return OTPSentResponse(
        message="OTP sent",
        phone=payload.phone,
        expires_in_seconds=settings.OTP_EXPIRE_MINUTES * 60,
        debug_otp=code if not settings.use_twilio else None,
    )


@router.post("/partner/verify-otp", response_model=LoginResponse)
def partner_verify_otp(payload: OTPVerify, db: Session = Depends(get_db)):
    if not OTPService.verify_otp(db, payload.phone, payload.otp, OTPPurpose.PARTNER_LOGIN):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired OTP")
    p = db.query(Partner).filter(Partner.phone == payload.phone).first()
    is_new = False
    if not p:
        p = Partner(phone=payload.phone, phone_verified=True)
        db.add(p)
        db.commit()
        db.refresh(p)
        is_new = True
    else:
        p.phone_verified = True
        db.commit()
    return LoginResponse(
        tokens=_build_tokens(p.id, "partner"),
        user_id=p.id,
        role="partner",
        is_new_user=is_new,
    )


# ------------- ADMIN -------------
@router.post("/admin/login", response_model=LoginResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    a = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
    if not a or not verify_password(payload.password, a.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not a.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin disabled")
    a.last_login = datetime.utcnow()
    db.commit()
    return LoginResponse(
        tokens=_build_tokens(a.id, "admin"),
        user_id=a.id,
        role="admin",
    )


# ------------- TOKEN REFRESH -------------
@router.post("/refresh", response_model=TokenPair)
def refresh_token(payload: TokenRefreshRequest):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return _build_tokens(int(data["sub"]), data["role"])


@router.post("/logout", response_model=MessageResponse)
def logout():
    # Stateless JWT — clients should drop tokens. For server-side blacklist, plug Redis here.
    return MessageResponse(message="Logged out. Discard tokens client-side.")
