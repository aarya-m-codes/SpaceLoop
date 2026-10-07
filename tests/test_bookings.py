"""Test suite for SpaceLoop Booking Engine, Precheck, Concurrency Control, and State Transitions."""

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
    """Test suite verifying slot reservation, precheck, double booking prevention, and lifecycle state machines."""

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

        # Auth headers
        self.guest1_headers = {"X-User-Id": str(self.guest1.id)}
        self.guest2_headers = {"X-User-Id": str(self.guest2.id)}
        self.host_headers = {"X-User-Id": str(self.host.id)}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =========================================================================
    # 1. Pricing Engine & Precheck Unit Tests
    # =========================================================================

    def test_pricing_calculation(self):
        """Verify subtotal, 10% platform fee, ₹100 deposit, and total sum."""
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        pricing = PricingEngine.calculate_precheck(
            price_per_hour=500.0,
            start_time=start,
            end_time=end,
        )

        self.assertEqual(pricing["duration_hours"], 4.0)
        self.assertEqual(pricing["subtotal"], 2000.0)         # 500 * 4
        self.assertEqual(pricing["platform_fee"], 200.0)      # 10% of 2000
        self.assertEqual(pricing["escrow_deposit"], 100.0)    # ₹100 statutory deposit
        self.assertEqual(pricing["final_amount"], 2300.0)     # 2000 + 200 + 100

    def test_precheck_endpoint_success(self):
        """Verify POST /api/bookings/precheck returns calculated amounts and availability."""
        start = utc_now() + timedelta(days=2)
        end = start + timedelta(hours=3)

        res = self.client.post(
            "/api/bookings/precheck",
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "guest_count": 2,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertTrue(data["is_available"])
        self.assertEqual(data["duration_hours"], 3.0)
        self.assertEqual(data["subtotal"], 1500.0)
        self.assertEqual(data["platform_fee"], 150.0)
        self.assertEqual(data["escrow_deposit"], 100.0)
        self.assertEqual(data["final_amount"], 1750.0)  # 1500 + 150 + 100

    def test_precheck_validations(self):
        """Verify precheck handles non-existent space, inactive space, past dates, min hours, and slot conflicts."""
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=3)

        # 1. Non-existent space
        res_404 = self.client.post(
            "/api/bookings/precheck",
            json={"space_id": 99999, "start_time": start.isoformat(), "end_time": end.isoformat()},
        )
        self.assertEqual(res_404.status_code, 404)

        # 2. Inactive space
        self.space.is_active = False
        db.session.commit()
        res_inactive = self.client.post(
            "/api/bookings/precheck",
            json={"space_id": self.space.id, "start_time": start.isoformat(), "end_time": end.isoformat()},
        )
        self.assertEqual(res_inactive.status_code, 400)
        self.space.is_active = True
        db.session.commit()

        # 3. Past start time
        past_start = utc_now() - timedelta(hours=2)
        res_past = self.client.post(
            "/api/bookings/precheck",
            json={"space_id": self.space.id, "start_time": past_start.isoformat(), "end_time": end.isoformat()},
        )
        self.assertEqual(res_past.status_code, 400)

        # 4. End before start
        res_inv = self.client.post(
            "/api/bookings/precheck",
            json={"space_id": self.space.id, "start_time": end.isoformat(), "end_time": start.isoformat()},
        )
        self.assertEqual(res_inv.status_code, 400)

        # 5. Below minimum hours
        short_end = start + timedelta(hours=1)
        res_short = self.client.post(
            "/api/bookings/precheck",
            json={"space_id": self.space.id, "start_time": start.isoformat(), "end_time": short_end.isoformat()},
        )
        self.assertEqual(res_short.status_code, 400)

    # =========================================================================
    # 2. Reservation Creation & Transactional Integrity
    # =========================================================================

    def test_create_booking_success(self):
        """Verify successful transactional booking creation, 4-digit PIN, deposit, and initial states."""
        start = (utc_now() + timedelta(days=2)).replace(microsecond=0)
        end = start + timedelta(hours=3)

        res = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "guest_count": 2,
            },
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["data"]
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["session_state"], "not_started")
        self.assertEqual(data["escrow_status"], "held")
        self.assertEqual(data["duration_hours"], 3.0)
        self.assertEqual(data["subtotal"], 1500.0)
        self.assertEqual(data["platform_fee"], 150.0)
        self.assertEqual(data["escrow_deposit"], 100.0)
        self.assertEqual(data["total_price"], 1750.0)

        # 4-digit arrival PIN verification
        self.assertIsNotNone(data["arrival_pin"])
        self.assertEqual(len(data["arrival_pin"]), 4)
        self.assertTrue(data["arrival_pin"].isdigit())

        # Internal escrow ledger transaction check
        escrow = EscrowTransaction.query.filter_by(booking_id=data["id"]).first()
        self.assertIsNotNone(escrow)
        self.assertEqual(escrow.status, "HELD")
        self.assertEqual(escrow.held_amount, 1750.0)

    def test_self_booking_prevention(self):
        """Verify hosts cannot book their own physical space listings."""
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=2)

        res = self.client.post(
            "/api/bookings",
            headers=self.host_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("own physical space", res.get_json()["error"]["message"])

    # =========================================================================
    # 3. Overlap Detection & Simultaneous Booking Defense
    # =========================================================================

    def test_overlapping_bookings(self):
        """Verify overlapping reservation attempts are rejected with 409 Conflict across multiple overlap shapes."""
        start = utc_now() + timedelta(days=3)
        end = start + timedelta(hours=4)

        # First reservation by Guest 1 succeeds
        res1 = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res1.status_code, 201)

        # Overlap Shape A: starts inside existing slot
        res_overlap_a = self.client.post(
            "/api/bookings",
            headers=self.guest2_headers,
            json={
                "space_id": self.space.id,
                "start_time": (start + timedelta(hours=1)).isoformat(),
                "end_time": (start + timedelta(hours=3)).isoformat(),
            },
        )
        self.assertEqual(res_overlap_a.status_code, 409)

        # Overlap Shape B: engulfs existing slot completely
        res_overlap_b = self.client.post(
            "/api/bookings",
            headers=self.guest2_headers,
            json={
                "space_id": self.space.id,
                "start_time": (start - timedelta(hours=1)).isoformat(),
                "end_time": (end + timedelta(hours=1)).isoformat(),
            },
        )
        self.assertEqual(res_overlap_b.status_code, 409)

        # Precheck also detects the conflict
        res_precheck = self.client.post(
            "/api/bookings/precheck",
            json={
                "space_id": self.space.id,
                "start_time": (start + timedelta(hours=2)).isoformat(),
                "end_time": (end + timedelta(hours=1)).isoformat(),
            },
        )
        self.assertEqual(res_precheck.status_code, 409)

    def test_simultaneous_bookings(self):
        """Verify exact simultaneous slot attempt is rejected with 409 Conflict."""
        start = utc_now() + timedelta(days=4)
        end = start + timedelta(hours=2)

        res1 = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post(
            "/api/bookings",
            headers=self.guest2_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res2.status_code, 409)

    # =========================================================================
    # 4. Host Acceptance & Host Rejection
    # =========================================================================

    def test_host_acceptance_flow(self):
        """Verify host can accept pending booking, while unauthorized users are rejected."""
        start = utc_now() + timedelta(days=2)
        end = start + timedelta(hours=3)

        create_res = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_id = create_res.get_json()["data"]["id"]

        # 1. Renter (guest) cannot accept booking
        unauth_accept = self.client.post(
            f"/api/booking/{booking_id}/accept",
            headers=self.guest1_headers,
        )
        self.assertEqual(unauth_accept.status_code, 403)

        # 2. Host accepts successfully -> confirmed
        host_accept = self.client.post(
            f"/api/booking/{booking_id}/accept",
            headers=self.host_headers,
        )
        self.assertEqual(host_accept.status_code, 200)
        self.assertEqual(host_accept.get_json()["data"]["status"], "confirmed")

    def test_host_rejection_flow(self):
        """Verify host can reject pending booking, refunding escrow and releasing slot."""
        start = utc_now() + timedelta(days=5)
        end = start + timedelta(hours=2)

        create_res = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_id = create_res.get_json()["data"]["id"]

        # 1. Host rejects booking
        reject_res = self.client.post(
            f"/api/booking/{booking_id}/reject",
            headers=self.host_headers,
            json={"reason": "Space unavailable due to maintenance."},
        )
        self.assertEqual(reject_res.status_code, 200)
        data = reject_res.get_json()["data"]
        self.assertEqual(data["status"], "rejected")
        self.assertEqual(data["escrow_status"], "refunded")

        # Escrow ledger record is marked REFUNDED
        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        self.assertEqual(escrow.status, "REFUNDED")

        # 2. Slot is now free for Guest 2
        new_res = self.client.post(
            "/api/bookings",
            headers=self.guest2_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(new_res.status_code, 201)

    # =========================================================================
    # 5. Cancellation & Slot Release
    # =========================================================================

    def test_cancellation_flow(self):
        """Verify cancellation updates status, refunds escrow, and releases slot."""
        start = utc_now() + timedelta(days=6)
        end = start + timedelta(hours=3)

        create_res = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_id = create_res.get_json()["data"]["id"]

        # Cancel by renter
        cancel_res = self.client.post(
            f"/api/booking/{booking_id}/cancel",
            headers=self.guest1_headers,
            json={"reason": "Travel plans changed."},
        )
        self.assertEqual(cancel_res.status_code, 200)
        data = cancel_res.get_json()["data"]
        self.assertEqual(data["status"], "cancelled")
        self.assertEqual(data["session_state"], "cancelled")
        self.assertEqual(data["escrow_status"], "refunded")

    # =========================================================================
    # 6. Dispute Creation & Escrow Freeze
    # =========================================================================

    def test_dispute_creation_and_freeze(self):
        """Verify dispute locks funds into disputed/frozen state and prevents double dispute."""
        start = utc_now() + timedelta(days=7)
        end = start + timedelta(hours=3)

        create_res = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_id = create_res.get_json()["data"]["id"]
        self.client.post(f"/api/booking/{booking_id}/accept", headers=self.host_headers)

        # File dispute
        dispute_res = self.client.post(
            f"/api/booking/{booking_id}/dispute",
            headers=self.guest1_headers,
            json={"reason": "Door PIN did not work and host was unreachable."},
        )
        self.assertEqual(dispute_res.status_code, 200)
        data = dispute_res.get_json()["data"]
        self.assertEqual(data["escrow_status"], "disputed")

        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        self.assertEqual(escrow.status, "FROZEN")

        # Duplicate dispute attempt is rejected
        dup_dispute = self.client.post(
            f"/api/booking/{booking_id}/dispute",
            headers=self.guest1_headers,
            json={"reason": "Another dispute."},
        )
        self.assertEqual(dup_dispute.status_code, 400)

    # =========================================================================
    # 7. Invalid State Transitions
    # =========================================================================

    def test_invalid_state_transitions(self):
        """Verify arbitrary or invalid state transitions are strictly rejected."""
        start = utc_now() + timedelta(days=8)
        end = start + timedelta(hours=2)

        create_res = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_id = create_res.get_json()["data"]["id"]

        # 1. Cannot check in to pending booking (must be confirmed)
        bad_checkin = self.client.post(
            f"/api/booking/{booking_id}/check-in",
            headers=self.guest1_headers,
        )
        self.assertEqual(bad_checkin.status_code, 400)

        # 2. Cancel the booking
        self.client.post(f"/api/booking/{booking_id}/cancel", headers=self.guest1_headers)

        # 3. Cannot accept already cancelled booking
        bad_accept = self.client.post(
            f"/api/booking/{booking_id}/accept",
            headers=self.host_headers,
        )
        self.assertEqual(bad_accept.status_code, 400)

        # 4. Cannot reject already cancelled booking
        bad_reject = self.client.post(
            f"/api/booking/{booking_id}/reject",
            headers=self.host_headers,
        )
        self.assertEqual(bad_reject.status_code, 400)

        # 5. Cannot dispute already cancelled booking
        bad_dispute = self.client.post(
            f"/api/booking/{booking_id}/dispute",
            headers=self.guest1_headers,
        )
        self.assertEqual(bad_dispute.status_code, 400)

    # =========================================================================
    # 8. Check-in with PIN/GPS, Complete, and Authorization Isolation
    # =========================================================================

    def test_check_in_and_complete_lifecycle(self):
        """Verify full lifecycle: pending -> confirmed -> active (check-in) -> completed."""
        start = utc_now() + timedelta(days=9)
        end = start + timedelta(hours=3)

        create_res = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_data = create_res.get_json()["data"]
        booking_id = booking_data["id"]
        pin = booking_data["arrival_pin"]

        # Accept by host
        self.client.post(f"/api/booking/{booking_id}/accept", headers=self.host_headers)

        # Check-in with arrival PIN, GPS, and inspection photos
        checkin_res = self.client.post(
            f"/api/booking/{booking_id}/check-in",
            headers=self.guest1_headers,
            json={
                "arrival_pin": pin,
                "latitude": 12.9785,
                "longitude": 77.6409,
                "inspection_photos": ["https://spaceloop.in/img/checkin1.jpg"],
            },
        )
        self.assertEqual(checkin_res.status_code, 200)
        cdata = checkin_res.get_json()["data"]
        self.assertEqual(cdata["status"], "active")
        self.assertEqual(cdata["session_state"], "checked_in")
        self.assertIsNotNone(cdata["check_in_time"])
        self.assertEqual(cdata["check_in_lat"], 12.9785)
        self.assertEqual(len(cdata["inspection_photos"]), 1)

        # Complete booking
        complete_res = self.client.post(
            f"/api/booking/{booking_id}/complete",
            headers=self.guest1_headers,
            json={"inspection_photos": ["https://spaceloop.in/img/checkout1.jpg"]},
        )
        self.assertEqual(complete_res.status_code, 200)
        comp_data = complete_res.get_json()["data"]
        self.assertEqual(comp_data["status"], "completed")
        self.assertEqual(comp_data["session_state"], "checked_out")
        self.assertIsNotNone(comp_data["check_out_time"])

    def test_booking_authorization_isolation(self):
        """Verify guest & host can view booking, but unrelated users are forbidden."""
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=2)

        create_res = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        booking_id = create_res.get_json()["data"]["id"]

        # Guest 1 can access
        res_g1 = self.client.get(f"/api/booking/{booking_id}", headers=self.guest1_headers)
        self.assertEqual(res_g1.status_code, 200)

        # Host can access
        res_host = self.client.get(f"/api/booking/{booking_id}", headers=self.host_headers)
        self.assertEqual(res_host.status_code, 200)

        # Guest 2 is unauthorized
        res_g2 = self.client.get(f"/api/booking/{booking_id}", headers=self.guest2_headers)
        self.assertEqual(res_g2.status_code, 403)

    def test_booking_field_support_and_route_aliases(self):
        """Verify all spec fields (space, renter, times, duration, guest_count, total_price, platform_fee, escrow_deposit, status, session_state, escrow_status, arrival PIN, timestamps, GPS, inspection photos) and singular/plural routes."""
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=3)

        res = self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "guest_count": 4,
            },
        )
        self.assertEqual(res.status_code, 201)
        b_id = res.get_json()["data"]["id"]

        # Test both singular and plural GET routes
        res_sing = self.client.get(f"/api/booking/{b_id}", headers=self.guest1_headers)
        self.assertEqual(res_sing.status_code, 200)
        data = res_sing.get_json()["data"]

        res_plur = self.client.get(f"/api/bookings/{b_id}", headers=self.guest1_headers)
        self.assertEqual(res_plur.status_code, 200)

        # Check all required fields
        self.assertIn("space", data)
        self.assertIn("renter", data)
        self.assertEqual(data["renter"]["id"], self.guest1.id)
        self.assertIn("start_time", data)
        self.assertIn("end_time", data)
        self.assertEqual(data["duration_hours"], 3.0)
        self.assertEqual(data["guest_count"], 4)
        self.assertEqual(data["total_price"], 1750.0)
        self.assertEqual(data["platform_fee"], 150.0)
        self.assertEqual(data["escrow_deposit"], 100.0)
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["session_state"], "not_started")
        self.assertEqual(data["escrow_status"], "held")
        self.assertIsNotNone(data["arrival_pin"])
        self.assertEqual(len(data["arrival_pin"]), 4)
        self.assertIn("check_in_time", data)
        self.assertIn("check_out_time", data)
        self.assertIn("check_in_lat", data)
        self.assertIn("check_in_lng", data)
        self.assertIn("inspection_photos", data)
        self.assertIsInstance(data["inspection_photos"], list)

    def test_list_my_bookings_and_host_reservations(self):
        """Verify list endpoints /my-bookings and /host-reservations."""
        start = utc_now() + timedelta(days=2)
        end = start + timedelta(hours=3)

        self.client.post(
            "/api/bookings",
            headers=self.guest1_headers,
            json={
                "space_id": self.space.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )

        # Guest view
        my_res = self.client.get("/api/bookings/my-bookings", headers=self.guest1_headers)
        self.assertEqual(my_res.status_code, 200)
        items = my_res.get_json()["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["space"]["title"], self.space.title)

        # Host view
        host_res = self.client.get("/api/bookings/host-reservations", headers=self.host_headers)
        self.assertEqual(host_res.status_code, 200)
        h_items = host_res.get_json()["data"]["items"]
        self.assertEqual(len(h_items), 1)
        self.assertEqual(h_items[0]["renter"]["full_name"], self.guest1.full_name)


if __name__ == "__main__":
    unittest.main()
