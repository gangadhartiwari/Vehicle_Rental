# 🚗 Vehicle Rental API (Self-Drive)

A production-ready FastAPI backend for a self-drive vehicle rental platform — bikes, cars, autos. Inspired by Zoomcar / Royal Brothers. Three roles: **User** (rider), **Partner** (vehicle provider), **Admin** (operations).

---

## ✨ Features

- **OTP-based phone login** for users and partners (email + password for admins)
- **JWT auth** (access + refresh tokens) with role-based access control
- **Partner KYC** — multi-document upload (Aadhaar, PAN, GST, etc.) with admin review workflow
- **Vehicle inventory** with images, RC, insurance docs; admin verification gate before going live
- **Geo-search** — find vehicles within radius of user's location, with date-window availability
- **Booking engine** — fare estimate, conflict detection, hourly/daily/weekly slabs, GST, security deposit
- **OTP-based vehicle handover** — separate pickup OTP and dropoff OTP exchanged between user and partner
- **Late fees & damage charges** auto-applied on dropoff
- **Cancellation refund window** — 100% > 24h, 50% within 24h, 0% within 2h
- **Ratings & reviews** with auto-recalc of vehicle/partner avg rating
- **PDF invoices** (ReportLab)
- **Admin dashboard** — stats, KYC review, vehicle verification, user/partner block, rating moderation
- **Auto-generated Swagger / ReDoc** documentation

## 🛠 Tech Stack

| Layer | Choice |
|---|---|
| Framework | FastAPI 0.115 (async) |
| ORM | SQLAlchemy 2.0 |
| DB (dev) | SQLite |
| DB (prod) | PostgreSQL (just change `DATABASE_URL`) |
| Auth | JWT (`python-jose`) + bcrypt |
| Validation | Pydantic v2 |
| OTP delivery | Twilio (auto-falls-back to console in dev) |
| PDF | ReportLab |
| Testing | FastAPI TestClient |

---

## 🎨 Frontend

A complete modern frontend is included in the [`frontend/`](./frontend) folder — vanilla HTML, CSS, and JS, no build step. To run it:

```bash
cd frontend
python -m http.server 3000
```

Then open http://localhost:3000. See [`frontend/README.md`](./frontend/README.md) for the full page tour, design notes, and the end-to-end booking lifecycle walkthrough.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (tested on 3.12)
- pip

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env — but defaults work out of the box for local dev
```

### 3. Seed sample data (optional but recommended)
```bash
python scripts/seed.py
```
This creates 3 partners (KYC approved), 6 verified vehicles across Mumbai/Delhi/Indore, 5 users with DLs, and the admin account.

### 4. Run
```bash
uvicorn app.main:app --reload
```

### 5. Open the docs
- Swagger UI → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc

---

## 🔐 Default Credentials

| Role | Login |
|---|---|
| **Admin** | `admin@vehiclerental.com` / `Admin@12345` |
| **User (seeded)** | `+919876543210`, `+919876543211`, … |
| **Partner (seeded)** | `+919811111111` (Mumbai), `+919822222222` (Delhi), `+919833333333` (Indore) |

In dev mode (no Twilio configured), OTPs are:
1. Printed to the server console with a 📱 prefix
2. Returned in the API response in the `debug_otp` field — so Postman/Swagger flows are seamless

---

## 📋 The Three Flows

### User flow
```
request-otp → verify-otp (auto-creates account)
            ↓
update profile + upload DL
            ↓
search vehicles (filter by type, city, geo radius, dates)
            ↓
estimate fare → create booking → pay
            ↓
[at pickup] show pickup OTP to partner → trip starts
[at dropoff] show dropoff OTP to partner → trip ends
            ↓
rate the rental → download invoice
```

### Partner flow
```
request-otp → verify-otp
            ↓
fill profile + bank details + upload Aadhaar & PAN (min req)
            ↓
submit KYC → wait for admin approval
            ↓
add vehicles (only allowed once KYC is APPROVED)
            ↓
