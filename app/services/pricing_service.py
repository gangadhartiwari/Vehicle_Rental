"""Pricing logic for rentals."""
from datetime import datetime
from app.core.config import settings
from app.models.vehicle import Vehicle


class PricingService:
    @staticmethod
    def compute_fare(
        vehicle: Vehicle, pickup_at: datetime, dropoff_at: datetime
    ) -> dict:
        """Compute fare with intelligent slab selection.

        - Up to 23 hours: hourly rate
        - 24h–6 days: daily rate
        - 7+ days: weekly rate (if defined), else daily
        """
        seconds = (dropoff_at - pickup_at).total_seconds()
        hours = round(seconds / 3600, 2)
        days = hours / 24

        basis = "hourly"
        if hours < 24:
            base = vehicle.hourly_rate * hours
            basis = "hourly"
        elif days < 7 or not vehicle.weekly_rate:
            # round up partial day
            billable_days = int(days) + (1 if hours % 24 > 0 else 0)
            base = vehicle.daily_rate * billable_days
            basis = "daily"
        else:
            weeks = days / 7
            billable_weeks = int(weeks) + (1 if days % 7 > 0 else 0)
            base = vehicle.weekly_rate * billable_weeks
            basis = "weekly"

        base = round(base, 2)
        gst = round(base * settings.GST_PERCENT / 100, 2)
        deposit = vehicle.security_deposit or settings.DEFAULT_SECURITY_DEPOSIT
        total = round(base + gst + deposit, 2)

        return {
            "duration_hours": hours,
            "base_amount": base,
            "gst_amount": gst,
            "security_deposit": deposit,
            "total_amount": total,
            "pricing_basis": basis,
        }

    @staticmethod
    def compute_late_fee(vehicle: Vehicle, scheduled_dropoff: datetime, actual_dropoff: datetime) -> float:
        """1.5x hourly rate for any hour past scheduled dropoff."""
        if actual_dropoff <= scheduled_dropoff:
            return 0.0
        late_hours = (actual_dropoff - scheduled_dropoff).total_seconds() / 3600
        billable = int(late_hours) + (1 if late_hours % 1 > 0 else 0)
        return round(vehicle.hourly_rate * 1.5 * billable, 2)
