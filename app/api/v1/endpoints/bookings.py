"""Booking endpoints — user side + partner views + invoice."""
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_partner
from app.db.session import get_db
from app.models import Booking, BookingStatus, User, Partner, Vehicle
from app.schemas import (
    BookingCreate, BookingOut, BookingCancel, BookingPickupVerify,
    BookingDropoffVerify, FareEstimateRequest, FareEstimateOut,
    PaymentInitiate, PaymentConfirm, MessageResponse,
)
from app.services.booking_service import BookingService
from app.utils.helpers import generate_invoice_pdf

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/estimate", response_model=FareEstimateOut)
def estimate(payload: FareEstimateRequest, db: Session = Depends(get_db)):
    fare = BookingService.estimate_fare(db, payload.vehicle_id, payload.pickup_at, payload.dropoff_at)
    return fare


@router.post("", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    b = BookingService.create_booking(
        db, user, payload.vehicle_id, payload.pickup_at, payload.dropoff_at,
        payload.pickup_location, payload.dropoff_location, payload.notes,
    )
    return b


# Mock payment — replace with Razorpay/Stripe webhook in production
@router.post("/{booking_id}/pay", response_model=BookingOut)
def mock_pay(
    booking_id: int,
    payload: PaymentInitiate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    b = db.get(Booking, booking_id)
    if not b or b.user_id != user.id:
        raise HTTPException(404, "Booking not found")
    if payload.booking_id != booking_id:
        raise HTTPException(400, "booking_id mismatch")
    import uuid
    txn = "MOCK_" + uuid.uuid4().hex[:16].upper()
    return BookingService.mock_pay(db, b, txn, payload.method)


@router.get("", response_model=List[BookingOut])
def my_bookings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_: Optional[BookingStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = db.query(Booking).filter(Booking.user_id == user.id)
    if status_:
        q = q.filter(Booking.status == status_)
    return q.order_by(Booking.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    b = db.get(Booking, booking_id)
    if not b or b.user_id != user.id:
        raise HTTPException(404, "Booking not found")
    return b


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: int, payload: BookingCancel, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    b = db.get(Booking, booking_id)
    if not b or b.user_id != user.id:
        raise HTTPException(404, "Booking not found")
    return BookingService.cancel(db, b, payload.reason, "user")


@router.post("/{booking_id}/start", response_model=BookingOut)
def start_trip(
    booking_id: int,
    payload: BookingPickupVerify,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    """Partner verifies pickup OTP shown by user to start the rental."""
    b = db.get(Booking, booking_id)
    if not b or b.partner_id != partner.id:
        raise HTTPException(404, "Booking not found")
    return BookingService.verify_pickup(db, b, payload.otp)


@router.post("/{booking_id}/end", response_model=BookingOut)
def end_trip(
    booking_id: int,
    payload: BookingDropoffVerify,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    """Partner verifies dropoff OTP & records damages to complete rental."""
    b = db.get(Booking, booking_id)
    if not b or b.partner_id != partner.id:
        raise HTTPException(404, "Booking not found")
    return BookingService.verify_dropoff(db, b, payload.otp, payload.damage_charges or 0.0, payload.notes)


@router.get("/{booking_id}/invoice")
def download_invoice(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    b = db.get(Booking, booking_id)
    if not b or b.user_id != user.id:
        raise HTTPException(404, "Booking not found")
    if b.status not in (BookingStatus.COMPLETED, BookingStatus.ONGOING, BookingStatus.CONFIRMED):
        raise HTTPException(400, "Invoice available after confirmation")

    out_path = Path("uploads") / "invoices" / f"{b.booking_code}.pdf"
    vehicle = db.get(Vehicle, b.vehicle_id)
    partner = db.get(Partner, b.partner_id)
    generate_invoice_pdf(b, vehicle, user, partner, out_path)
    return FileResponse(str(out_path), media_type="application/pdf", filename=f"{b.booking_code}.pdf")


# Partner sees their bookings
partner_bookings = APIRouter(prefix="/partners/me/bookings", tags=["Partner Bookings"])


@partner_bookings.get("", response_model=List[BookingOut])
def partner_booking_list(
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
    status_: Optional[BookingStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = db.query(Booking).filter(Booking.partner_id == partner.id)
    if status_:
        q = q.filter(Booking.status == status_)
    return q.order_by(Booking.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


@partner_bookings.get("/{booking_id}", response_model=BookingOut)
def partner_booking_detail(booking_id: int, partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    b = db.get(Booking, booking_id)
    if not b or b.partner_id != partner.id:
        raise HTTPException(404, "Not found")
    # hide pickup/dropoff OTPs from partner — they receive OTP from user verbally
    return b
