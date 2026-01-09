from flask import Blueprint, render_template, request
import os
from flask_mail import Mail, Message
from dotenv import load_dotenv
from twilio.rest import Client
load_dotenv()

complaint_bp = Blueprint("complaint", __name__)

mail = Mail()

complaints = []

facility_heads_data = {
    "Restroom": {
        "email": "katharbai5@gmail.com",
        "phone": "6380291677",
        "locations": ["Parking", "Pll Hall G-Floor"]
    },
    "Drinking Water": {
        "email": "24mca022@americancollege.edu.in",
        "phone": "9364665666",
        "locations": ["Near Library", "Near Centenary Hall"]
    },
    "Electrical & Plumbing": {
        "email": "24mca017@americancollege.edu.in",
        "phone": "8925390937",
        "locations": ["Main Hall", "Pll hall"]
    }
}

facility_heads = {}
for facility, info in facility_heads_data.items():
    for loc in info["locations"]:
        facility_heads[(facility, loc)] = info


def send_email(to_email, facility, location, issue):
    msg = Message(
        subject="🚨 New Facility Complaint",
        recipients=[to_email]
    )
    msg.body = f"""
Facility: {facility}
Location: {location}
Issue: {issue}
"""
    mail.send(msg)


def send_sms(phone, facility, location):
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    client.messages.create(
        body=f"New complaint: {facility} at {location}",
        from_=os.getenv("TWILIO_PHONE"),
        to=f"+91{phone}"
    )


@complaint_bp.route("/complaint", methods=["GET", "POST"])
def complaint():
    from app import conn, cur
    if request.method == "POST":
        facility = request.form["facility"]
        location = request.form["location"]
        issue = request.form["issue"]

        # Save complaint to DB (PostgreSQL)
        cur.execute(
            "INSERT INTO complaints (facility, location, issue) VALUES (%s, %s, %s)",
            (facility, location, issue)
        )
        conn.commit()

        # 2️⃣ Send to facility head
        head = facility_heads.get((facility, location))
        if head:
            send_email(head["email"], facility, location, issue)
            send_sms(head["phone"], facility, location)

        return "✅ Complaint submitted successfully"

    return render_template("complaint.html")
