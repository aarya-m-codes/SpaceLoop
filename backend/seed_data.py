import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Flask, current_app, has_app_context
from sqlalchemy.exc import SQLAlchemyError

from backend.core.database import db
from models import (
    Booking,
    EscrowTransaction,
    Notification,
    Review,
    Space,
    User,
    utc_now,
)
from security import hash_password

logger = logging.getLogger("spaceloop.seed")

# Common password for all demo accounts as explicitly mandated
DEMO_PASSWORD_RAW = "SpaceLoopDemo123!"


def ensure_demo_accounts(app: Flask | None = None) -> dict[str, str]:
    """Idempotently ensure required SpaceLoop demo accounts exist and are verified.
    
    Guarantees:
    1. seeker.rohit@spaceloop.in  (Password: SpaceLoopDemo123!, Role: seeker)
    2. host.arjun@spaceloop.in     (Password: SpaceLoopDemo123!, Role: host)
    3. admin.spaceloop@spaceloop.in (Password: SpaceLoopDemo123!, Role: admin)
    
    Safe to execute in both development (SQLite) and production/staging (PostgreSQL) environments.
    """
    target_app = app or (current_app._get_current_object() if has_app_context() else None)
    if target_app is not None and not has_app_context():
        with target_app.app_context():
            return _ensure_demo_accounts_internal()
    return _ensure_demo_accounts_internal()


def _ensure_demo_accounts_internal() -> dict[str, str]:
    status_report: dict[str, str] = {}
    hashed_pwd = hash_password(DEMO_PASSWORD_RAW)

    demo_specs = [
        {
            "email": "seeker.rohit@spaceloop.in",
            "full_name": "Rohit Sharma",
            "phone": "+919876501234",
            "role": "GUEST",
            "kyc_status": "VERIFIED",
            "kyc_document_type": None,
        },
        {
            "email": "host.arjun@spaceloop.in",
            "full_name": "Arjun Verma",
            "phone": "+919833344455",
            "role": "HOST",
            "kyc_status": "VERIFIED",
            "kyc_document_type": "Aadhaar",
        },
        {
            "email": "admin.spaceloop@spaceloop.in",
            "full_name": "SpaceLoop Administrator",
            "phone": "+919876543210",
            "role": "ADMIN",
            "kyc_status": "VERIFIED",
            "kyc_document_type": "Aadhaar",
        },
        # Ensure legacy aliases also remain verified with demo password for full backwards compatibility
        {
            "email": "admin@spaceloop.in",
            "full_name": "SpaceLoop Administrator",
            "phone": "+919876543210",
            "role": "ADMIN",
            "kyc_status": "VERIFIED",
            "kyc_document_type": "Aadhaar",
        },
        {
            "email": "host.rahul@spaceloop.in",
            "full_name": "Rahul Sharma",
            "phone": "+919811122233",
            "role": "HOST",
            "kyc_status": "VERIFIED",
            "kyc_document_type": "PAN",
        },
    ]

    try:
        for spec in demo_specs:
            user = User.query.filter_by(email=spec["email"]).first()
            if user:
                # Update existing record idempotently
                user.password_hash = hashed_pwd
                user.role = spec["role"]
                user.is_active = True
                user.is_verified = True
                user.kyc_status = spec["kyc_status"]
                if spec.get("kyc_document_type"):
                    user.kyc_document_type = spec["kyc_document_type"]
                status_report[spec["email"]] = "updated"
            else:
                # Create record
                user = User(
                    email=spec["email"],
                    password_hash=hashed_pwd,
                    full_name=spec["full_name"],
                    phone=spec["phone"],
                    role=spec["role"],
                    is_active=True,
                    is_verified=True,
                    kyc_status=spec["kyc_status"],
                    kyc_document_type=spec.get("kyc_document_type"),
                )
                db.session.add(user)
                status_report[spec["email"]] = "created"

        db.session.flush()

        # Ensure host.arjun has an active Space listing so the Host Dashboard displays real metrics
        host_arjun = User.query.filter_by(email="host.arjun@spaceloop.in").first()
        if host_arjun:
            existing_space = Space.query.filter_by(host_id=host_arjun.id).first()
            if not existing_space:
                arjun_space = Space(
                    host_id=host_arjun.id,
                    title="Koramangala 80ft Road Creator Studio & Desks",
                    description="Acoustically treated creator studio and quiet ergonomic workstations in Koramangala 4th Block.",
                    space_type="studio",
                    address_line1="412, 80 Feet Road, 4th Block, Koramangala",
                    city="Bengaluru",
                    state="Karnataka",
                    pincode="560034",
                    latitude=12.9352,
                    longitude=77.6245,
                    price_per_hour=200.0,
                    price_per_day=1400.0,
                    capacity=10,
                    amenities=["High-Speed WiFi", "Soundproofing", "Podcast Microphones", "Ergonomic Chairs", "Power Backup"],
                    rules="No smoking. Booking confirmation required at entrance.",
                    is_active=True,
                    is_approved=True,
                )
                db.session.add(arjun_space)
                status_report["host_arjun_space"] = "created"

        db.session.commit()
        logger.info(f"Demo accounts successfully synchronized: {status_report}")
        return status_report
    except SQLAlchemyError as err:
        db.session.rollback()
        logger.error(f"Failed to synchronize demo accounts: {err}", exc_info=True)
        raise


