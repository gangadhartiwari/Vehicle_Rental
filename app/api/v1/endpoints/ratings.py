"""Rating endpoints — user submits, public list per vehicle."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Rating, Booking, BookingStatus, Vehicle, Partner, User
from app.schemas import RatingCreate, RatingOut

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("", response_model=RatingOut, status_code=201)
def submit_rating(payload: RatingCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    b = db.get(Booking, payload.booking_id)
    if not b or b.user_id != user.id:
        raise HTTPException(404, "Booking not found")
    if b.status != BookingStatus.COMPLETED:
        raise HTTPException(400, "You can rate only completed bookings")
    if db.query(Rating).filter(Rating.booking_id == b.id).first():
        raise HTTPException(409, "Already rated this booking")

    r = Rating(
        booking_id=b.id,
        user_id=user.id,
        vehicle_id=b.vehicle_id,
        partner_id=b.partner_id,
        stars=payload.stars,
        review=payload.review,
    )
    db.add(r)

    # Recompute aggregates
    vehicle = db.get(Vehicle, b.vehicle_id)
    if vehicle:
        ratings = db.query(Rating).filter(Rating.vehicle_id == vehicle.id).all() + [r]
        vehicle.avg_rating = round(sum(rt.stars for rt in ratings) / len(ratings), 2)

    partner = db.get(Partner, b.partner_id)
    if partner:
        all_p = db.query(Rating).filter(Rating.partner_id == partner.id).all() + [r]
        partner.avg_rating = round(sum(rt.stars for rt in all_p) / len(all_p), 2)

    db.commit()
    db.refresh(r)
    return r


@router.get("/vehicle/{vehicle_id}", response_model=List[RatingOut])
def vehicle_ratings(
    vehicle_id: int, db: Session = Depends(get_db),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    return (
        db.query(Rating).filter(Rating.vehicle_id == vehicle_id)
        .order_by(Rating.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size).all()
    )


@router.get("/partner/{partner_id}", response_model=List[RatingOut])
def partner_ratings(
    partner_id: int, db: Session = Depends(get_db),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    return (
        db.query(Rating).filter(Rating.partner_id == partner_id)
        .order_by(Rating.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size).all()
    )
