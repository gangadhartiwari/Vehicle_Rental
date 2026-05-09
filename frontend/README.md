# Vehicle Rental — Frontend

A modern, multi-page frontend for the Vehicle Rental FastAPI backend. Built with vanilla HTML, CSS, and JavaScript — no build step required.

## Quick Start

### 1. Start the backend

From the project root:

```bash
cd vehicle_rental
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend will run at `http://localhost:8000` and auto-create a default admin account:
- **Email:** `admin@vehiclerental.com`
- **Password:** `Admin@12345`

### 2. Serve the frontend

From the `frontend/` folder, run any static server. The simplest:

```bash
cd frontend
python -m http.server 3000
```

Then open **http://localhost:3000** in your browser.

> The backend's CORS is preconfigured to accept `http://localhost:3000`, so this port works out of the box. If you serve on a different port, update `CORS_ORIGINS` in your backend `.env`.

### 3. (Optional) Point at a different backend

By default the frontend talks to `http://localhost:8000`. To override, run this once in your browser console:

```js
localStorage.setItem('rw_api_base', 'https://your-backend.example.com')
```

---

## Page Tour

| Page | Path | Purpose |
|------|------|---------|
| Landing | `/index.html` | Public homepage — hero, how it works, role cards |
| Browse | `/pages/browse.html` | Public vehicle search with filters (type, city, price, fuel, transmission, dates) |
| Vehicle Detail | `/pages/vehicle-detail.html?id=...` | Full vehicle view with sticky booking widget, fare estimation, ratings |
| Login | `/pages/login.html` | Single login page with tabs for Rider / Partner / Admin |
| Partner Onboarding | `/pages/partner-onboard.html` | Marketing page for partner sign-up |
| Rider Dashboard | `/pages/user-dashboard.html` | Bookings, profile, driving licence, pay/cancel/rate flows |
| Partner Dashboard | `/pages/partner-dashboard.html` | Vehicles, bookings (with pickup/drop-off OTP verification), KYC, bank account |
| Admin Dashboard | `/pages/admin-dashboard.html` | Stats, user/partner/vehicle/booking/rating moderation |

---

## OTP Login (Dev Mode)

Riders and Partners log in with phone + OTP. If your backend has no Twilio credentials configured, it runs in dev mode and returns a `debug_otp` in the response — the login page displays this in a yellow banner so you can copy and paste it during testing.

For Admin, use email + password.

---

## Booking Lifecycle (How to Test)

1. **Rider** signs up via OTP → completes profile + uploads DL
2. **Partner** signs up via OTP → completes profile, adds bank account, uploads KYC documents, submits for review
3. **Admin** approves the partner's KYC
4. Partner adds a vehicle (now unlocked)
5. **Admin** verifies the vehicle (so it appears in public search)
6. Rider browses → opens vehicle → estimates fare → books
7. Rider pays (mock payment)
8. Rider shares **pickup OTP** with partner → partner verifies → trip starts
9. Rider shares **drop-off OTP** → partner verifies (with optional damage charges) → trip completes
10. Rider rates the trip → can download invoice PDF

---

## File Structure

```
frontend/
├── index.html              # Landing page
├── README.md               # This file
├── css/
│   └── styles.css          # Full design system
├── js/
│   └── app.js              # API client, auth, helpers, formatters
├── assets/                 # (empty — for any future static assets)
└── pages/
    ├── browse.html
    ├── vehicle-detail.html
    ├── login.html
    ├── partner-onboard.html
    ├── user-dashboard.html
    ├── partner-dashboard.html
    └── admin-dashboard.html
```

---

## Design Notes

- **Aesthetic:** modern editorial / premium — warm cream background, deep emerald accent, Fraunces display + Inter body fonts
- **No frameworks, no build step** — drop-in static files that work with any HTTP server
- **All API calls** go through the `api()` wrapper in `js/app.js`, which handles JWT auth, JSON, and FormData uploads uniformly
- **Auth tokens** are stored in `localStorage` (`rw_access_token`, `rw_refresh_token`, `rw_role`, `rw_user_id`)
- **Status badges** are colour-coded for every backend status (booking, payment, KYC, vehicle)
- **Toasts and modals** are built in — no external UI library needed

---

## Troubleshooting

**"Failed to fetch" on every request**
→ Backend isn't running, or CORS isn't accepting your frontend origin. Check that the backend logs show it started on port 8000, and that you're serving the frontend on port 3000.

**Login works but dashboard shows "Unauthorized"**
→ Token expired or backend was restarted with a different `SECRET_KEY`. Log out and log in again.

**Partner can't add vehicles**
→ KYC must be APPROVED. Use the admin dashboard to approve the partner.

**Vehicle doesn't appear in public search**
→ Admin must verify the vehicle (admin dashboard → Vehicles → Verify).
