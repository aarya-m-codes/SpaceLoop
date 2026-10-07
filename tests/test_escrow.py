"""Test suite for SpaceLoop Financial Escrow Subsystem."""

import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from backend.core.database import db
from backend.modules.escrow.service import EscrowService
from config import TestingConfig
from models import Booking, EscrowTransaction, FraudEventRecord, Space, User, utc_now
from security import hash_password


class EscrowTestCase(unittest.TestCase):
    """Test suite verifying fund holding, release scheduling, dispute freezing, and admin resolution."""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Users: Host, Guest, Admin, Stranger
        self.host = User(
            email="host.anand@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Anand Host",
            role="HOST",
            is_active=True,
            is_verified=True,
        )
        self.guest = User(
            email="guest.neha@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Neha Guest",
            role="GUEST",
            is_active=True,
            is_verified=True,
        )
        self.admin = User(
            email="admin.escrow@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Admin Escrow",
            role="ADMIN",
            is_active=True,
            is_verified=True,
        )
        self.stranger = User(
            email="stranger@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Stranger User",
            role="GUEST",
            is_active=True,
            is_verified=True,
        )
        db.session.add_all([self.host, self.guest, self.admin, self.stranger])
        db.session.commit()

        # Space listing
        self.space = Space(
            host_id=self.host.id,
            title="Connaught Place Executive Office",
            description="Prestigious office in Central Delhi.",
            space_type="room",
            address_line1="Outer Circle, CP",
            city="New Delhi",
            state="Delhi",
            pincode="110001",
            latitude=28.6315,
            longitude=77.2167,
            price_per_hour=300.0,
            minimum_hours=1,
            capacity=4,
            is_active=True,
            is_approved=True,
        )
        db.session.add(self.space)
        db.session.commit()

        # Auth headers
        self.host_headers = {"X-User-Id": str(self.host.id)}
        self.guest_headers = {"X-User-Id": str(self.guest.id)}
        self.admin_headers = {"X-User-Id": str(self.admin.id)}
        self.stranger_headers = {"X-User-Id": str(self.stranger.id)}

        # Create base booking
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=3)
        self.booking = Booking(
            space_id=self.space.id,
            guest_id=self.guest.id,
            start_time=start,
            end_time=end,
            total_hours=3.0,
            base_amount=900.0,
            platform_fee=90.0,
            taxes_gst=16.2,
            total_amount=1006.2,
            currency="INR",
            status="CONFIRMED",
            access_code="SECURE88",
        )
        db.session.add(self.booking)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =========================================================================
    # 1. Hold Funds & Details
    # =========================================================================

    def test_hold_funds_and_get_details(self):
        """Verify escrow creation on booking confirmation and access control."""
        escrow = EscrowService.hold_funds(self.booking)
        self.assertEqual(escrow.status, "HELD")
        self.assertEqual(escrow.held_amount, 1006.2)
        self.assertIsNotNone(escrow.release_scheduled_at)

        # Guest can view
        res_guest = self.client.get(f"/api/v1/escrow/{self.booking.id}", headers=self.guest_headers)
        self.assertEqual(res_guest.status_code, 200)
        self.assertEqual(res_guest.get_json()["data"]["held_amount"], 1006.2)

        # Host can view
        res_host = self.client.get(f"/api/v1/escrow/{self.booking.id}", headers=self.host_headers)
        self.assertEqual(res_host.status_code, 200)

        # Stranger is unauthorized
        res_stranger = self.client.get(f"/api/v1/escrow/{self.booking.id}", headers=self.stranger_headers)
        self.assertEqual(res_stranger.status_code, 403)

    # =========================================================================
    # 2. Release & Schedule Transitions
    # =========================================================================

    def test_schedule_and_release_to_host(self):
        """Verify HELD -> RELEASE_SCHEDULED -> RELEASED transitions."""
        EscrowService.hold_funds(self.booking)

        # 1. Schedule release
        sched_res = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/schedule-release",
            headers=self.guest_headers,
        )
        self.assertEqual(sched_res.status_code, 200)
        self.assertEqual(sched_res.get_json()["data"]["status"], "RELEASE_SCHEDULED")

        # 2. Guest early approval release to host
        release_res = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/release",
            headers=self.guest_headers,
        )
        self.assertEqual(release_res.status_code, 200)
        data = release_res.get_json()["data"]
        self.assertEqual(data["status"], "RELEASED")
        self.assertIsNotNone(data["released_at"])

        # Booking should transition to COMPLETED
        db.session.refresh(self.booking)
        self.assertEqual(self.booking.status, "COMPLETED")

    def test_refund_to_guest(self):
        """Verify refund transitions escrow to REFUNDED and booking to CANCELLED."""
        EscrowService.hold_funds(self.booking)

        refund_res = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/refund",
            headers=self.guest_headers,
            json={"reason": "Guest emergency cancellation"},
        )
        self.assertEqual(refund_res.status_code, 200)
        data = refund_res.get_json()["data"]
        self.assertEqual(data["status"], "REFUNDED")
        self.assertIsNotNone(data["refunded_at"])

        # Booking should transition to CANCELLED
        db.session.refresh(self.booking)
        self.assertEqual(self.booking.status, "CANCELLED")

    # =========================================================================
    # 3. Dispute Freezing & Safety
    # =========================================================================

    def test_freeze_dispute_and_block_transfers(self):
        """Verify dispute filing locks funds into FROZEN status and blocks standard releases."""
        EscrowService.hold_funds(self.booking)

        # File dispute
        dispute_res = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/dispute",
            headers=self.guest_headers,
            json={"reason": "Space was locked and host did not answer call."},
        )
        self.assertEqual(dispute_res.status_code, 200)
        data = dispute_res.get_json()["data"]
        self.assertEqual(data["status"], "FROZEN")
        self.assertIn("locked", data["dispute_reason"])

        # Booking marked DISPUTED
        db.session.refresh(self.booking)
        self.assertEqual(self.booking.status, "DISPUTED")

        # Fraud event telemetry record created
        fraud_event = FraudEventRecord.query.filter_by(event_type="ESCROW_DISPUTE_FILED").first()
        self.assertIsNotNone(fraud_event)

        # Standard release MUST be rejected while frozen
        rel_attempt = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/release",
            headers=self.host_headers,
        )
        self.assertEqual(rel_attempt.status_code, 409)

        # Standard refund MUST be rejected while frozen
        ref_attempt = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/refund",
            headers=self.guest_headers,
        )
        self.assertEqual(ref_attempt.status_code, 409)

    # =========================================================================
    # 4. Admin Dispute Adjudication
    # =========================================================================

    def test_admin_dispute_resolution(self):
        """Verify admin adjudication with REFUND_TO_GUEST and RELEASE_TO_HOST."""
        EscrowService.hold_funds(self.booking)
        EscrowService.freeze_dispute(self.booking.id, self.guest, "AC was broken during entire stay.")

        # Non-admin cannot resolve
        unauth_res = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/resolve-dispute",
            headers=self.host_headers,
            json={"resolution": "RELEASE_TO_HOST"},
        )
        self.assertEqual(unauth_res.status_code, 403)

        # Admin resolves with REFUND_TO_GUEST
        resolve_res = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/resolve-dispute",
            headers=self.admin_headers,
            json={
                "resolution": "REFUND_TO_GUEST",
                "notes": "Verified host failed to provide listed AC amenity.",
            },
        )
        self.assertEqual(resolve_res.status_code, 200)
        data = resolve_res.get_json()["data"]
        self.assertEqual(data["status"], "REFUNDED")
        self.assertIsNotNone(data["refunded_at"])

    # =========================================================================
    # 5. Automated Release Processing (Cron / Background Worker)
    # =========================================================================

    def test_process_scheduled_releases_cron(self):
        """Verify background batch worker auto-releases eligible matured escrows."""
        escrow = EscrowService.hold_funds(self.booking)
        escrow.status = "RELEASE_SCHEDULED"
        # Simulate scheduled time in the past
        escrow.release_scheduled_at = utc_now() - timedelta(minutes=5)
        db.session.commit()

        # Trigger process-releases endpoint
        res = self.client.post("/api/v1/escrow/process-releases")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["data"]["processed_count"], 1)

        db.session.refresh(escrow)
        self.assertEqual(escrow.status, "RELEASED")
        self.assertIsNotNone(escrow.released_at)

    # =========================================================================
    # 6. Admin Summary Metrics
    # =========================================================================

    def test_admin_escrow_summary_metrics(self):
        """Verify platform financial summary endpoint for administrative metrics."""
        EscrowService.hold_funds(self.booking)

        # Admin view
        res = self.client.get("/api/v1/escrow/summary", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("total_held", data)
        self.assertIn("total_released", data)
        self.assertIn("total_refunded", data)
        self.assertIn("total_frozen", data)
        self.assertIn("active_disputes_count", data)
        self.assertGreaterEqual(data["total_held"], 1006.2)

        # Non-admin view forbidden
        res_guest = self.client.get("/api/v1/escrow/summary", headers=self.guest_headers)
        self.assertEqual(res_guest.status_code, 403)


if __name__ == "__main__":
    unittest.main()
