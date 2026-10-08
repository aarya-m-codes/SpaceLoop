"""Test suite for SpaceLoop Ported Features: Calculator, OTI Trust, System Telemetry, Micro-Lease & Inquiries."""

import unittest
import uuid
from datetime import datetime, timedelta, timezone

from app import create_app
from backend.core.database import db
from config import TestingConfig
from models import Booking, Space, User, utc_now
from security import hash_password


class CalculatorAndSessionFeaturesTestCase(unittest.TestCase):
    """Verifies the new endpoints added from the LogicLoop platform comparison."""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.session.rollback()
        db.drop_all()
        db.create_all()

        uid = uuid.uuid4().hex[:8]
        # Create Host and Seeker with unique emails
        self.host = User(
            email=f"host.{uid}@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Kanishk Host",
            role="HOST",
            is_active=True,
            is_verified=True,
        )
        self.seeker = User(
            email=f"seeker.{uid}@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Aarya Seeker",
            role="GUEST",
            is_active=True,
            is_verified=True,
        )
        db.session.add_all([self.host, self.seeker])
        db.session.commit()

        # Create Space listing
        self.space = Space(
            host_id=self.host.id,
            title="Koramangala Creator Pod",
            description="Quiet acoustic podcast and study studio.",
            space_type="Studio",
            address_line1="5th Block, Koramangala",
            city="Bengaluru",
            state="Karnataka",
            pincode="560034",
            latitude=12.9352,
            longitude=77.6245,
            price_per_hour=120.0,
            minimum_hours=1,
            capacity=4,
            amenities=["wifi", "power_backup", "ac"],
            is_active=True,
            is_approved=True,
        )
        db.session.add(self.space)
        db.session.commit()

        # Create Booking
        start = utc_now() + timedelta(hours=1)
        end = start + timedelta(hours=3)
        self.booking = Booking(
            guest_id=self.seeker.id,
            space_id=self.space.id,
            start_time=start,
            end_time=end,
            total_hours=2.0,
            base_amount=240.0,
            platform_fee=12.0,
            taxes_gst=0.0,
            total_amount=352.0,
            escrow_deposit=100.0,
            status="confirmed",
            arrival_pin="9482",
            access_code="QR-LL-9482",
        )
        db.session.add(self.booking)
        db.session.commit()

        self.seeker_headers = {"X-User-Id": str(self.seeker.id)}
        self.host_headers = {"X-User-Id": str(self.host.id)}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =========================================================================
    # 1. Calculator Tests
    # =========================================================================

    def test_calculator_categories(self):
        """GET /api/v1/calculator/categories returns valid category list."""
        res = self.client.get("/api/v1/calculator/categories")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("categories", data)
        self.assertGreaterEqual(len(data["categories"]), 5)

    def test_calculator_estimate(self):
        """POST /api/v1/calculator/estimate calculates passive revenue projections."""
        payload = {
            "space_type": "Studio",
            "square_feet": 200,
            "city": "Bengaluru",
            "hours_per_day": 8,
            "days_per_week": 5,
        }
        res = self.client.post("/api/v1/calculator/estimate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("estimated_monthly_inr", data)
        self.assertGreater(data["estimated_monthly_inr"], 0)
        self.assertIn("estimated_hourly_inr", data)
        self.assertIn("occupancy_rate_pct", data)

    # =========================================================================
    # 2. System Status & Connectivity Tests
    # =========================================================================

    def test_system_status(self):
        """GET /api/v1/system/status returns service status."""
        res = self.client.get("/api/v1/system/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "operational")
        self.assertIn("version", data)

    def test_system_connectivity(self):
        """GET /api/v1/system/connectivity checks multi-rail connection status."""
        res = self.client.get("/api/v1/system/connectivity")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("connectivity", data)

    def test_system_toggle_ai_simulation(self):
        """POST /api/v1/system/dev/toggle-ai-simulation toggles simulation state."""
        res = self.client.post(
            "/api/v1/system/dev/toggle-ai-simulation",
            json={"enabled": True},
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ai_simulation_enabled"))

    # =========================================================================
    # 3. OTI Trust & Safety Tests
    # =========================================================================

    def test_trust_stats(self):
        """GET /api/v1/trust/stats returns aggregated metrics."""
        res = self.client.get("/api/v1/trust/stats")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("stats", data)

    def test_simulate_oti(self):
        """POST /api/v1/trust/simulate-oti computes 4-pillar trust formula."""
        payload = {
            "punctuality": 95,
            "condition": 90,
            "verification": 100,
            "settlement": 100,
        }
        res = self.client.post("/api/v1/trust/simulate-oti", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("score", data)
        self.assertGreaterEqual(data["score"], 90)
        self.assertIn("tier", data)

    def test_oti_breakdown(self):
        """GET /api/v1/trust/oti-breakdown retrieves user trust profile."""
        res = self.client.get(
            f"/api/v1/trust/oti-breakdown?entity_type=user&entity_id={self.seeker.id}"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("oti_score", data)
        self.assertIn("components", data)

    # =========================================================================
    # 4. Session & Micro-Lease Tests
    # =========================================================================

    def test_booking_micro_lease(self):
        """GET /api/v1/bookings/<id>/micro-lease returns Section 52 agreement."""
        res = self.client.get(
            f"/api/v1/bookings/{self.booking.id}/micro-lease",
            headers=self.seeker_headers,
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("agreement_markdown", data)
        self.assertIn("Section 52", data["agreement_markdown"])

    def test_booking_status(self):
        """GET /api/v1/bookings/<id>/status returns live session state."""
        res = self.client.get(
            f"/api/v1/bookings/{self.booking.id}/status",
            headers=self.seeker_headers,
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "confirmed")
        self.assertEqual(data.get("arrival_pin"), "9482")

    def test_inspect_condition(self):
        """POST /api/v1/bookings/<id>/inspect-condition performs CV condition delta."""
        payload = {
            "checkout_photo_url": "https://example.com/checkout.jpg",
            "notes": "Everything clean, lights switched off",
        }
        res = self.client.post(
            f"/api/v1/bookings/{self.booking.id}/inspect-condition",
            json=payload,
            headers=self.seeker_headers,
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("condition_match_pct", data)

    # =========================================================================
    # 5. Space QR Pass & Inquiries
    # =========================================================================

    def test_space_qr_pass(self):
        """GET /api/v1/spaces/<id>/qr-pass returns pass tokens."""
        res = self.client.get(f"/api/v1/spaces/{self.space.id}/qr-pass")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("qr_token", data)

    def test_space_inquiries_flow(self):
        """Submit inquiry, fetch inquiries, and host reply."""
        # Seeker sends inquiry
        inquiry_res = self.client.post(
            f"/api/v1/spaces/{self.space.id}/inquiries",
            json={"message": "Is high-speed Wi-Fi available on weekends?"},
            headers=self.seeker_headers,
        )
        self.assertEqual(inquiry_res.status_code, 201)
        inquiry_data = inquiry_res.get_json()
        inquiry_id = inquiry_data["inquiry"]["id"]

        # Get inquiries
        list_res = self.client.get(
            f"/api/v1/spaces/{self.space.id}/inquiries",
            headers=self.host_headers,
        )
        self.assertEqual(list_res.status_code, 200)
        list_data = list_res.get_json()
        self.assertGreaterEqual(len(list_data["inquiries"]), 1)

        # Host replies
        reply_res = self.client.post(
            f"/api/v1/spaces/inquiries/{inquiry_id}/reply",
            json={"reply": "Yes, 300 Mbps fiber backup is on 24/7!"},
            headers=self.host_headers,
        )
        self.assertEqual(reply_res.status_code, 200)
        reply_data = reply_res.get_json()
        self.assertEqual(reply_data["inquiry"]["reply"], "Yes, 300 Mbps fiber backup is on 24/7!")


if __name__ == "__main__":
    unittest.main()
