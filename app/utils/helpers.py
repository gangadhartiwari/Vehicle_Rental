"""Geo helpers and invoice PDF."""
import math
from io import BytesIO
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generate_invoice_pdf(booking, vehicle, user, partner, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, title=f"Invoice {booking.booking_code}")
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>INVOICE — {booking.booking_code}</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Date: {datetime.utcnow().strftime('%d %b %Y')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    party = [
        ["Customer", user.full_name or user.phone],
        ["Phone", user.phone],
        ["Provider", partner.business_name or partner.contact_person or partner.phone],
        ["Vehicle", f"{vehicle.brand} {vehicle.model} ({vehicle.registration_number})"],
        ["Pickup", booking.pickup_at.strftime("%d %b %Y, %H:%M")],
        ["Dropoff", booking.dropoff_at.strftime("%d %b %Y, %H:%M")],
        ["Duration", f"{booking.duration_hours} hours"],
    ]
    t1 = Table(party, hAlign="LEFT", colWidths=[120, 360])
    t1.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
    ]))
    story.append(t1)
    story.append(Spacer(1, 18))

    final = booking.final_amount or booking.total_amount
    breakdown = [
        ["Description", "Amount (₹)"],
        ["Rental charge", f"{booking.base_amount:.2f}"],
        ["GST", f"{booking.gst_amount:.2f}"],
        ["Security deposit (refundable)", f"{booking.security_deposit:.2f}"],
        ["Late fee", f"{booking.late_fee:.2f}"],
        ["Damage charges", f"{booking.damage_charges:.2f}"],
        ["Discount", f"-{booking.discount_amount:.2f}"],
        ["TOTAL", f"{final:.2f}"],
    ]
    t2 = Table(breakdown, hAlign="LEFT", colWidths=[300, 180])
    t2.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightyellow),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(t2)
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"Payment Status: <b>{booking.payment_status.value}</b> &nbsp; | &nbsp; Booking Status: <b>{booking.status.value}</b>",
        styles["Normal"],
    ))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Thank you for using our service.", styles["Italic"]))

    doc.build(story)
    return output_path
