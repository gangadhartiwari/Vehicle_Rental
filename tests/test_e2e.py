"""End-to-end smoke test of the rental backend.

Uses FastAPI TestClient — no separate server process needed. Validates:
- OTP login flow (user + partner + admin)
- Partner KYC + bank + vehicle creation
- Admin KYC approval + vehicle verification
- Vehicle search
- Booking → pay → start (OTP) → end (OTP) → rating
- Invoice download
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import io

# Use a separate test DB
os.environ["DATABASE_URL"] = "sqlite:///./test_e2e.db"

# Clean DB
Path("test_e2e.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient
from app.main import app

# Use TestClient as context manager so lifespan (table creation + admin bootstrap) fires
client = TestClient(app)
client.__enter__()

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check(label: str, condition: bool, detail: str = ""):
    status = f"{GREEN}✓{RESET}" if condition else f"{RED}✗{RESET}"
    print(f"  {status} {label}{(' — ' + detail) if detail else ''}")
    if not condition:
        print(f"    {RED}DETAIL:{RESET} {detail}")
        sys.exit(1)


def section(title: str):
    print(f"\n{BOLD}{title}{RESET}")


# ============= 1. HEALTH =============
section("1. Health")
r = client.get("/api/v1/health")
check("GET /health → 200", r.status_code == 200, str(r.json()))


# ============= 2. USER OTP LOGIN =============
section("2. User OTP login flow")
USER_PHONE = "+919876543210"

r = client.post("/api/v1/auth/user/request-otp", json={"phone": USER_PHONE})
check("Request OTP", r.status_code == 200, r.text)
otp = r.json().get("debug_otp")
check("debug_otp present in dev mode", bool(otp), "missing debug_otp")

r = client.post("/api/v1/auth/user/verify-otp", json={"phone": USER_PHONE, "otp": otp})
check("Verify OTP", r.status_code == 200, r.text)
USER_TOKEN = r.json()["tokens"]["access_token"]
USER_ID = r.json()["user_id"]
check("Token + user_id received", bool(USER_TOKEN and USER_ID), str(r.json()))
check("Marked as new user", r.json()["is_new_user"] is True)

# Update profile + DL
r = client.patch(
    "/api/v1/users/me",
    json={"full_name": "Aarav Sharma", "email": "aarav@example.com"},
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Update profile", r.status_code == 200, r.text)

r = client.post(
    "/api/v1/users/me/dl",
    json={"dl_number": "MH0120220001234"},
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Save DL number", r.status_code == 200, r.text)


# ============= 3. PARTNER OTP LOGIN =============
section("3. Partner OTP login + onboarding")
PARTNER_PHONE = "+919812345678"

r = client.post("/api/v1/auth/partner/request-otp", json={"phone": PARTNER_PHONE})
check("Partner OTP request", r.status_code == 200, r.text)
p_otp = r.json()["debug_otp"]

r = client.post("/api/v1/auth/partner/verify-otp", json={"phone": PARTNER_PHONE, "otp": p_otp})
check("Partner OTP verify", r.status_code == 200, r.text)
PARTNER_TOKEN = r.json()["tokens"]["access_token"]
PARTNER_ID = r.json()["user_id"]

# Profile update
r = client.patch(
    "/api/v1/partners/me",
    json={
        "business_name": "City Rentals Pvt Ltd",
        "contact_person": "Rohan Patel",
        "email": "ops@cityrentals.in",
        "city": "Mumbai", "state": "Maharashtra", "pincode": "400001",
        "address_line": "123 Marine Drive",
        "hub_lat": 18.9388, "hub_lng": 72.8354,
    },
    headers={"Authorization": f"Bearer {PARTNER_TOKEN}"},
)
check("Partner profile update", r.status_code == 200, r.text)

# Bank
r = client.post(
    "/api/v1/partners/me/bank",
    json={"bank_account_number": "1234567890123", "bank_ifsc": "hdfc0001234", "bank_holder_name": "City Rentals Pvt Ltd"},
    headers={"Authorization": f"Bearer {PARTNER_TOKEN}"},
)
check("Bank details saved", r.status_code == 200, r.text)
check("IFSC uppercased", r.json()["bank_ifsc"] == "HDFC0001234")

# Upload AADHAAR doc
fake_pdf = io.BytesIO(b"%PDF-1.4 fake aadhaar content for test")
r = client.post(
    "/api/v1/partners/me/documents",
    data={"doc_type": "AADHAAR", "doc_number": "1234-5678-9012"},
    files={"file": ("aadhaar.pdf", fake_pdf, "application/pdf")},
    headers={"Authorization": f"Bearer {PARTNER_TOKEN}"},
)
check("Upload AADHAAR", r.status_code == 200, r.text)

# Upload PAN doc
fake_pdf2 = io.BytesIO(b"%PDF-1.4 fake pan")
r = client.post(
    "/api/v1/partners/me/documents",
    data={"doc_type": "PAN", "doc_number": "ABCDE1234F"},
    files={"file": ("pan.pdf", fake_pdf2, "application/pdf")},
    headers={"Authorization": f"Bearer {PARTNER_TOKEN}"},
)
check("Upload PAN", r.status_code == 200, r.text)

# Submit KYC
r = client.post("/api/v1/partners/me/submit-kyc", headers={"Authorization": f"Bearer {PARTNER_TOKEN}"})
check("Submit KYC", r.status_code == 200, r.text)
check("KYC status SUBMITTED", r.json()["kyc_status"] == "SUBMITTED")


# ============= 4. ADMIN APPROVES KYC =============
section("4. Admin login + KYC approval + vehicle verification")
r = client.post(
    "/api/v1/auth/admin/login",
    json={"email": "admin@vehiclerental.com", "password": "Admin@12345"},
)
check("Admin login", r.status_code == 200, r.text)
ADMIN_TOKEN = r.json()["tokens"]["access_token"]

# Approve KYC
r = client.post(
    f"/api/v1/admin/partners/{PARTNER_ID}/kyc/review",
    json={"status": "APPROVED", "remarks": "All documents look good"},
    headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
)
check("Admin approves KYC", r.status_code == 200, r.text)
check("KYC now APPROVED", r.json()["kyc_status"] == "APPROVED")


# ============= 5. PARTNER ADDS VEHICLE =============
section("5. Partner adds vehicle (post-KYC)")
r = client.post(
    "/api/v1/partners/me/vehicles",
    json={
        "vehicle_type": "BIKE",
        "brand": "Royal Enfield",
        "model": "Classic 350",
        "year": 2023,
        "color": "Black",
        "registration_number": "MH01AB1234",
        "fuel_type": "PETROL",
        "transmission": "MANUAL",
        "seats": 2,
        "hourly_rate": 120,
        "daily_rate": 1500,
        "weekly_rate": 8500,
        "security_deposit": 3000,
        "pickup_address": "Marine Drive, Mumbai",
        "pickup_lat": 18.9388, "pickup_lng": 72.8354,
        "pickup_city": "Mumbai",
        "description": "Well-maintained classic bike",
        "features": "ABS,Disc Brakes,LED Headlamp",
    },
    headers={"Authorization": f"Bearer {PARTNER_TOKEN}"},
)
check("Add vehicle", r.status_code == 201, r.text)
VEHICLE_ID = r.json()["id"]
check("Vehicle initially unverified", r.json()["is_verified"] is False)

# Admin verifies
r = client.post(
    f"/api/v1/admin/vehicles/{VEHICLE_ID}/verify",
    headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
)
check("Admin verifies vehicle", r.status_code == 200, r.text)
check("Vehicle is_verified=True", r.json()["is_verified"] is True)


# ============= 6. SEARCH =============
section("6. Vehicle search")
r = client.get(
    "/api/v1/vehicles/search",
    params={"vehicle_type": "BIKE", "city": "Mumbai", "lat": 18.94, "lng": 72.83, "radius_km": 5},
)
check("Search returns results", r.status_code == 200, r.text)
results = r.json()
check("At least 1 vehicle found", len(results) >= 1, f"got {len(results)}")
check("Distance computed", results[0].get("distance_km") is not None, f"distance={results[0].get('distance_km')}")


# ============= 7. BOOKING FLOW =============
section("7. Booking flow")
pickup = (datetime.utcnow() + timedelta(hours=2)).isoformat()
dropoff = (datetime.utcnow() + timedelta(hours=8)).isoformat()

# Estimate
r = client.post(
    "/api/v1/bookings/estimate",
    json={"vehicle_id": VEHICLE_ID, "pickup_at": pickup, "dropoff_at": dropoff},
)
check("Fare estimate", r.status_code == 200, r.text)
fare = r.json()
check("Hourly basis (6h)", fare["pricing_basis"] == "hourly", f"got {fare['pricing_basis']}")
expected_base = 120 * 6
check(f"Base = ₹{expected_base}", abs(fare["base_amount"] - expected_base) < 0.01, f"got {fare['base_amount']}")

# Create booking
r = client.post(
    "/api/v1/bookings",
    json={
        "vehicle_id": VEHICLE_ID,
        "pickup_at": pickup,
        "dropoff_at": dropoff,
        "pickup_location": "Marine Drive Hub",
        "dropoff_location": "Marine Drive Hub",
        "notes": "Will pick up at 3 PM",
    },
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Create booking", r.status_code == 201, r.text)
booking = r.json()
BOOKING_ID = booking["id"]
check("Booking PENDING_PAYMENT", booking["status"] == "PENDING_PAYMENT")
check("No OTPs yet (pre-payment)", booking["pickup_otp"] is None and booking["dropoff_otp"] is None)

# Conflict detection
r = client.post(
    "/api/v1/bookings",
    json={"vehicle_id": VEHICLE_ID, "pickup_at": pickup, "dropoff_at": dropoff},
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Conflicting booking rejected (409)", r.status_code == 409, r.text)

# Pay
r = client.post(
    f"/api/v1/bookings/{BOOKING_ID}/pay",
    json={"booking_id": BOOKING_ID, "method": "upi"},
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Payment successful", r.status_code == 200, r.text)
paid = r.json()
check("Status CONFIRMED after pay", paid["status"] == "CONFIRMED")
check("Pickup OTP issued", bool(paid["pickup_otp"]) and len(paid["pickup_otp"]) == 4)
check("Dropoff OTP issued", bool(paid["dropoff_otp"]) and len(paid["dropoff_otp"]) == 4)
PICKUP_OTP = paid["pickup_otp"]
DROPOFF_OTP = paid["dropoff_otp"]

# Wrong OTP rejected
r = client.post(
    f"/api/v1/bookings/{BOOKING_ID}/start",
    json={"otp": "0000"},
    headers={"Authorization": f"Bearer {PARTNER_TOKEN}"},
)
check("Wrong pickup OTP rejected", r.status_code == 400, r.text)

# Correct pickup OTP
r = client.post(
    f"/api/v1/bookings/{BOOKING_ID}/start",
    json={"otp": PICKUP_OTP},
    headers={"Authorization": f"Bearer {PARTNER_TOKEN}"},
)
check("Pickup OTP verified — trip started", r.status_code == 200, r.text)
check("Status = ONGOING", r.json()["status"] == "ONGOING")

# Dropoff with damage charges
r = client.post(
    f"/api/v1/bookings/{BOOKING_ID}/end",
    json={"otp": DROPOFF_OTP, "damage_charges": 200, "notes": "Minor scratch on tank"},
    headers={"Authorization": f"Bearer {PARTNER_TOKEN}"},
)
check("Dropoff OTP verified — trip ended", r.status_code == 200, r.text)
ended = r.json()
check("Status = COMPLETED", ended["status"] == "COMPLETED")
check("Damage charges applied", ended["damage_charges"] == 200)


# ============= 8. RATING =============
section("8. Rating")
r = client.post(
    "/api/v1/ratings",
    json={"booking_id": BOOKING_ID, "stars": 5, "review": "Smooth experience, bike was clean"},
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Submit rating", r.status_code == 201, r.text)

# Duplicate rating rejected
r = client.post(
    "/api/v1/ratings",
    json={"booking_id": BOOKING_ID, "stars": 4},
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Duplicate rating rejected (409)", r.status_code == 409)

# Vehicle avg rating updated
r = client.get(f"/api/v1/vehicles/{VEHICLE_ID}")
check("Vehicle avg_rating = 5.0", r.json()["avg_rating"] == 5.0)


# ============= 9. INVOICE =============
section("9. Invoice download")
r = client.get(
    f"/api/v1/bookings/{BOOKING_ID}/invoice",
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Invoice PDF downloads", r.status_code == 200, r.text[:200])
check("Content-type is PDF", "pdf" in r.headers.get("content-type", "").lower())
check("PDF is non-empty", len(r.content) > 1000, f"size={len(r.content)}")


# ============= 10. ADMIN STATS =============
section("10. Admin stats dashboard")
r = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
check("Stats endpoint", r.status_code == 200, r.text)
s = r.json()
check("1 user", s["users"]["total"] == 1)
check("1 partner KYC approved", s["partners"]["kyc_approved"] == 1)
check("1 vehicle verified", s["vehicles"]["verified"] == 1)
check("1 booking completed", s["bookings"]["completed"] == 1)


# ============= 11. AUTH ENFORCEMENT =============
section("11. Auth enforcement")
r = client.get("/api/v1/users/me")
check("No-auth → 401/403", r.status_code in (401, 403), r.text)

r = client.get("/api/v1/users/me", headers={"Authorization": "Bearer invalid.token.here"})
check("Bad token → 401", r.status_code == 401, r.text)

# User can't access admin
r = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {USER_TOKEN}"})
check("User token → admin endpoint = 403", r.status_code == 403, r.text)


# ============= 12. CANCELLATION =============
section("12. Cancellation flow (refund window logic)")
# Make a fresh booking
pickup2 = (datetime.utcnow() + timedelta(days=2)).isoformat()
dropoff2 = (datetime.utcnow() + timedelta(days=2, hours=4)).isoformat()
r = client.post(
    "/api/v1/bookings",
    json={"vehicle_id": VEHICLE_ID, "pickup_at": pickup2, "dropoff_at": dropoff2},
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Second booking created", r.status_code == 201, r.text)
B2 = r.json()["id"]

r = client.post(
    f"/api/v1/bookings/{B2}/pay",
    json={"booking_id": B2, "method": "upi"},
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Second booking paid", r.status_code == 200)

r = client.post(
    f"/api/v1/bookings/{B2}/cancel",
    json={"reason": "Plans changed"},
    headers={"Authorization": f"Bearer {USER_TOKEN}"},
)
check("Cancel >24h before pickup → REFUNDED", r.status_code == 200, r.text)
check("Status CANCELLED", r.json()["status"] == "CANCELLED")
check("Payment status REFUNDED", r.json()["payment_status"] == "REFUNDED")


print(f"\n{BOLD}{GREEN}🎉 ALL TESTS PASSED 🎉{RESET}\n")
