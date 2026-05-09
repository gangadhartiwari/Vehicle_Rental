"""OTP generation, delivery, verification."""
import logging
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.misc import OTPRecord, OTPPurpose

logger = logging.getLogger(__name__)


def generate_otp(length: int | None = None) -> str:
    n = length or settings.OTP_LENGTH
    return "".join(random.choices(string.digits, k=n))


def send_sms(phone: str, message: str) -> bool:
    """Send SMS via Twilio if configured, else log to console (dev mode)."""
    if not settings.use_twilio:
        logger.info(f"[DEV-OTP] To {phone}: {message}")
        print(f"\n📱 [DEV-OTP] To {phone}: {message}\n")
        return True
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message, from_=settings.TWILIO_PHONE_NUMBER, to=phone
        )
        return True
    except Exception as e:
        logger.error(f"Twilio SMS failed: {e}")
        return False


class OTPService:
    @staticmethod
    def can_resend(db: Session, phone: str, purpose: OTPPurpose) -> Tuple[bool, int]:
        latest = (
            db.query(OTPRecord)
            .filter(OTPRecord.phone == phone, OTPRecord.purpose == purpose)
            .order_by(desc(OTPRecord.created_at))
            .first()
        )
        if not latest:
            return True, 0
        elapsed = (datetime.utcnow() - latest.created_at).total_seconds()
        cooldown = settings.OTP_RESEND_COOLDOWN_SECONDS
        if elapsed < cooldown:
            return False, int(cooldown - elapsed)
        return True, 0

    @staticmethod
    def request_otp(
        db: Session, phone: str, purpose: OTPPurpose
    ) -> Tuple[OTPRecord, str]:
        ok, wait = OTPService.can_resend(db, phone, purpose)
        if not ok:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait}s before requesting another OTP",
            )

        # Invalidate any older un-used OTPs for this phone+purpose
        db.query(OTPRecord).filter(
            OTPRecord.phone == phone,
            OTPRecord.purpose == purpose,
            OTPRecord.is_used == False,  # noqa
        ).update({"is_used": True})

        code = generate_otp()
        record = OTPRecord(
            phone=phone,
            code_hash=hash_password(code),
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        message = (
            f"Your {settings.APP_NAME} OTP is {code}. "
            f"Valid for {settings.OTP_EXPIRE_MINUTES} minutes. Do not share."
        )
        send_sms(phone, message)
        return record, code

    @staticmethod
    def verify_otp(
        db: Session, phone: str, code: str, purpose: OTPPurpose
    ) -> bool:
        record = (
            db.query(OTPRecord)
            .filter(
                OTPRecord.phone == phone,
                OTPRecord.purpose == purpose,
                OTPRecord.is_used == False,  # noqa
            )
            .order_by(desc(OTPRecord.created_at))
            .first()
        )
        if not record:
            return False

        if datetime.utcnow() > record.expires_at:
            record.is_used = True
            db.commit()
            return False

        if record.attempts >= settings.OTP_MAX_ATTEMPTS:
            record.is_used = True
            db.commit()
            return False

        record.attempts += 1

        if not verify_password(code, record.code_hash):
            db.commit()
            return False

        record.is_used = True
        db.commit()
        return True
