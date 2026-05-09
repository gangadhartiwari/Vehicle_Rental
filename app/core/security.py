"""Security primitives: password hashing, JWT encode/decode."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import bcrypt
from jose import jwt, JWTError

from app.core.config import settings


def _truncate(secret: str) -> bytes:
    """bcrypt has a 72-byte limit. Truncate safely (covers OTP hashing too)."""
    b = secret.encode("utf-8")
    return b[:72]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_truncate(plain), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate(plain), hashed.encode("utf-8"))
    except Exception:
        return False


def _create_token(subject: str | int, expires_delta: timedelta, token_type: str, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str | int, role: str, extra: dict | None = None) -> str:
    data = {"role": role}
    if extra:
        data.update(extra)
    return _create_token(
        subject,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
        data,
    )


def create_refresh_token(subject: str | int, role: str) -> str:
    return _create_token(
        subject,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
        {"role": role},
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
