"""Booking lifecycle: create, confirm, pickup, dropoff, cancel."""
import random
import string
from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus, Payment, PaymentStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.user import User
from app.models.partner import Partner
from app.services.pricing_service import PricingService


def generate_booking_code() -> str:
    return "VR" + "".join(random.choices(string.digits, k=8))


def generate_otp_code(length: int = 4) -> str:
    return "".join(random.choices(string.digits, k=length))


class BookingService:
    @staticmethod
    def _has_conflict(db: Session, vehicle_id: int, pickup_at: datetime, dropoff_at: datetime, exclude_id: int | None = None) -> bool:
        # Two intervals overlap iff start_a < end_b AND start_b < end_a
        active = [BookingStatus.CONFIRMED, BookingStatus.ONGOING, BookingStatus.PENDING_PAYMENT]
        q = db.query(Booking).filter(
            Booking.vehicle_id == vehicle_id,
            Booking.status.in_(active),
            Booking.pickup_at < dropoff_at,
            Booking.dropoff_at > pickup_at,
        )
        if exclude_id:
            q = q.filter(Booking.id != exclude_id)
        return db.query(q.exists()).scalar()

    @staticmethod
    def estimate_fare(db: Session, vehicle_id: int, pickup_at: datetime, dropoff_at: datetime) -> dict:
        if dropoff_at <= pickup_at:
            raise HTTPException(400, "dropoff_at must be after pickup_at")
        v = db.get(Vehicle, vehicle_id)
        if not v:
            raise HTTPException(404, "Vehicle not found")
        return PricingService.compute_fare(v, pickup_at, dropoff_at)

    @staticmethod
    def create_booking(db: Session, user: User, vehicle_id: int, pickup_at: datetime, dropoff_at: datetime,
                       pickup_location: str | None, dropoff_location: str | None, notes: str | None) -> Booking:
        if pickup_at < datetime.utcnow():
            raise HTTPException(400, "Pickup time must be in the future")

        vehicle = db.get(Vehicle, vehicle_id)
        if not vehicle:
            raise HTTPException(404, "Vehicle not found")
        if vehicle.status not in (VehicleStatus.AVAILABLE,):
            raise HTTPException(400, f"Vehicle is currently {vehicle.status.value}")
        if not vehicle.is_verified:
            raise HTTPException(400, "Vehicle is not verified yet")

        if not user.dl_number:
            raise HTTPException(400, "Driver's licence required to book. Please update your profile.")

        if BookingService._has_conflict(db, vehicle_id, pickup_at, dropoff_at):
            raise HTTPException(409, "Vehicle is already booked for the selected time window")

        fare = PricingService.compute_fare(vehicle, pickup_at, dropoff_at)

        b = Booking(
            booking_code=generate_booking_code(),
            user_id=user.id,
            vehicle_id=vehicle_id,
            partner_id=vehicle.partner_id,
            pickup_at=pickup_at,
            dropoff_at=dropoff_at,
            pickup_location=pickup_location or vehicle.pickup_address,
            dropoff_location=dropoff_location or vehicle.pickup_address,
            duration_hours=fare["duration_hours"],
            base_amount=fare["base_amount"],
            gst_amount=fare["gst_amount"],
            security_deposit=fare["security_deposit"],
            total_amount=fare["total_amount"],
            status=BookingStatus.PENDING_PAYMENT,
            payment_status=PaymentStatus.PENDING,
            notes=notes,
        )
        db.add(b)
        db.commit()
        db.refresh(b)
        return b

    @staticmethod
    def mock_pay(db: Session, booking: Booking, transaction_id: str, method: str) -> Booking:
        if booking.status != BookingStatus.PENDING_PAYMENT:
            raise HTTPException(400, f"Cannot pay for booking in status {booking.status.value}")

        pay = Payment(
            booking_id=booking.id,
            amount=booking.total_amount,
            method=method,
            transaction_id=transaction_id,
            gateway="mock",
            status=PaymentStatus.PAID,
            paid_at=datetime.utcnow(),
        )
        db.add(pay)
        booking.payment_status = PaymentStatus.PAID
        booking.status = BookingStatus.CONFIRMED
        booking.pickup_otp = generate_otp_code(4)
        booking.dropoff_otp = generate_otp_code(4)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def cancel(db: Session, booking: Booking, reason: str, by: str) -> Booking:
        if booking.status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
            raise HTTPException(400, f"Cannot cancel a {booking.status.value} booking")
        if booking.status == BookingStatus.ONGOING:
            raise HTTPException(400, "Cannot cancel an ongoing rental — please return the vehicle")

        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = reason
        booking.cancelled_by = by

        if booking.payment_status == PaymentStatus.PAID:
            # Refund-window policy: full refund > 24h, 50% within 24h, 0% within 2h
            now = datetime.utcnow()
            hours_to_pickup = (booking.pickup_at - now).total_seconds() / 3600
            if hours_to_pickup > 24:
                refund_pct = 1.0
            elif hours_to_pickup > 2:
                refund_pct = 0.5
            else:
                refund_pct = 0.0
            if refund_pct > 0 and booking.payment:
                # Refund includes deposit always
                refundable = booking.base_amount * refund_pct + booking.gst_amount * refund_pct + booking.security_deposit
                booking.payment.status = PaymentStatus.REFUNDED
                booking.payment_status = PaymentStatus.REFUNDED
                booking.notes = (booking.notes or "") + f"\nRefund issued: ₹{refundable:.2f} ({int(refund_pct*100)}%)"
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def verify_pickup(db: Session, booking: Booking, otp: str) -> Booking:
        if booking.status != BookingStatus.CONFIRMED:
            raise HTTPException(400, f"Cannot start trip in status {booking.status.value}")
        if booking.pickup_otp != otp:
            raise HTTPException(400, "Invalid pickup OTP")
        booking.status = BookingStatus.ONGOING
        booking.actual_pickup_at = datetime.utcnow()
        booking.vehicle.status = VehicleStatus.BOOKED
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def verify_dropoff(db: Session, booking: Booking, otp: str, damage_charges: float = 0.0, notes: str | None = None) -> Booking:
        if booking.status != BookingStatus.ONGOING:
            raise HTTPException(400, f"Cannot end trip in status {booking.status.value}")
        if booking.dropoff_otp != otp:
            raise HTTPException(400, "Invalid dropoff OTP")

        now = datetime.utcnow()
        booking.actual_dropoff_at = now
        late_fee = PricingService.compute_late_fee(booking.vehicle, booking.dropoff_at, now)
        booking.late_fee = late_fee
        booking.damage_charges = damage_charges or 0.0
        booking.final_amount = round(booking.total_amount + late_fee + (damage_charges or 0.0), 2)
        booking.status = BookingStatus.COMPLETED
        if notes:
            booking.notes = (booking.notes or "") + f"\n[Return notes] {notes}"
        booking.vehicle.status = VehicleStatus.AVAILABLE
        booking.vehicle.total_bookings += 1

        # Update partner aggregates
        partner = db.get(Partner, booking.partner_id)
        if partner:
            partner.total_bookings += 1
            partner.total_earnings += booking.base_amount  # exclude GST/deposit/late
        db.commit()
        db.refresh(booking)
        return booking