def seed_all(app: Flask | None = None) -> dict[str, int]:
    """Populate database with realistic seed data for the Indian marketplace.
    
    Returns a summary count of created entities.
    """
    target_app = app or (current_app._get_current_object() if has_app_context() else None)
    if target_app is not None and not has_app_context():
        with target_app.app_context():
            return _seed_all_internal()
    return _seed_all_internal()


def _seed_all_internal() -> dict[str, int]:
    counts = {"users": 0, "spaces": 0, "bookings": 0, "reviews": 0}

    # First, always synchronize demo accounts
    demo_status = _ensure_demo_accounts_internal()
    counts["demo_accounts_synced"] = len(demo_status)

    # Check if full seed catalog already populated
    if Space.query.count() >= 3:
        logger.info("Database spaces catalog already populated. Skipping duplicate entities.")
        return counts

    try:
        # Resolve host references for sample spaces
        host_rahul = User.query.filter_by(email="host.rahul@spaceloop.in").first()
        host_arjun = User.query.filter_by(email="host.arjun@spaceloop.in").first()
        seeker_rohit = User.query.filter_by(email="seeker.rohit@spaceloop.in").first()

        # Seed spaces if needed
        space1 = Space.query.filter_by(title="Indiranagar Tech Loft & Dedicated Desk").first()
        if not space1 and host_rahul:
            space1 = Space(
                host_id=host_rahul.id,
                title="Indiranagar Tech Loft & Dedicated Desk",
                description="High-speed 1Gbps fiber internet, ergonomic Herman Miller chairs, power backup, and specialty coffee in prime 100ft Road Indiranagar.",
                space_type="desk",
                address_line1="1248, 100 Feet Road, HAL 2nd Stage",
                city="Bengaluru",
                state="Karnataka",
                pincode="560038",
                latitude=12.9784,
                longitude=77.6408,
                price_per_hour=150.0,
                price_per_day=950.0,
                capacity=12,
                amenities=["High-Speed WiFi", "Ergonomic Chairs", "Power Backup", "Espresso Machine", "Meeting Pod"],
                rules="Quiet hours between 2 PM and 4 PM. No smoking on premises.",
                is_active=True,
                is_approved=True,
            )
            db.session.add(space1)
            counts["spaces"] += 1

        space2 = Space.query.filter_by(title="BKC Executive Boardroom & Media Studio").first()
        if not space2 and (host_arjun or host_rahul):
            space2 = Space(
                host_id=(host_arjun or host_rahul).id,
                title="BKC Executive Boardroom & Media Studio",
                description="Soundproof conference room with 4K video conferencing, dual monitors, podcast mics, and rooftop terrace in Mumbai's financial center.",
                space_type="studio",
                address_line1="Plot C-59, G Block, Bandra Kurla Complex",
                city="Mumbai",
                state="Maharashtra",
                pincode="400051",
                latitude=19.0657,
                longitude=72.8687,
                price_per_hour=450.0,
                price_per_day=3200.0,
                capacity=8,
                amenities=["4K Conference Display", "Soundproofing", "Podcast Microphones", "Whiteboard", "Valet Parking"],
                rules="Prior reservation required for recording studio equipment.",
                is_active=True,
                is_approved=True,
            )
            db.session.add(space2)
            counts["spaces"] += 1

        space3 = Space.query.filter_by(title="Connaught Place Colonial Work Pod").first()
        if not space3 and host_rahul:
            space3 = Space(
                host_id=host_rahul.id,
                title="Connaught Place Colonial Work Pod",
                description="Charming colonial architecture meets modern coworking. Located 2 minutes from Rajiv Chowk Metro station.",
                space_type="private_office",
                address_line1="Block B, Inner Circle, Connaught Place",
                city="New Delhi",
                state="Delhi",
                pincode="110001",
                latitude=28.6315,
                longitude=77.2167,
                price_per_hour=250.0,
                price_per_day=1800.0,
                capacity=4,
                amenities=["Metro Adjacent", "High-Speed WiFi", "Printer/Scanner", "Tea/Coffee Bar", "Air Conditioned"],
                rules="Valid ID verification required at security gate.",
                is_active=True,
                is_approved=True,
            )
            db.session.add(space3)
            counts["spaces"] += 1

        db.session.flush()

        # Seed sample booking if none exist
        if Booking.query.count() == 0 and space1 and seeker_rohit:
            start_time = utc_now() + timedelta(days=1)
            end_time = start_time + timedelta(hours=4)
            base_amt = 150.0 * 4
            fee = base_amt * 0.10
            gst = fee * 0.18
            total = base_amt + fee + gst

            booking1 = Booking(
                space_id=space1.id,
                guest_id=seeker_rohit.id,
                start_time=start_time,
                end_time=end_time,
                total_hours=4.0,
                base_amount=base_amt,
                platform_fee=fee,
                taxes_gst=gst,
                total_amount=total,
                currency="INR",
                status="CONFIRMED",
                access_code="SPACE99",
            )
            db.session.add(booking1)
            db.session.flush()
            counts["bookings"] += 1

            escrow1 = EscrowTransaction(
                booking_id=booking1.id,
                guest_id=seeker_rohit.id,
                host_id=space1.host_id,
                held_amount=total,
                currency="INR",
                status="HELD",
                release_scheduled_at=end_time + timedelta(hours=24),
            )
            db.session.add(escrow1)

            review1 = Review(
                space_id=space1.id,
                guest_id=seeker_rohit.id,
                rating=5,
                comment="Incredible workspace! Super fast wifi and very quiet environment in Indiranagar.",
                is_verified_stay=True,
                host_response="Thank you Rohit! Looking forward to hosting you again.",
            )
            db.session.add(review1)
            counts["reviews"] += 1

            notif1 = Notification(
                user_id=seeker_rohit.id,
                title="Booking Confirmed!",
                body="Your booking at Indiranagar Tech Loft is confirmed. Check-in code: SPACE99.",
                notification_type="BOOKING",
                is_read=False,
            )
            db.session.add(notif1)

        db.session.commit()
        logger.info(f"Database successfully seeded: {counts}")
        return counts
    except SQLAlchemyError as err:
        db.session.rollback()
        logger.error(f"Failed to seed database: {err}", exc_info=True)
        raise


if __name__ == "__main__":
    # Allow executing directly: python backend/seed_data.py
    backend_dir = Path(__file__).resolve().parent
    repo_root = backend_dir.parent
    for p in (str(backend_dir), str(repo_root)):
        if p not in sys.path:
            sys.path.insert(0, p)

    from backend.app.bootstrap.application import create_app
    cli_app = create_app()
    with cli_app.app_context():
        print("Synchronizing demo accounts...")
        result = ensure_demo_accounts(cli_app)
        print("Demo accounts synchronization status:", result)
        print("Checking catalog seed...")
        seed_res = seed_all(cli_app)
        print("Seed summary:", seed_res)
