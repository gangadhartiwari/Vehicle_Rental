"""Vehicle endpoints: partner CRUD + public search with geo + filters."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.api.deps import get_current_partner, get_current_user
from app.db.session import get_db
from app.models import (
    Partner, Vehicle, VehicleType, FuelType, TransmissionType, VehicleStatus,
    KYCStatus, Booking, BookingStatus,
)
from app.schemas import VehicleCreate, VehicleUpdate, VehicleOut, MessageResponse
from app.services.file_service import save_upload
from app.utils.helpers import haversine_km

router = APIRouter(tags=["Vehicles"])


# --------- PARTNER: CRUD ----------
partner_router = APIRouter(prefix="/partners/me/vehicles", tags=["Partner Vehicles"])


@partner_router.post("", response_model=VehicleOut, status_code=201)
def create_vehicle(payload: VehicleCreate, partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    if partner.kyc_status != KYCStatus.APPROVED:
        raise HTTPException(403, "KYC must be APPROVED before adding vehicles")
    if db.query(Vehicle).filter(Vehicle.registration_number == payload.registration_number).first():
        raise HTTPException(409, "A vehicle with this registration number already exists")

    v = Vehicle(partner_id=partner.id, **payload.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@partner_router.get("", response_model=List[VehicleOut])
def list_my_vehicles(partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    return db.query(Vehicle).filter(Vehicle.partner_id == partner.id).order_by(Vehicle.created_at.desc()).all()


@partner_router.get("/{vehicle_id}", response_model=VehicleOut)
def get_my_vehicle(vehicle_id: int, partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.partner_id == partner.id).first()
    if not v:
        raise HTTPException(404, "Not found")
    return v


@partner_router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_my_vehicle(vehicle_id: int, payload: VehicleUpdate, partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.partner_id == partner.id).first()
    if not v:
        raise HTTPException(404, "Not found")
    if v.status == VehicleStatus.BOOKED:
        raise HTTPException(400, "Vehicle is currently booked — cannot edit")
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return v


@partner_router.delete("/{vehicle_id}", response_model=MessageResponse)
def delete_my_vehicle(vehicle_id: int, partner: Partner = Depends(get_current_partner), db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.partner_id == partner.id).first()
    if not v:
        raise HTTPException(404, "Not found")
    # block delete if any active bookings
    active = db.query(Booking).filter(
        Booking.vehicle_id == vehicle_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ONGOING, BookingStatus.PENDING_PAYMENT]),
    ).count()
    if active:
        raise HTTPException(400, "Cannot delete — active bookings exist. Set status to INACTIVE instead.")
    db.delete(v)
    db.commit()
    return MessageResponse(message="Deleted")


@partner_router.post("/{vehicle_id}/images", response_model=VehicleOut)
def upload_vehicle_image(
    vehicle_id: int,
    file: UploadFile = File(...),
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.partner_id == partner.id).first()
    if not v:
        raise HTTPException(404, "Not found")
    rel = save_upload(file, "vehicles")
    existing = (v.images or "").split(",") if v.images else []
    existing = [e for e in existing if e.strip()]
    existing.append(rel)
    v.images = ",".join(existing)
    db.commit()
    db.refresh(v)
    return v


@partner_router.post("/{vehicle_id}/rc", response_model=VehicleOut)
def upload_rc(
    vehicle_id: int,
    file: UploadFile = File(...),
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.partner_id == partner.id).first()
    if not v:
        raise HTTPException(404, "Not found")
    v.rc_image = save_upload(file, "vehicles")
    db.commit()
    db.refresh(v)
    return v


@partner_router.post("/{vehicle_id}/insurance", response_model=VehicleOut)
def upload_insurance(
    vehicle_id: int,
    file: UploadFile = File(...),
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db),
):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.partner_id == partner.id).first()
    if not v:
        raise HTTPException(404, "Not found")
    v.insurance_image = save_upload(file, "vehicles")
    db.commit()
    db.refresh(v)
    return v


# --------- PUBLIC: SEARCH (auth required for booking but search is open to all logged-in users) ----------
public_router = APIRouter(prefix="/vehicles", tags=["Vehicle Search"])


@public_router.get("/search", response_model=List[VehicleOut])
def search_vehicles(
    db: Session = Depends(get_db),
    vehicle_type: Optional[VehicleType] = None,
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = Query(10.0, gt=0, le=100),
    pickup_at: Optional[datetime] = None,
    dropoff_at: Optional[datetime] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    fuel_type: Optional[FuelType] = None,
    transmission: Optional[TransmissionType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = db.query(Vehicle).filter(
        Vehicle.is_verified == True,  # noqa
        Vehicle.status == VehicleStatus.AVAILABLE,
    )
    if vehicle_type:
        q = q.filter(Vehicle.vehicle_type == vehicle_type)
    if city:
        q = q.filter(Vehicle.pickup_city.ilike(f"%{city}%"))
    if min_price is not None:
        q = q.filter(Vehicle.hourly_rate >= min_price)
    if max_price is not None:
        q = q.filter(Vehicle.hourly_rate <= max_price)
    if fuel_type:
        q = q.filter(Vehicle.fuel_type == fuel_type)
    if transmission:
        q = q.filter(Vehicle.transmission == transmission)

    # Exclude vehicles with conflicting bookings if window provided
    if pickup_at and dropoff_at:
        if dropoff_at <= pickup_at:
            raise HTTPException(400, "dropoff_at must be after pickup_at")
        conflict_subq = db.query(Booking.vehicle_id).filter(
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ONGOING, BookingStatus.PENDING_PAYMENT]),
            Booking.pickup_at < dropoff_at,
            Booking.dropoff_at > pickup_at,
        ).subquery()
        q = q.filter(~Vehicle.id.in_(conflict_subq))

    rows = q.all()

    # Geo filter + distance enrichment in Python (sqlite-friendly)
    results = []
    for v in rows:
        out = VehicleOut.model_validate(v).model_dump()
        if lat is not None and lng is not None and v.pickup_lat and v.pickup_lng:
            d = haversine_km(lat, lng, v.pickup_lat, v.pickup_lng)
            if d > radius_km:
                continue
            out["distance_km"] = round(d, 2)
        results.append(out)

    # Sort by distance if geo, else by rating
    if lat is not None and lng is not None:
        results.sort(key=lambda x: (x.get("distance_km") if x.get("distance_km") is not None else 9999))
    else:
        results.sort(key=lambda x: -x["avg_rating"])

    start = (page - 1) * page_size
    return results[start:start + page_size]


@public_router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    v = db.get(Vehicle, vehicle_id)
    if not v or not v.is_verified:
        raise HTTPException(404, "Vehicle not found")
    return v
