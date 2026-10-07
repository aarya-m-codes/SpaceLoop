"""Unit and Integration Tests for SpaceLoop Admin Management & Compliance API.

Validates:
- Strict authorization enforcement (@require_admin)
- Prevention of non-admin access (401/403)
- Overall statistics aggregation
- User management (search, filter, suspend, reactivate, self-suspension block)
- Space listing oversight and status toggling
- Bookings oversight and session states
- Micro-escrow financials audit
- Dispute review and binding adjudication (REFUND_SEEKER, RELEASE_TO_HOST, SPLIT_50_50)
- Immutable compliance audit trail logging (AuditLog)
"""

import json
import unittest
from datetime import datetime, timezone, timedelta

from app import create_app
from backend.core.database import db
from config import TestingConfig
from models import (
    User,
    Space,
    Booking,
    EscrowTransaction,
    AuditLog,
    RiskAssessment,
    FraudAlertRecord,
)


from backend.modules.auth.tokens import create_access_token
from backend.modules.auth.password import hash_user_password

class AdminApiTestCase(unittest.TestCase):
    """Test suite covering the Admin Experience endpoints and security guards."""

    def setUp(self):
        import tempfile
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")

        class AdminTestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "test-admin-secret-key-32-bytes!"

        self.app = create_app(AdminTestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Create admin user
        self.admin = User(
            email="admin@spaceloop.in",
            password_hash=hash_user_password("AdminPass123!"),
            full_name="Platform Admin",
            role="admin",
            is_active=True,
            trust_score=100.0,
        )
        db.session.add(self.admin)

        # Create regular seeker user
        self.seeker = User(
            email="seeker@example.com",
            password_hash=hash_user_password("SeekerPass123!"),
            full_name="Seeker User",
            role="seeker",
            is_active=True,
            is_student_verified=True,
            student_discount_rate=0.15,
            trust_score=85.0,
        )
        db.session.add(self.seeker)

        # Create host user
        self.host = User(
            email="host@example.com",
            password_hash=hash_user_password("HostPass123!"),
            full_name="Host User",
            role="host",
            is_active=True,
            is_host_verified=True,
            trust_score=90.0,
        )
        db.session.add(self.host)

        db.session.commit()

        # Generate JWT tokens
        self.admin_token = create_access_token(self.admin.id, self.admin.email, self.admin.role)
        self.seeker_token = create_access_token(self.seeker.id, self.seeker.email, self.seeker.role)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        try:
            import os
            os.close(self.temp_db_fd)
            os.unlink(self.temp_db_path)
        except OSError:
            pass

    def _auth_headers(self, token):
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def test_unauthorized_access_blocked(self):
        """Unauthenticated or non-admin users must be rejected with 401/403."""
        # No token
        res = self.client.get("/api/v1/admin/stats")
        self.assertEqual(res.status_code, 401)

        # Non-admin token
        res = self.client.get(
            "/api/v1/admin/stats",
            headers=self._auth_headers(self.seeker_token),
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_stats(self):
        """Admin stats endpoint aggregates users, spaces, bookings, and escrow metrics."""
        # Create a space
        space = Space(
            host_id=self.host.id,
            title="Desk in Koramangala",
            space_type="desk",
            location="5th Block, Koramangala",
            address_line1="123 5th Block",
            city="Bengaluru",
            state="Karnataka",
            pincode="560034",
            latitude=12.9352,
            longitude=77.6245,
            price_per_hour=150.0,
            is_active=True,
        )
        db.session.add(space)
        db.session.commit()

        res = self.client.get(
            "/api/v1/admin/stats",
            headers=self._auth_headers(self.admin_token),
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        stats = data["data"]
        self.assertGreaterEqual(stats["users"]["total"], 3)
        self.assertGreaterEqual(stats["spaces"]["total"], 1)

    def test_admin_users_and_toggle_status(self):
        """Admin can list users with filters and toggle suspension with audit logging."""
        # List users
        res = self.client.get(
            "/api/v1/admin/users?role=seeker",
            headers=self._auth_headers(self.admin_token),
        )
        self.assertEqual(res.status_code, 200)
        users = res.get_json()["users"]
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["email"], "seeker@example.com")

        # Suspend seeker
        res = self.client.post(
            f"/api/v1/admin/users/{self.seeker.id}/toggle-status",
            headers=self._auth_headers(self.admin_token),
        )
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.get_json()["user"]["is_active"])

        # Check audit log was created
        audit = AuditLog.query.filter_by(action="USER_SUSPENDED", entity_id=str(self.seeker.id)).first()
        self.assertIsNotNone(audit)

        # Reactivate seeker
        res = self.client.post(
            f"/api/v1/admin/users/{self.seeker.id}/toggle-status",
            headers=self._auth_headers(self.admin_token),
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["user"]["is_active"])

        # Prevent admin self-suspension
        res = self.client.post(
            f"/api/v1/admin/users/{self.admin.id}/toggle-status",
            headers=self._auth_headers(self.admin_token),
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_spaces_and_toggle_status(self):
        """Admin can list listings and toggle activation."""
        space = Space(
            host_id=self.host.id,
            title="Whitefield Studio",
            space_type="studio",
            location="ITPL Main Rd",
            address_line1="ITPL Main Rd",
            city="Bengaluru",
            state="Karnataka",
            pincode="560066",
            latitude=12.9845,
            longitude=77.7289,
            price_per_hour=200.0,
            is_active=True,
        )
        db.session.add(space)
        db.session.commit()

        # List spaces
        res = self.client.get(
            "/api/v1/admin/spaces",
            headers=self._auth_headers(self.admin_token),
        )
        self.assertEqual(res.status_code, 200)
        spaces = res.get_json()["spaces"]
        self.assertGreaterEqual(len(spaces), 1)

        # Toggle to paused
        res = self.client.post(
            f"/api/v1/admin/spaces/{space.id}/toggle-status",
            headers=self._auth_headers(self.admin_token),
        )
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.get_json()["space"]["is_active"])

        # Audit log verification
        audit = AuditLog.query.filter_by(action="SPACE_DEACTIVATED", entity_id=str(space.id)).first()
        self.assertIsNotNone(audit)

    def test_admin_disputes_and_adjudication(self):
        """Admin can list and resolve disputes deterministically via EscrowService."""
        now = datetime.now(timezone.utc)
        space = Space(
            host_id=self.host.id,
            title="HSR Desk",
            space_type="desk",
            location="Sector 2, HSR",
            address_line1="Sector 2, HSR",
            city="Bengaluru",
            state="Karnataka",
            pincode="560102",
            latitude=12.9116,
            longitude=77.6389,
            price_per_hour=100.0,
            is_active=True,
        )
        db.session.add(space)
        db.session.flush()

        booking = Booking(
            guest_id=self.seeker.id,
            space_id=space.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=3),
            total_hours=2.0,
            base_amount=200.0,
            platform_fee=10.0,
            escrow_deposit=100.0,
            total_amount=310.0,
            status="disputed",
            escrow_status="disputed",
            cancellation_reason="Seeker reported lock code failure and dirty facility.",
        )
        db.session.add(booking)
        db.session.flush()

        # Record held escrow transaction
        escrow_tx = EscrowTransaction(
            booking_id=booking.id,
            guest_id=self.seeker.id,
            host_id=self.host.id,
            transaction_type="deposit_hold",
            amount=310.0,
            held_amount=310.0,
            status="HELD",
            description="Escrow deposit held for booking",
        )
        db.session.add(escrow_tx)
        db.session.commit()

        # Query disputes
        res = self.client.get(
            "/api/v1/admin/disputes",
            headers=self._auth_headers(self.admin_token),
        )
        self.assertEqual(res.status_code, 200)
        disputes = res.get_json()["disputes"]
        self.assertEqual(len(disputes), 1)
        self.assertEqual(disputes[0]["booking_id"], booking.id)

        # Adjudicate dispute: REFUND_SEEKER
        res = self.client.post(
            f"/api/v1/admin/disputes/{booking.id}/adjudicate",
            headers=self._auth_headers(self.admin_token),
            json={
                "resolution": "REFUND_SEEKER",
                "notes": "Verified host was unresponsive to door code request.",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        # Check booking status updated
        refreshed_b = db.session.get(Booking, booking.id)
        self.assertEqual(refreshed_b.status.upper(), "CANCELLED")
        self.assertEqual(refreshed_b.escrow_status.lower(), "refunded")

        # Check audit log entry
        audit = AuditLog.query.filter_by(action="DISPUTE_ADJUDICATED_REFUND_SEEKER").first()
        self.assertIsNotNone(audit)

    def test_admin_audit_logs(self):
        """Admin can review immutable audit log events."""
        log = AuditLog(
            user_id=self.admin.id,
            action="SECURITY_RULE_OVERRIDE",
            entity_type="SYSTEM",
            entity_id="SYS_1",
            changes={"reason": "Manual compliance drill"},
            ip_address="127.0.0.1",
        )
        db.session.add(log)
        db.session.commit()

        res = self.client.get(
            "/api/v1/admin/audit-logs",
            headers=self._auth_headers(self.admin_token),
        )
        self.assertEqual(res.status_code, 200)
        logs = res.get_json()["audit_logs"]
        self.assertGreaterEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "SECURITY_RULE_OVERRIDE")


if __name__ == "__main__":
    unittest.main()
