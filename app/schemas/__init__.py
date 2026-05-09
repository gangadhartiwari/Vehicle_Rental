from app.schemas.common import (
    BaseSchema, MessageResponse, TokenPair, PaginatedResponse, PageParams,
)
from app.schemas.auth import (
    OTPRequest, OTPVerify, OTPSentResponse, TokenRefreshRequest,
    AdminLoginRequest, LoginResponse,
)
from app.schemas.user import UserUpdate, UserDLUpdate, UserOut, UserAdminOut
from app.schemas.partner import (
    PartnerProfileUpdate, PartnerBankUpdate, DocumentOut, PartnerOut,
    PartnerDetailOut, KYCReviewRequest,
)
from app.schemas.vehicle import (
    VehicleCreate, VehicleUpdate, VehicleOut, VehicleSearch,
)
from app.schemas.booking import (
    BookingCreate, FareEstimateRequest, FareEstimateOut, BookingOut,
    BookingCancel, BookingPickupVerify, BookingDropoffVerify,
    PaymentInitiate, PaymentConfirm,
)
from app.schemas.rating import RatingCreate, RatingOut
