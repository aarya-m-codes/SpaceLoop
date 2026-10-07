"""Test suite for SpaceLoop Booking Engine, Concurrency Control, and State Transitions."""

import os
import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from backend.core.database import db
from backend.modules.bookings.concurrency import ConcurrencyManager
from backend.modules.bookings.pricing import PricingEngine
from backend.modules.bookings.service import BookingService
from config import TestingConfig
from models import Booking, EscrowTransaction, Space, User, utc_now
from security import hash_password


class BookingsTestCase(unittest.TestCase):
    """Test suite verifying slot reservation, double booking prevention, and lifecycle state machines."""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create Host, Guest 1, and Guest 2
        self.host = User(
            email="host.vikram@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Vikram Host",
            role="HOST",
            is_active=True,
            is_verified=True,
        )
        self.guest1 = User(
            email="guest.rohit@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Rohit Guest",
            role="GUEST",
            is_active=True,
            is_verified=True,
        )
        self.guest2 = User(
            email="guest.sneha@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Sneha Guest",
            role="GUEST",
            is_active=True,
            is_verified=True,
        )
        db.session.add_all([self.host, self.guest1, self.guest2])
        db.session.commit()

        # Create Space listing
        self.space = Space(
            host_id=self.host.id,
            title="Indiranagar Tech Loft Studio",
            description="Prime private studio with acoustic soundproofing in Indiranagar.",
            space_type="studio",
            address_line1="12th Main Road, Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            pincode="560038",
            latitude=12.9784,
            longitude=77.6408,
            price_per_hour=500.0,
            minimum_hours=2,
            capacity=6,
            amenities=["wifi", "quiet", "ac"],
            is_active=True,
            is_approved=True,
        )
        db.session.add(self.space)
        db.session.commit()

        # Login tokens
        self.guest1_headers = {"X-User-Id": str(self.guest1.id)}
        self.guest2_headers = {"X-User-Id": str(self.guest2.id)}
        self.host_headers = {"X-User-Id": str(self.host.id)}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =========================================================================
    # 1. Pricing Engine Unit Tests
    # =========================================================================

    def test_pricing_calculation(self):
        """Verify 10% platform fee, 18% GST on platform fee, and total sum."""
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        pricing = PricingEngine.calculate_pricing(
            price_per_hour=500.0,
            start_time=start,
            end_time=end,
        )

        self.assertEqual(pricing["total_hours"], 4.0)
        self.assertEqual(pricing["base_amount"], 2000.0)      # 500 * 4
        self.assertEqual(pricing["platform_fee"], 200.0)      # 10% of 2000
        self.assertEqual(pricing["taxes_gst"], 36.0)          # 18% of 200
        self.assertEqual(pricing["total_amount"], 2236.0)     # 2000 + 200 + 36

    # =========================================================================
    # 2. Reservation Creation & Validation
    # =========================================================================

    def test_create_booking_success(self):
        """Verify successful slot hold creation, access code generation, and pricing."""
        start = (utc_now() + timedelta(days=2)).replace(microsecond=0)
        end = start + timedelta(hours=3)

        res = self.client.post(
            "/api/v1/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["data"]
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["total_hours"], 3.0)
        self.assertEqual(data["base_amount"], 1500.0)
        self.assertEqual(data["total_amount"], 1677.0)  # 1500 + 150 + 27
        self.assertIsNotNone(data["access_code"])
        self.assertEqual(len(data["access_code"]), 6)

    def test_self_booking_prevention(self):
        """Verify hosts cannot book their own physical space listings."""
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=2)

        res = self.client.post(
            "/api/v1/bookings",
            headers=self.host_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("own physical space", res.get_json()["error"]["message"])

    def test_minimum_hours_validation(self):
        """Verify duration below space minimum_hours is rejected."""
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=1)  # Space requires min 2 hours

        res = self.client.post(
            "/api/v1/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("minimum", res.get_json()["error"]["message"])

    def test_past_booking_rejected(self):
        """Verify past start_time is rejected."""
        start = utc_now() - timedelta(hours=2)
        end = utc_now() + timedelta(hours=1)

        res = self.client.post(
            "/api/v1/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("past", res.get_json()["error"]["message"])

    # =========================================================================
    # 3. Concurrency Control & Double Booking Prevention
    # =========================================================================

    def test_double_booking_prevention(self):
        """Verify overlapping reservation attempt is rejected with 409 Conflict."""
        start = utc_now() + timedelta(days=3)
        end = start + timedelta(hours=4)

        # First reservation by Guest 1 succeeds
        res1 = self.client.post(
            "/api/v1/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res1.status_code, 201)

        # Second reservation by Guest 2 for overlapping slot (starts 1h into Guest 1's slot)
        overlap_start = start + timedelta(hours=1)
        overlap_end = overlap_start + timedelta(hours=2)

        res2 = self.client.post(
            "/api/v1/bookings",
            headers=self.guest2_headers,
            json={
                "space_id": self.space.id,
                "start_time": overlap_start.isoformat(),
                "end_time": overlap_end.isoformat(),
            },
        )
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already booked or reserved", res2.get_json()["error"]["message"])

    # =========================================================================
    # 4. Booking Lifecycle & State Transitions
    # =========================================================================

    def test_booking_lifecycle_state_transitions(self):
        """Verify PENDING -> CONFIRMED -> CHECKED_IN -> COMPLETED with Escrow integration."""
        start = utc_now() + timedelta(days=2)
        end = start + timedelta(hours=3)

        # 1. Create booking (PENDING)
        create_res = self.client.post(
            "/api/v1/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_id = create_res.get_json()["data"]["id"]

        # 2. Confirm booking (CONFIRMED) & check Escrow hold
        confirm_res = self.client.post(
            f"/api/v1/bookings/{booking_id}/confirm",
            headers=self.guest1_headers,
        )
        self.assertEqual(confirm_res.status_code, 200)
        self.assertEqual(confirm_res.get_json()["data"]["status"], "CONFIRMED")

        # Escrow transaction must exist and be in HELD status
        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        self.assertIsNotNone(escrow)
        self.assertEqual(escrow.status, "HELD")
        self.assertEqual(escrow.held_amount, confirm_res.get_json()["data"]["total_amount"])

        # 3. Check in (CHECKED_IN)
        checkin_res = self.client.post(
            f"/api/v1/bookings/{booking_id}/check-in",
            headers=self.guest1_headers,
        )
        self.assertEqual(checkin_res.status_code, 200)
        self.assertEqual(checkin_res.get_json()["data"]["status"], "CHECKED_IN")

        # 4. Complete stay (COMPLETED)
        complete_res = self.client.post(
            f"/api/v1/bookings/{booking_id}/complete",
            headers=self.guest1_headers,
        )
        self.assertEqual(complete_res.status_code, 200)
        self.assertEqual(complete_res.get_json()["data"]["status"], "COMPLETED")

    def test_booking_cancellation_and_slot_release(self):
        """Verify cancellation updates status, refunds escrow, and releases slot for new bookings."""
        start = utc_now() + timedelta(days=4)
        end = start + timedelta(hours=2)

        # 1. Create and confirm booking
        create_res = self.client.post(
            "/api/v1/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_id = create_res.get_json()["data"]["id"]
        self.client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=self.guest1_headers)

        # 2. Cancel booking
        cancel_res = self.client.post(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers=self.guest1_headers,
            json={"reason": "Schedule conflict"},
        )
        self.assertEqual(cancel_res.status_code, 200)
        self.assertEqual(cancel_res.get_json()["data"]["status"], "CANCELLED")

        # Escrow must be marked REFUNDED
        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        self.assertEqual(escrow.status, "REFUNDED")

        # 3. Now Guest 2 CAN book the newly released timeframe!
        res_guest2 = self.client.post(
            "/api/v1/bookings",
            headers=self.guest2_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res_guest2.status_code, 201)

    # =========================================================================
    # 5. Access Control & Visibility
    # =========================================================================

    def test_booking_authorization_isolation(self):
        """Verify guest & host can view booking, but unrelated users are forbidden."""
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=2)

        create_res = self.client.post(
            "/api/v1/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_id = create_res.get_json()["data"]["id"]

        # Guest 1 can access
        res_g1 = self.client.get(f"/api/v1/bookings/{booking_id}", headers=self.guest1_headers)
        self.assertEqual(res_g1.status_code, 200)

        # Host can access
        res_host = self.client.get(f"/api/v1/bookings/{booking_id}", headers=self.host_headers)
        self.assertEqual(res_host.status_code, 200)

        # Guest 2 is unauthorized
        res_g2 = self.client.get(f"/api/v1/bookings/{booking_id}", headers=self.guest2_headers)
        self.assertEqual(res_g2.status_code, 403)

    def test_my_bookings_and_host_reservations_lists(self):
        """Verify guest listing on /my-bookings and host view on /host-reservations."""
        start = utc_now() + timedelta(days=2)
        end = start + timedelta(hours=3)

        self.client.post(
            "/api/v1/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )

        # Guest view
        my_res = self.client.get("/api/v1/bookings/my-bookings", headers=self.guest1_headers)
        self.assertEqual(my_res.status_code, 200)
        items = my_res.get_json()["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["space"]["title"], self.space.title)

        # Host view
        host_res = self.client.get("/api/v1/bookings/host-reservations", headers=self.host_headers)
        self.assertEqual(host_res.status_code, 200)
        h_items = host_res.get_json()["data"]["items"]
        self.assertEqual(len(h_items), 1)
        self.assertEqual(h_items[0]["guest"]["full_name"], self.guest1.full_name)


if __name__ == "__main__":
    unittest.main()