admin verifies each vehicle → vehicle goes live
            ↓
manage bookings, verify pickup/dropoff OTPs at handover
```

### Admin flow
```
login (email + password)
            ↓
review pending KYCs → approve / reject (with remarks)
            ↓
verify vehicles (activates them in search)
            ↓
monitor: stats dashboard, all bookings, all ratings
            ↓
moderate: block users/partners, force-cancel, delete reviews
```

---

## 🧪 Testing

Run the comprehensive E2E smoke test (no external deps, uses TestClient):
```bash
PYTHONPATH=. python tests/test_e2e.py
```
This walks through all 12 sections — health, OTP login (3 roles), KYC, vehicle CRUD, search with geo, fare estimate, booking, payment, OTP handover, rating, invoice, admin stats, auth enforcement, cancellation refunds. **Every test must pass before considering this production-ready.**

## 📮 Postman

Import `postman_collection.json` into Postman. Set the `base_url` collection variable (default `http://localhost:8000`). All auth requests auto-save tokens to collection variables — just run them top-to-bottom in each folder.

---

## 🗂 Project Structure

```
vehicle_rental/
├── app/
│   ├── main.py                 # FastAPI app, lifespan, middleware
│   ├── core/
│   │   ├── config.py           # Pydantic settings (env-driven)
│   │   └── security.py         # bcrypt + JWT helpers
│   ├── db/
│   │   └── session.py          # Engine, SessionLocal, Base, get_db
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── partner.py
│   │   ├── vehicle.py
│   │   ├── booking.py
│   │   └── misc.py             # OTP, Rating, Admin
│   ├── schemas/                # Pydantic request/response models
│   ├── services/               # Business logic
│   │   ├── otp_service.py
│   │   ├── pricing_service.py
│   │   ├── booking_service.py
│   │   └── file_service.py
│   ├── api/
│   │   ├── deps.py             # get_current_user/partner/admin
│   │   └── v1/
│   │       ├── router.py       # Aggregates all routers
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── users.py
│   │           ├── partners.py
│   │           ├── vehicles.py
│   │           ├── bookings.py
│   │           ├── ratings.py
│   │           ├── admin.py
│   │           └── health.py
│   └── utils/
│       └── helpers.py          # haversine, invoice PDF
├── tests/
│   └── test_e2e.py             # Full flow integration test
├── scripts/
│   └── seed.py                 # Sample data
├── uploads/                    # KYC docs, vehicle images, invoices (DEV only — use S3 in prod)
├── postman_collection.json
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🗄 Database Schema (key tables)

```
users
  id, phone (unique), email, full_name, profile_image,
  dl_number, dl_image, dl_verified,
  is_active, is_blocked, phone_verified,
  last_lat, last_lng, created_at, updated_at

partners
  id, phone (unique), email, business_name, contact_person,
  address_line, city, state, pincode, hub_lat, hub_lng,
  kyc_status (PENDING|SUBMITTED|APPROVED|REJECTED), kyc_remarks,
  bank_account_number, bank_ifsc, bank_holder_name,
  is_active, is_blocked, phone_verified,
  total_earnings, total_bookings, avg_rating,
  created_at, updated_at

partner_documents
  id, partner_id, doc_type (AADHAAR|PAN|GST|...),
  doc_number, file_url, is_verified, uploaded_at

vehicles
  id, partner_id, vehicle_type (BIKE|CAR|AUTO),
  brand, model, year, color, registration_number (unique),
  fuel_type, transmission, seats,
  hourly_rate, daily_rate, weekly_rate, security_deposit,
  pickup_address, pickup_lat, pickup_lng, pickup_city,
  images (csv), description, features,
  status (AVAILABLE|BOOKED|UNDER_MAINTENANCE|INACTIVE),
  is_verified, avg_rating, total_bookings,
  rc_number, rc_image, insurance_number, insurance_image,
  insurance_expiry, pollution_cert_expiry,
  created_at, updated_at

