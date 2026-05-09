"""Admin endpoints for the dashboard."""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import (
    User, Partner, PartnerDocument, Vehicle, Booking, BookingStatus,
    Rating, AdminUser, KYCStatus, VehicleStatus, PaymentStatus,
)
from app.schemas import (
    UserAdminOut, PartnerDetailOut, VehicleOut, BookingOut, RatingOut,
    KYCReviewRequest, MessageResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# ---- Stats ----
@router.get("/stats")
def get_stats(_: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    last_30 = datetime.utcnow() - timedelta(days=30)

    total_bookings_30d = db.query(func.count(Booking.id)).filter(Booking.created_at >= last_30).scalar() or 0
    revenue_30d = db.query(func.coalesce(func.sum(Booking.base_amount), 0)).filter(
        Booking.created_at >= last_30,
        Booking.payment_status == PaymentStatus.PAID,
    ).scalar() or 0

    return {
        "users": {
            "total": db.query(func.count(User.id)).scalar() or 0,
            "active": db.query(func.count(User.id)).filter(User.is_active == True, User.is_blocked == False).scalar() or 0,
            "blocked": db.query(func.count(User.id)).filter(User.is_blocked == True).scalar() or 0,
        },
        "partners": {
            "total": db.query(func.count(Partner.id)).scalar() or 0,
            "kyc_pending": db.query(func.count(Partner.id)).filter(Partner.kyc_status == KYCStatus.SUBMITTED).scalar() or 0,
            "kyc_approved": db.query(func.count(Partner.id)).filter(Partner.kyc_status == KYCStatus.APPROVED).scalar() or 0,
        },
        "vehicles": {
            "total": db.query(func.count(Vehicle.id)).scalar() or 0,
            "verified": db.query(func.count(Vehicle.id)).filter(Vehicle.is_verified == True).scalar() or 0,
            "available": db.query(func.count(Vehicle.id)).filter(Vehicle.status == VehicleStatus.AVAILABLE).scalar() or 0,
            "booked": db.query(func.count(Vehicle.id)).filter(Vehicle.status == VehicleStatus.BOOKED).scalar() or 0,
        },
        "bookings": {
            "total": db.query(func.count(Booking.id)).scalar() or 0,
            "ongoing": db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.ONGOING).scalar() or 0,
            "completed": db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.COMPLETED).scalar() or 0,
            "cancelled": db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.CANCELLED).scalar() or 0,
            "last_30d": total_bookings_30d,
        },
        "revenue": {
            "last_30d_gross": float(revenue_30d),
            "currency": "INR",
        },
        "as_of": datetime.utcnow().isoformat(),
    }


# ---- Users ----
@router.get("/users", response_model=List[UserAdminOut])
def list_users(
    _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db),
    q: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(User)
    if q:
        like = f"%{q}%"
        query = query.filter((User.phone.ilike(like)) | (User.full_name.ilike(like)) | (User.email.ilike(like)))
    return query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.post("/users/{user_id}/block", response_model=MessageResponse)
def block_user(user_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    u.is_blocked = True
    db.commit()
    return MessageResponse(message=f"User {u.phone} blocked")


@router.post("/users/{user_id}/unblock", response_model=MessageResponse)
def unblock_user(user_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    u.is_blocked = False
    db.commit()
    return MessageResponse(message=f"User {u.phone} unblocked")


@router.post("/users/{user_id}/verify-dl", response_model=MessageResponse)
def verify_dl(user_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    u.dl_verified = True
    db.commit()
    return MessageResponse(message="DL verified")


# ---- Partners / KYC ----
@router.get("/partners", response_model=List[PartnerDetailOut])
def list_partners(
    _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db),
    kyc_status: Optional[KYCStatus] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Partner)
    if kyc_status:
        query = query.filter(Partner.kyc_status == kyc_status)
    if q:
        like = f"%{q}%"
        query = query.filter((Partner.phone.ilike(like)) | (Partner.business_name.ilike(like)) | (Partner.email.ilike(like)))
    return query.order_by(Partner.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.get("/partners/{partner_id}", response_model=PartnerDetailOut)
def get_partner(partner_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    p = db.get(Partner, partner_id)
    if not p:
        raise HTTPException(404, "Partner not found")
    return p


@router.post("/partners/{partner_id}/kyc/review", response_model=PartnerDetailOut)
def review_kyc(
    partner_id: int, payload: KYCReviewRequest,
    _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db),
):
    if payload.status not in (KYCStatus.APPROVED, KYCStatus.REJECTED):
        raise HTTPException(400, "Status must be APPROVED or REJECTED")
    p = db.get(Partner, partner_id)
    if not p:
        raise HTTPException(404, "Partner not found")
    p.kyc_status = payload.status
    p.kyc_remarks = payload.remarks
    if payload.status == KYCStatus.APPROVED:
        for d in p.documents:
            d.is_verified = True
    db.commit()
    db.refresh(p)
    return p


@router.post("/partners/{partner_id}/block", response_model=MessageResponse)
def block_partner(partner_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    p = db.get(Partner, partner_id)
    if not p:
        raise HTTPException(404, "Not found")
    p.is_blocked = True
    db.commit()
    return MessageResponse(message="Partner blocked")


@router.post("/partners/{partner_id}/unblock", response_model=MessageResponse)
def unblock_partner(partner_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    p = db.get(Partner, partner_id)
    if not p:
        raise HTTPException(404, "Not found")
    p.is_blocked = False
    db.commit()
    return MessageResponse(message="Partner unblocked")


# ---- Vehicles ----
@router.get("/vehicles", response_model=List[VehicleOut])
def list_vehicles(
    _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db),
    is_verified: Optional[bool] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Vehicle)
    if is_verified is not None:
        query = query.filter(Vehicle.is_verified == is_verified)
    return query.order_by(Vehicle.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.post("/vehicles/{vehicle_id}/verify", response_model=VehicleOut)
def verify_vehicle(vehicle_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    v = db.get(Vehicle, vehicle_id)
    if not v:
        raise HTTPException(404, "Not found")
    v.is_verified = True
    if v.status == VehicleStatus.INACTIVE:
        v.status = VehicleStatus.AVAILABLE
    db.commit()
    db.refresh(v)
    return v


@router.post("/vehicles/{vehicle_id}/unverify", response_model=VehicleOut)
def unverify_vehicle(vehicle_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    v = db.get(Vehicle, vehicle_id)
    if not v:
        raise HTTPException(404, "Not found")
    v.is_verified = False
    db.commit()
    db.refresh(v)
    return v


# ---- Bookings ----
@router.get("/bookings", response_model=List[BookingOut])
def list_all_bookings(
    _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db),
    status_: Optional[BookingStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    q = db.query(Booking)
    if status_:
        q = q.filter(Booking.status == status_)
    return q.order_by(Booking.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.post("/bookings/{booking_id}/force-cancel", response_model=BookingOut)
def admin_cancel(booking_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db), reason: str = "Cancelled by admin"):
    from app.services.booking_service import BookingService
    b = db.get(Booking, booking_id)
    if not b:
        raise HTTPException(404, "Not found")
    return BookingService.cancel(db, b, reason, "admin")


# ---- Ratings (moderation) ----
@router.get("/ratings", response_model=List[RatingOut])
def list_ratings(
    _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    return db.query(Rating).order_by(Rating.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.delete("/ratings/{rating_id}", response_model=MessageResponse)
def delete_rating(rating_id: int, _: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    r = db.get(Rating, rating_id)
    if not r:
        raise HTTPException(404, "Not found")
    db.delete(r)
    db.commit()
    return MessageResponse(message="Rating deleted")
