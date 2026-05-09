"""Seed the database with realistic test data.

Run from project root:
    python scripts/seed.py

Creates:
- Admin (already bootstrapped via app startup, but ensures it)
- 3 sample partners (KYC approved)
- 6 sample vehicles (2 bikes, 2 cars, 2 autos) — all verified and available
- 5 sample users with DLs

Use the printed OTP placeholders to log in via the API for testing.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta
from app.db.session import Base, engine, SessionLocal
from app.models import (
    User, Partner, PartnerDocument, Vehicle, AdminUser, AdminRole,
    KYCStatus, DocumentType, VehicleType, FuelType, TransmissionType, VehicleStatus,
)
from app.core.security import hash_password
from app.core.config import settings


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ---- Admin ----
        if not db.query(AdminUser).filter(AdminUser.email == settings.ADMIN_EMAIL).first():
            db.add(AdminUser(
                email=settings.ADMIN_EMAIL,
                full_name="Super Admin",
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role=AdminRole.SUPERADMIN,
                is_active=True,
            ))
            db.commit()
            print(f"✅ Admin created: {settings.ADMIN_EMAIL} / {settings.ADMIN_PASSWORD}")
        else:
            print("ℹ️  Admin exists")

        # ---- Partners ----
        partners_data = [
            {
                "phone": "+919811111111", "email": "ops@mumbairentals.in",
                "business_name": "Mumbai Self-Drive", "contact_person": "Rohan Patel",
                "city": "Mumbai", "state": "Maharashtra", "pincode": "400001",
                "address_line": "12 Marine Drive", "hub_lat": 18.9388, "hub_lng": 72.8354,
            },
            {
                "phone": "+919822222222", "email": "info@delhirides.in",
                "business_name": "Delhi Rides", "contact_person": "Priya Singh",
                "city": "Delhi", "state": "Delhi", "pincode": "110001",
                "address_line": "Connaught Place", "hub_lat": 28.6315, "hub_lng": 77.2167,
            },
            {
                "phone": "+919833333333", "email": "hi@indorewheels.in",
                "business_name": "Indore Wheels", "contact_person": "Vikram Joshi",
                "city": "Indore", "state": "Madhya Pradesh", "pincode": "452001",
                "address_line": "Vijay Nagar", "hub_lat": 22.7196, "hub_lng": 75.8577,
            },
        ]
        partner_objs = []
        for pd in partners_data:
            existing = db.query(Partner).filter(Partner.phone == pd["phone"]).first()
            if existing:
                partner_objs.append(existing)
                continue
            p = Partner(
                **pd,
                phone_verified=True,
                kyc_status=KYCStatus.APPROVED,
                kyc_remarks="Approved via seed",
                bank_account_number="50100012345678",
                bank_ifsc="HDFC0001234",
                bank_holder_name=pd["business_name"],
            )
            db.add(p)
            db.flush()
            db.add_all([
                PartnerDocument(partner_id=p.id, doc_type=DocumentType.AADHAAR, doc_number="123456789012", file_url="/uploads/kyc/seed_aadhaar.pdf", is_verified=True),
                PartnerDocument(partner_id=p.id, doc_type=DocumentType.PAN, doc_number="ABCDE1234F", file_url="/uploads/kyc/seed_pan.pdf", is_verified=True),
            ])
            partner_objs.append(p)
        db.commit()
        print(f"✅ {len(partner_objs)} partners seeded")

        # ---- Vehicles ----
        vehicles_data = [
            (0, VehicleType.BIKE, "Royal Enfield", "Classic 350", 2023, "Black", "MH01AB1234", FuelType.PETROL, TransmissionType.MANUAL, 2, 120, 1500, 8500, 3000, "Marine Drive, Mumbai", 18.9388, 72.8354, "Mumbai", "Premium classic bike, well-maintained", "ABS,Disc Brakes,LED Headlamp"),
            (0, VehicleType.CAR, "Maruti Suzuki", "Swift VXi", 2022, "White", "MH01CD5678", FuelType.PETROL, TransmissionType.MANUAL, 5, 200, 2200, 13000, 5000, "Marine Drive, Mumbai", 18.9388, 72.8354, "Mumbai", "Compact and fuel-efficient", "AC,Power Steering,Music System"),
            (1, VehicleType.BIKE, "Honda", "Activa 6G", 2024, "Grey", "DL01EF9012", FuelType.PETROL, TransmissionType.AUTOMATIC, 2, 60, 700, 4000, 1500, "Connaught Place, Delhi", 28.6315, 77.2167, "Delhi", "City scooter, perfect for commuting", "LED,Mobile Charger"),
            (1, VehicleType.CAR, "Hyundai", "Creta SX", 2023, "Blue", "DL01GH3456", FuelType.DIESEL, TransmissionType.AUTOMATIC, 5, 350, 4500, 27000, 8000, "Connaught Place, Delhi", 28.6315, 77.2167, "Delhi", "Premium SUV with sunroof", "Sunroof,AC,Cruise Control,Reverse Camera"),
            (2, VehicleType.AUTO, "Bajaj", "RE Auto", 2021, "Yellow", "MP09IJ7890", FuelType.CNG, TransmissionType.MANUAL, 3, 80, 900, 5000, 2000, "Vijay Nagar, Indore", 22.7196, 75.8577, "Indore", "CNG auto for short city trips", "Sturdy build"),
            (2, VehicleType.BIKE, "TVS", "Apache RTR 160", 2023, "Red", "MP09KL1234", FuelType.PETROL, TransmissionType.MANUAL, 2, 90, 1100, 6500, 2500, "Vijay Nagar, Indore", 22.7196, 75.8577, "Indore", "Sporty commuter bike", "Disc Brakes,Digital Console"),
        ]
        existing_regs = {v.registration_number for v in db.query(Vehicle).all()}
        added = 0
        for (idx, vt, brand, model, year, color, reg, fuel, trans, seats, hr, dr, wr, dep, addr, lat, lng, city, desc, feats) in vehicles_data:
            if reg in existing_regs:
                continue
            v = Vehicle(
                partner_id=partner_objs[idx].id,
                vehicle_type=vt, brand=brand, model=model, year=year, color=color,
                registration_number=reg, fuel_type=fuel, transmission=trans, seats=seats,
                hourly_rate=hr, daily_rate=dr, weekly_rate=wr, security_deposit=dep,
                pickup_address=addr, pickup_lat=lat, pickup_lng=lng, pickup_city=city,
                description=desc, features=feats,
                status=VehicleStatus.AVAILABLE, is_verified=True,
            )
            db.add(v)
            added += 1
        db.commit()
        print(f"✅ {added} vehicles seeded")

        # ---- Users ----
        users_data = [
            ("+919876543210", "Aarav Sharma",  "aarav@example.com",  "MH0120220001234"),
            ("+919876543211", "Diya Patel",    "diya@example.com",   "DL0120220005678"),
            ("+919876543212", "Kabir Singh",   "kabir@example.com",  "MP0920220009012"),
            ("+919876543213", "Ananya Iyer",   "ananya@example.com", "MH0120230001111"),
            ("+919876543214", "Rohan Kapoor",  "rohan@example.com",  "DL0120230002222"),
        ]
        added_u = 0
        for phone, name, email, dl in users_data:
            if db.query(User).filter(User.phone == phone).first():
                continue
            db.add(User(
                phone=phone, full_name=name, email=email, dl_number=dl, dl_verified=True,
                phone_verified=True, is_active=True,
                last_lat=19.0, last_lng=72.8,
            ))
            added_u += 1
        db.commit()
        print(f"✅ {added_u} users seeded")

        print("\n🎯 Seeding complete!")
        print("\n📞 Test phones (request OTP via /api/v1/auth/...):")
        print("   USERS:")
        for p, n, _, _ in users_data:
            print(f"     - {p}  ({n})")
        print("   PARTNERS:")
        for pd in partners_data:
            print(f"     - {pd['phone']}  ({pd['business_name']})")
        print(f"\n🔐 ADMIN: {settings.ADMIN_EMAIL} / {settings.ADMIN_PASSWORD}")
        print("\n💡 In dev mode (no Twilio configured), OTPs print to the server console & are returned in `debug_otp` field.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
