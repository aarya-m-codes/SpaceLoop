"""Test suite for SpaceLoop Financial Micro-Escrow, Deterministic Ledger, and UPI Payment Adapter."""

import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from backend.core.database import db
from backend.modules.bookings.pricing import PricingEngine
from backend.modules.escrow.payment_adapter import MockUPIPaymentAdapter, get_payment_adapter
from backend.modules.escrow.service import EscrowService
from config import TestingConfig
from models import Booking, EscrowTransaction, FraudEventRecord, Space, User, utc_now
from security import hash_password


class EscrowTestCase(unittest.TestCase):
    """Test suite verifying micro-escrow fund holding, deterministic settlements, UPI adapters, and ledger safety."""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.session.remove()
        db.drop_all()
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

        # Space listing: ₹300/hour
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

        # Create base booking: 3 hours @ ₹300/hr = ₹900 subtotal, ₹45 fee (5%), ₹100 deposit, total = ₹1045
        start = utc_now() + timedelta(days=1)
        end = start + timedelta(hours=3)
        self.booking = Booking(
            space_id=self.space.id,
            guest_id=self.guest.id,
            start_time=start,
            end_time=end,
            total_hours=3.0,
            base_amount=900.0,
            platform_fee=45.0,
            escrow_deposit=100.0,
            total_amount=1045.0,
            currency="INR",
            status="confirmed",
            session_state="not_started",
            escrow_status="held",
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
        self.assertEqual(escrow.held_amount, 1045.0)
        self.assertIsNotNone(escrow.release_scheduled_at)

        # Guest can view
        res_guest = self.client.get(f"/api/v1/escrow/{self.booking.id}", headers=self.guest_headers)
        self.assertEqual(res_guest.status_code, 200)
        self.assertEqual(res_guest.get_json()["data"]["held_amount"], 1045.0)

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
        self.assertEqual(self.booking.status.lower(), "completed")

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
        self.assertEqual(self.booking.status.lower(), "cancelled")

    # =========================================================================
    # 3. Micro-Escrow Deterministic Settlement & Multi-Entry Ledger
    # =========================================================================

    def test_normal_checkout_settlement(self):
        """Verify normal checkout executes 3-part ledger settlement:
        1. Host receives Space Subtotal (₹900.00).
        2. SpaceLoop retains 5% platform fee (₹45.00).
        3. Seeker receives ₹100.00 security deposit.
        4. Escrow status becomes released.
        5. Zero discrepancy between deposit hold and outflows.
        """
        EscrowService.hold_funds(self.booking)

        res = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/checkout",
            headers=self.host_headers,
            json={
                "host_vpa": "host.anand@okhdfcbank",
                "seeker_vpa": "guest.neha@okaxis",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]

        self.assertEqual(data["status"], "RELEASED")
        self.assertEqual(data["host_payout"], 900.0)
        self.assertEqual(data["platform_fee"], 45.0)
        self.assertEqual(data["deposit_returned"], 100.0)
        self.assertEqual(data["total_settled"], 1045.0)
        self.assertTrue(data["is_mock"])

        # Verify database ledger entries
        txs = EscrowTransaction.query.filter_by(booking_id=self.booking.id).all()
        # Should have: deposit_hold, release, fee, refund
        tx_types = {tx.transaction_type: tx for tx in txs}
        self.assertIn("deposit_hold", tx_types)
        self.assertIn("release", tx_types)
        self.assertIn("fee", tx_types)
        self.assertIn("refund", tx_types)

        hold_tx = tx_types["deposit_hold"]
        release_tx = tx_types["release"]
        fee_tx = tx_types["fee"]
        refund_tx = tx_types["refund"]

        self.assertEqual(hold_tx.held_amount, 1045.0)
        self.assertEqual(release_tx.amount, 900.0)
        self.assertEqual(fee_tx.amount, 45.0)
        self.assertEqual(refund_tx.amount, 100.0)

        # Invariant: Hold amount == Sum(outflows)
        outflow_sum = round(release_tx.amount + fee_tx.amount + refund_tx.amount, 2)
        self.assertEqual(outflow_sum, hold_tx.held_amount)

        # Verify audit trail ledger endpoint
        ledger_res = self.client.get(f"/api/v1/escrow/{self.booking.id}/ledger", headers=self.guest_headers)
        self.assertEqual(ledger_res.status_code, 200)
        ledger_data = ledger_res.get_json()["data"]
        self.assertEqual(ledger_data["total_held"], 1045.0)
        self.assertEqual(ledger_data["discrepancy"], 0.0)
        self.assertEqual(len(ledger_data["transactions"]), 4)

    def test_cancellation_settlement(self):
        """Verify cancellation formula per specification:
        - SpaceLoop retains ONLY the 5% platform fee (₹45.00).
        - Seeker receives 100% rental (₹900.00) + 100% deposit (₹100.00) = ₹1000.00.
        """
        EscrowService.hold_funds(self.booking)

        res = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/refund",
            headers=self.guest_headers,
            json={"reason": "Guest had a scheduling conflict", "seeker_vpa": "guest.neha@okaxis"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]

        self.assertEqual(data["status"], "REFUNDED")
        self.assertEqual(data["seeker_refund"], 1000.0)
        self.assertEqual(data["platform_fee_retained"], 45.0)
        self.assertTrue(data["is_mock"])

        # Check booking status
        db.session.refresh(self.booking)
        self.assertEqual(self.booking.status.lower(), "cancelled")
        self.assertEqual(self.booking.escrow_status.lower(), "refunded")

        # Check ledger balance
        txs = EscrowTransaction.query.filter_by(booking_id=self.booking.id).all()
        refund_tx = next(t for t in txs if t.transaction_type == "refund")
        fee_tx = next(t for t in txs if t.transaction_type == "fee")

        self.assertEqual(refund_tx.amount, 1000.0)
        self.assertEqual(fee_tx.amount, 45.0)
        self.assertEqual(refund_tx.amount + fee_tx.amount, 1045.0)

    def test_host_rejection_settlement(self):
        """Verify host rejection grants 100% full refund (₹1045.00) including fee and deposit."""
        EscrowService.hold_funds(self.booking)

        res, err, status = EscrowService.host_rejection_settlement(
            booking_id=self.booking.id,
            current_user=self.host,
            reason="Space plumbing maintenance required",
        )
        self.assertEqual(status, 200)
        self.assertIsNone(err)
        self.assertEqual(res["status"], "REFUNDED")
        self.assertEqual(res["full_refund"], 1045.0)

        db.session.refresh(self.booking)
        self.assertEqual(self.booking.status.lower(), "rejected")
        self.assertEqual(self.booking.escrow_status.lower(), "refunded")

        # Escrow primary hold status
        hold = EscrowTransaction.query.filter_by(booking_id=self.booking.id, transaction_type="deposit_hold").first()
        self.assertEqual(hold.status, "REFUNDED")

    # =========================================================================
    # 4. Duplicate Defenses & Concurrency Guards
    # =========================================================================

    def test_duplicate_settlement_prevention(self):
        """Verify duplicate checkout or release attempts are blocked with 409 Conflict."""
        EscrowService.hold_funds(self.booking)

        # First checkout succeeds
        res1 = self.client.post(f"/api/v1/escrow/{self.booking.id}/checkout", headers=self.host_headers)
        self.assertEqual(res1.status_code, 200)

        # Second checkout rejected
        res2 = self.client.post(f"/api/v1/escrow/{self.booking.id}/checkout", headers=self.host_headers)
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already been executed", res2.get_json()["error"]["message"])

        # Release attempt also rejected
        res3 = self.client.post(f"/api/v1/escrow/{self.booking.id}/release", headers=self.host_headers)
        self.assertEqual(res3.status_code, 409)

    def test_duplicate_refund_prevention(self):
        """Verify duplicate refund attempts are blocked with 409 Conflict."""
        EscrowService.hold_funds(self.booking)

        # First refund succeeds
        res1 = self.client.post(f"/api/v1/escrow/{self.booking.id}/refund", headers=self.guest_headers)
        self.assertEqual(res1.status_code, 200)

        # Second refund rejected
        res2 = self.client.post(f"/api/v1/escrow/{self.booking.id}/refund", headers=self.guest_headers)
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already been executed", res2.get_json()["error"]["message"])

    def test_dispute_freeze_blocks_settlement_and_refund(self):
        """Verify dispute locks funds into FROZEN state and blocks both checkout and refund."""
        EscrowService.hold_funds(self.booking)

        # File dispute
        res_disp = self.client.post(
            f"/api/v1/escrow/{self.booking.id}/dispute",
            headers=self.guest_headers,
            json={"reason": "Door PIN did not work and host was unreachable"},
        )
        self.assertEqual(res_disp.status_code, 200)

        # Checkout attempt blocked
        res_checkout = self.client.post(f"/api/v1/escrow/{self.booking.id}/checkout", headers=self.host_headers)
        self.assertEqual(res_checkout.status_code, 409)

        # Release attempt blocked
        res_release = self.client.post(f"/api/v1/escrow/{self.booking.id}/release", headers=self.host_headers)
        self.assertEqual(res_release.status_code, 409)

        # Refund attempt blocked
        res_refund = self.client.post(f"/api/v1/escrow/{self.booking.id}/refund", headers=self.guest_headers)
        self.assertEqual(res_refund.status_code, 409)

    # =========================================================================
    # 5. Exact Math: 5% Platform Fee, ₹100 Deposit, & Rounding
    # =========================================================================

    def test_exact_fee_and_deposit_rounding(self):
        """Verify exact 5% fee calculation, ₹100 statutory deposit, and half-cent rounding."""
        # Case 1: Standard round numbers (₹500/hr * 4 hrs = ₹2000.0)
        p1 = PricingEngine.calculate_precheck(
            price_per_hour=500.0,
            start_time=utc_now(),
            end_time=utc_now() + timedelta(hours=4),
        )
        self.assertEqual(p1["subtotal"], 2000.0)
        self.assertEqual(p1["platform_fee"], 100.0)      # 5% of 2000
        self.assertEqual(p1["escrow_deposit"], 100.0)    # ₹100.00
        self.assertEqual(p1["final_amount"], 2200.0)     # 2000 + 100 + 100

        # Case 2: Fractional subtotal requiring rounding (₹333.33 * 3 hrs = ₹999.99)
        # 5% of 999.99 = 49.9995 -> 50.00
        p2 = PricingEngine.calculate_precheck(
            price_per_hour=333.33,
            start_time=utc_now(),
            end_time=utc_now() + timedelta(hours=3),
        )
        self.assertEqual(p2["subtotal"], 999.99)
        self.assertEqual(p2["platform_fee"], 50.0)
        self.assertEqual(p2["escrow_deposit"], 100.0)
        self.assertEqual(p2["final_amount"], 1149.99)

        # Case 3: 1 hour @ ₹125.50 = ₹125.50 subtotal
        # 5% of 125.50 = 6.275 -> 6.28
        p3 = PricingEngine.calculate_precheck(
            price_per_hour=125.50,
            start_time=utc_now(),
            end_time=utc_now() + timedelta(hours=1),
        )
        self.assertEqual(p3["subtotal"], 125.50)
        self.assertEqual(p3["platform_fee"], 6.28)
        self.assertEqual(p3["escrow_deposit"], 100.0)
        self.assertEqual(p3["final_amount"], 231.78)

    # =========================================================================
    # 6. Payment Adapter, VPA Validation, & Penny-Drop
    # =========================================================================

    def test_payment_adapter_vpa_and_penny_drop(self):
        """Verify payment adapter interface, VPA regex verification, mock penny drop, and disclaimers."""
        adapter = get_payment_adapter()

        # 1. Valid VPA formats
        self.assertTrue(adapter.validate_vpa("user@okhdfcbank"))
        self.assertTrue(adapter.validate_vpa("merchant.store@axisbank"))
        self.assertTrue(adapter.validate_vpa("neha_99@paytm"))

        # 2. Invalid VPA formats
        self.assertFalse(adapter.validate_vpa("invalid-vpa-no-handle"))
        self.assertFalse(adapter.validate_vpa("invalid@"))
        self.assertFalse(adapter.validate_vpa("@bank"))

        # 3. Penny-drop verification
        penny = adapter.verify_penny_drop("host.anand@okhdfcbank")
        self.assertTrue(penny.is_valid)
        self.assertEqual(penny.amount, 1.0)
        self.assertTrue(penny.is_mock)
        self.assertIn("No real currency", penny.mock_disclaimer)

        # 4. Verify VPA API endpoint
        res = self.client.post("/api/v1/escrow/verify-vpa", json={"vpa": "host.anand@okhdfcbank"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertTrue(data["is_valid"])
        self.assertTrue(data["is_mock"])
        self.assertEqual(data["vpa"], "host.anand@okhdfcbank")

    # =========================================================================
    # 7. Admin Dispute Adjudication & Summary
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

    def test_process_scheduled_releases_cron(self):
        """Verify background batch worker auto-releases eligible matured escrows."""
        escrow = EscrowService.hold_funds(self.booking)
        escrow.status = "RELEASE_SCHEDULED"
        escrow.release_scheduled_at = utc_now() - timedelta(minutes=5)
        db.session.commit()

        # Trigger process-releases endpoint
        res = self.client.post("/api/v1/escrow/process-releases")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["data"]["processed_count"], 1)

        db.session.refresh(escrow)
        self.assertEqual(escrow.status, "RELEASED")
        self.assertIsNotNone(escrow.released_at)

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
        self.assertGreaterEqual(data["total_held"], 1045.0)

        # Non-admin view forbidden
        res_guest = self.client.get("/api/v1/escrow/summary", headers=self.guest_headers)
        self.assertEqual(res_guest.status_code, 403)


if __name__ == "__main__":
    unittest.main()
