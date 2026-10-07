import logging
from datetime import datetime, timedelta, timezone
from flask import Flask
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

from flask import current_app, has_app_context

logger = logging.getLogger("spaceloop.seed")


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

    # Verify if users already exist
    existing_user_count = User.query.count()
    if existing_user_count > 0:
        logger.info(f"Database already populated with {existing_user_count} users. Skipping seed.")
        return counts

    try:
        # 1. Create Seed Users
        admin_user = User(
            email="admin@spaceloop.in",
            password_hash=hash_password("Admin@SpaceLoop2026!"),
            full_name="SpaceLoop Administrator",
            phone="+919876543210",
            role="ADMIN",
            is_active=True,
            is_verified=True,
            kyc_status="VERIFIED",
            kyc_document_type="Aadhaar",
        )
        host_rahul = User(
            email="host.rahul@spaceloop.in",
            password_hash=hash_password("HostRahul#2026"),
            full_name="Rahul Sharma",
            phone="+919811122233",
            role="HOST",
            is_active=True,
            is_verified=True,
            kyc_status="VERIFIED",
            kyc_document_type="PAN",
        )
        host_priya = User(
            email="host.priya@spaceloop.in",
            password_hash=hash_password("HostPriya#2026"),
            full_name="Priya Nair",
            phone="+919822233344",
            role="HOST",
            is_active=True,
            is_verified=True,
            kyc_status="VERIFIED",
            kyc_document_type="Aadhaar",
        )
        guest_arjun = User(
            email="guest.arjun@spaceloop.in",
            password_hash=hash_password("GuestArjun#2026"),
            full_name="Arjun Verma",
            phone="+919833344455",
            role="GUEST",
            is_active=True,
            is_verified=True,
            kyc_status="VERIFIED",
        )
        guest_ananya = User(
            email="guest.ananya@spaceloop.in",
            password_hash=hash_password("GuestAnanya#2026"),
            full_name="Ananya Sen",
            phone="+919844455566",
            role="GUEST",
            is_active=True,
            is_verified=True,
            kyc_status="PENDING",
        )
        seeker_rohit = User(
            email="seeker.rohit@spaceloop.in",
            password_hash=hash_password("SeekerSecret2026!"),
            full_name="Rohit Sharma",
            phone="+919876501234",
            role="GUEST",
            is_active=True,
            is_verified=True,
            kyc_status="VERIFIED",
        )
        host_ananya = User(
            email="host.ananya@spaceloop.in",
            password_hash=hash_password("HostSecret2026!"),
            full_name="Ananya Iyer",
            phone="+919876505678",
            role="HOST",
            is_active=True,
            is_verified=True,
            kyc_status="VERIFIED",
            kyc_document_type="Aadhaar",
        )

        db.session.add_all([admin_user, host_rahul, host_priya, guest_arjun, guest_ananya, seeker_rohit, host_ananya])
        db.session.flush()
        counts["users"] = 7

        # 2. Create Seed Spaces across Indian Tech Hubs
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

        space2 = Space(
            host_id=host_priya.id,
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

        db.session.add_all([space1, space2, space3])
        db.session.flush()
        counts["spaces"] = 3

        # 3. Create Sample Bookings & Escrow Holds
        start_time = utc_now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        base_amt = 150.0 * 4
        fee = base_amt * 0.10
        gst = fee * 0.18
        total = base_amt + fee + gst

        booking1 = Booking(
            space_id=space1.id,
            guest_id=guest_arjun.id,
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
        counts["bookings"] = 1

        escrow1 = EscrowTransaction(
            booking_id=booking1.id,
            guest_id=guest_arjun.id,
            host_id=host_rahul.id,
            held_amount=total,
            currency="INR",
            status="HELD",
            release_scheduled_at=end_time + timedelta(hours=24),
        )
        db.session.add(escrow1)

        # 4. Create Sample Review
        review1 = Review(
            space_id=space1.id,
            guest_id=guest_arjun.id,
            rating=5,
            comment="Incredible workspace! Super fast wifi and very quiet environment in Indiranagar.",
            is_verified_stay=True,
            host_response="Thank you Arjun! Looking forward to hosting you again.",
        )
        db.session.add(review1)
        counts["reviews"] = 1

        # 5. Create Sample Notification
        notif1 = Notification(
            user_id=guest_arjun.id,
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