bookings
  id, booking_code (unique), user_id, vehicle_id, partner_id,
  pickup_at, dropoff_at, actual_pickup_at, actual_dropoff_at,
  pickup_location, dropoff_location,
  duration_hours,
  base_amount, gst_amount, security_deposit, discount_amount,
  total_amount, late_fee, damage_charges, final_amount,
  status (PENDING_PAYMENT|CONFIRMED|ONGOING|COMPLETED|CANCELLED|NO_SHOW),
  payment_status (PENDING|PAID|REFUNDED|FAILED),
  cancellation_reason, cancelled_by, notes,
  pickup_otp, dropoff_otp,
  created_at, updated_at

payments
  id, booking_id (1:1), amount, method, transaction_id,
  gateway, gateway_response, status, paid_at, created_at

otp_records
  id, phone, code_hash (bcrypt), purpose, attempts,
  is_used, expires_at, created_at

ratings
  id, booking_id (unique), user_id, vehicle_id, partner_id,
  stars, review, created_at

admin_users
  id, email (unique), full_name, password_hash,
  role (SUPERADMIN|OPERATIONS|SUPPORT),
  is_active, last_login, created_at
```

---

## 🔄 Booking State Machine

```
       create               pay                 verify pickup OTP
PENDING_PAYMENT ─────► CONFIRMED ─────► CONFIRMED ─────► ONGOING
       │                  │                                 │
       │ cancel           │ cancel                          │ verify dropoff OTP
       ▼                  ▼                                 ▼
   CANCELLED          CANCELLED (refund per window)     COMPLETED
                                                            │
                                                            ▼
                                                       can rate + invoice
```

---

## 💰 Pricing Logic

The pricing service auto-picks the most appropriate slab:
| Duration | Basis |
|---|---|
| < 24 hours | hourly_rate × hours |
| 24h – 6d 23h, or no weekly_rate | daily_rate × ceil(days) |
| 7+ days, weekly_rate present | weekly_rate × ceil(weeks) |

GST is added on top of base. Security deposit is added to the total but tracked separately for refund.

**Late fee**: 1.5× hourly rate per (rounded-up) hour past scheduled dropoff.

**Cancellation refund** (on the rental amount, deposit always refunded):
- More than 24h before pickup → 100%
- 2–24h before pickup → 50%
- Less than 2h → 0%

---

## 🔐 Security Notes

- Passwords/OTPs are hashed with bcrypt (12 rounds).
- JWT tokens are signed with HS256 — set a strong `SECRET_KEY` in `.env` for production (use `openssl rand -hex 32`).
- OTPs are 6-digit, expire in 5 min, capped at 5 verify attempts and 30s resend cooldown.
- All write operations are role-gated; admin-only endpoints reject non-admin tokens with 403.
- File uploads are validated for extension (jpg/jpeg/png/pdf/webp) and size (10MB default).
- The `/uploads` static mount is for **dev only** — in production, push files to S3/Cloudinary and serve via CDN.

---

## 🌐 Production Deployment Checklist

- [ ] Switch `DATABASE_URL` to PostgreSQL
- [ ] Generate strong `SECRET_KEY` and rotate periodically
- [ ] Wire real Twilio credentials (or your preferred OTP gateway)
- [ ] Replace mock payment endpoint with real Razorpay/Stripe webhook flow
- [ ] Move file storage from local `/uploads` to S3 (use `boto3`)
- [ ] Add Redis for OTP storage and rate-limiting (the code already supports `REDIS_URL`)
- [ ] Run `alembic init alembic && alembic revision --autogenerate` for migrations
- [ ] Put behind nginx + HTTPS (Let's Encrypt)
- [ ] Configure CORS origins to your real frontend domains
- [ ] Set `DEBUG=False`
- [ ] Add logging aggregation (Loki / CloudWatch / Datadog)
- [ ] Add monitoring (Sentry for errors, Prometheus + Grafana for metrics)
- [ ] Set up daily DB backups
- [ ] Run `pytest tests/test_e2e.py` in CI

---

## 📜 License

MIT — use it freely.
