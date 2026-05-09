"""Import all models so Base.metadata sees them for create_all."""
from app.models.user import User
from app.models.partner import Partner, PartnerDocument, KYCStatus, DocumentType
from app.models.vehicle import (
    Vehicle, VehicleType, FuelType, TransmissionType, VehicleStatus,
)
from app.models.booking import Booking, Payment, BookingStatus, PaymentStatus
from app.models.misc import OTPRecord, OTPPurpose, Rating, AdminUser, AdminRole

__all__ = [
    "User",
    "Partner", "PartnerDocument", "KYCStatus", "DocumentType",
    "Vehicle", "VehicleType", "FuelType", "TransmissionType", "VehicleStatus",
    "Booking", "Payment", "BookingStatus", "PaymentStatus",
    "OTPRecord", "OTPPurpose", "Rating",
    "AdminUser", "AdminRole",
]
