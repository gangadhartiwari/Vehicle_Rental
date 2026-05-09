"""Auth dependencies — current user / partner / admin extraction."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models import User, Partner, AdminUser

bearer = HTTPBearer(auto_error=False)


def _decode_or_401(creds: HTTPAuthorizationCredentials | None) -> dict:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    payload = decode_token(creds.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return payload


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    payload = _decode_or_401(creds)
    if payload.get("role") != "user":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User role required")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active or user.is_blocked:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account inactive or blocked")
    return user


def get_current_partner(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Partner:
    payload = _decode_or_401(creds)
    if payload.get("role") != "partner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Partner role required")
    p = db.get(Partner, int(payload["sub"]))
    if not p or not p.is_active or p.is_blocked:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Partner inactive or blocked")
    return p


def get_current_admin(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> AdminUser:
    payload = _decode_or_401(creds)
    if payload.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    a = db.get(AdminUser, int(payload["sub"]))
    if not a or not a.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin inactive")
    return a
