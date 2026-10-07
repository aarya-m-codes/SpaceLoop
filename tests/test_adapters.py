"""Test suite for SpaceLoop External Integration Adapters.

Tests:
1. Email Adapters:
   - InMemoryEmailAdapter
   - ResendEmailAdapter
   - BrevoEmailAdapter
   - SMTPEmailAdapter
   - Transactional email dispatch for all required templates:
     verification, password reset, booking, cancellation, host approval/rejection, check-in, checkout, dispute
   - EmailLog persistence & audit querying
2. Student Verification:
   - POST /api/verify/student
   - 15% discount rate application
   - Privacy guarantee: raw student ID is tokenized via SHA-256, never stored raw
3. Aadhaar Verification:
   - POST /api/verify/aadhaar
   - Privacy guarantee: raw 12-digit Aadhaar is tokenized via SHA-256, never stored raw
   - Masked display format
4. Host Verification:
   - POST /api/verify/host
   - DISCOM utility bill verification
   - UPI penny-drop / beneficiary name matching
   - Clear indication of mock vs live external mode
"""

import hashlib
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from backend.core.cache import cache
from backend.core.database import db, init_db
from backend.modules.email.adapters.base import EmailDispatchResult
from backend.modules.email.adapters.brevo_adapter import BrevoEmailAdapter
from backend.modules.email.adapters.memory import InMemoryEmailAdapter
from backend.modules.email.adapters.resend_adapter import ResendEmailAdapter
from backend.modules.email.adapters.smtp_adapter import SMTPEmailAdapter
from backend.modules.email.service import EmailService
from backend.modules.verification.service import VerificationService
from config import TestingConfig
from models import EmailLog, User
from security import hash_password


class ExternalAdaptersTestCase(unittest.TestCase):
    """Test suite for external provider adapters and verification endpoints."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")

        class AdapterTestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "test-adapter-secret-key-32-bytes"

        self.app = create_app(AdapterTestConfig)
        self.client = self.app.test_client()

        # Force EmailService to use a fresh InMemoryEmailAdapter
        self.memory_adapter = InMemoryEmailAdapter()
        EmailService.set_adapter(self.memory_adapter)

        # Reset verification adapters to default
        VerificationService.set_student_adapter(None)
        VerificationService.set_aadhaar_adapter(None)
        VerificationService.set_discom_adapter(None)
        VerificationService.set_upi_adapter(None)

        with self.app.app_context():
            init_db(self.app)
            cache.clear()

            self.user = User(
                email="rohan.student@iitb.ac.in",
                password_hash=hash_password("Password#2026"),
                full_name="Rohan Verma",
                role="seeker",
                is_active=True,
                is_verified=True,
            )
            self.host_user = User(
                email="anita.host@spaceloop.in",
                password_hash=hash_password("Password#2026"),
                full_name="Anita Sharma",
                role="host",
                is_active=True,
                is_verified=True,
            )
            db.session.add_all([self.user, self.host_user])
            db.session.commit()

            self.user_id = self.user.id
            self.host_user_id = self.host_user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except OSError:
            pass

    # =========================================================================
    # 1. EMAIL ADAPTER TESTS
    # =========================================================================

    def test_in_memory_email_adapter(self):
        """Test that InMemoryEmailAdapter stores emails in memory and supports clearing."""
        adapter = InMemoryEmailAdapter()
        res = adapter.send_email(
            to_email="test@spaceloop.in",
            subject="Test Subject",
            html_content="<p>Test</p>",
            text_content="Test",
        )
        self.assertTrue(res.success)
        self.assertEqual(res.provider, "in_memory")
        self.assertEqual(len(adapter.get_outbox()), 1)

        last = adapter.get_last_email()
        self.assertIsNotNone(last)
        self.assertEqual(last["to"], "test@spaceloop.in")
        self.assertEqual(last["subject"], "Test Subject")

        adapter.clear()
        self.assertEqual(len(adapter.get_outbox()), 0)

    @patch("requests.post")
    def test_resend_email_adapter(self, mock_post):
        """Test ResendEmailAdapter dispatches API requests correctly."""
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id": "resend-msg-123"})
        adapter = ResendEmailAdapter(api_key="re_test_key_123")

        res = adapter.send_email(
            to_email="user@spaceloop.in",
            subject="Resend Test",
            html_content="<p>Hello Resend</p>",
        )
        self.assertTrue(res.success)
        self.assertEqual(res.provider, "resend")
        self.assertEqual(res.message_id, "resend-msg-123")

        # Test failure without API key
        adapter_no_key = ResendEmailAdapter(api_key="")
        res_fail = adapter_no_key.send_email(to_email="user@spaceloop.in", subject="Fail", html_content="<p>Fail</p>")
        self.assertFalse(res_fail.success)
        self.assertIn("not configured", res_fail.error)

    @patch("requests.post")
    def test_brevo_email_adapter(self, mock_post):
        """Test BrevoEmailAdapter dispatches API requests correctly."""
        mock_post.return_value = MagicMock(status_code=201, json=lambda: {"messageId": "brevo-msg-456"})
        adapter = BrevoEmailAdapter(api_key="xkeysib-test-123")

        res = adapter.send_email(
            to_email="user@spaceloop.in",
            subject="Brevo Test",
            html_content="<p>Hello Brevo</p>",
        )
        self.assertTrue(res.success)
        self.assertEqual(res.provider, "brevo")
        self.assertEqual(res.message_id, "brevo-msg-456")

        # Test failure without API key
        adapter_no_key = BrevoEmailAdapter(api_key="")
        res_fail = adapter_no_key.send_email(to_email="user@spaceloop.in", subject="Fail", html_content="<p>Fail</p>")
        self.assertFalse(res_fail.success)
        self.assertIn("not configured", res_fail.error)

    @patch("smtplib.SMTP")
    def test_smtp_email_adapter(self, mock_smtp_cls):
        """Test SMTPEmailAdapter transmits multipart MIME messages."""
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server

        adapter = SMTPEmailAdapter(host="smtp.mailtrap.io", port=587, user="user", password="pwd", use_tls=True)
        res = adapter.send_email(
            to_email="user@spaceloop.in",
            subject="SMTP Test",
            html_content="<p>Hello SMTP</p>",
            text_content="Hello SMTP",
        )
        self.assertTrue(res.success)
        self.assertEqual(res.provider, "smtp")
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pwd")
        mock_server.send_message.assert_called_once()

    def test_transactional_email_templates_and_email_log(self):
        """Test that all 8+ transactional templates dispatch and create EmailLog entries."""
        with self.app.app_context():
            recipient = "guest@spaceloop.in"

            # 1. Verification
            s1, l1 = EmailService.send_verification_email(recipient, token="TOKEN-123", user_name="Rohan")
            self.assertTrue(s1)
            self.assertEqual(l1.template_name, "verification")
            self.assertEqual(l1.status, "SENT")
            self.assertIn("Verify", l1.subject)

            # 2. Password Reset
            s2, l2 = EmailService.send_password_reset_email(recipient, token="RESET-456", user_name="Rohan")
            self.assertTrue(s2)
            self.assertEqual(l2.template_name, "password_reset")
            self.assertIn("Reset", l2.subject)

            # 3. Booking Confirmation
            s3, l3 = EmailService.send_booking_confirmation_email(
                recipient,
                {
                    "space_title": "Indiranagar Creative Desk",
                    "start_time": "10:00 AM",
                    "end_time": "02:00 PM",
                    "arrival_pin": "4491",
                    "total_price": 750.0,
                },
            )
            self.assertTrue(s3)
            self.assertEqual(l3.template_name, "booking")
            self.assertIn("Booking Confirmed", l3.subject)

            # 4. Cancellation
            s4, l4 = EmailService.send_cancellation_email(
                recipient,
                {
                    "booking_id": "BK-901",
                    "refund_amount": 712.50,
                    "platform_fee": 37.50,
                    "deposit_refunded": 100.0,
                },
            )
            self.assertTrue(s4)
            self.assertEqual(l4.template_name, "cancellation")
            self.assertIn("Cancelled", l4.subject)

            # 5. Host Approval
            s5, l5 = EmailService.send_host_approval_email(
                recipient,
                {
                    "space_title": "Indiranagar Creative Desk",
                    "booking_id": "BK-901",
                    "arrival_pin": "4491",
                },
            )
            self.assertTrue(s5)
            self.assertEqual(l5.template_name, "host_approval")

            # 6. Host Rejection
            s6, l6 = EmailService.send_host_rejection_email(
                recipient,
                {
                    "space_title": "Indiranagar Creative Desk",
                    "booking_id": "BK-901",
                    "refund_amount": 750.0,
                    "reason": "Host traveling",
                },
            )
            self.assertTrue(s6)
            self.assertEqual(l6.template_name, "host_rejection")

            # 7. Check-In
            s7, l7 = EmailService.send_check_in_email(
                recipient,
                {
                    "space_title": "Indiranagar Creative Desk",
                    "booking_id": "BK-901",
                    "check_in_time": "10:05 AM",
                },
            )
            self.assertTrue(s7)
            self.assertEqual(l7.template_name, "check_in")

            # 8. Check-Out
            s8, l8 = EmailService.send_checkout_email(
                recipient,
                {
                    "space_title": "Indiranagar Creative Desk",
                    "booking_id": "BK-901",
                    "deposit_released": 100.0,
                },
            )
            self.assertTrue(s8)
            self.assertEqual(l8.template_name, "checkout")

            # 9. Dispute
            s9, l9 = EmailService.send_dispute_email(
                recipient,
                {
                    "booking_id": "BK-901",
                    "dispute_reason": "Space power outage",
                },
            )
            self.assertTrue(s9)
            self.assertEqual(l9.template_name, "dispute")

            # Verify in-memory outbox has all 9 dispatched emails
            outbox = self.memory_adapter.get_outbox()
            self.assertEqual(len(outbox), 9)

            # Verify database EmailLog query
            logs = EmailService.get_email_logs(recipient_email=recipient)
            self.assertEqual(len(logs), 9)
            self.assertTrue(all(log["status"] == "SENT" for log in logs))

    # =========================================================================
    # 2. STUDENT VERIFICATION TESTS
    # =========================================================================

    def test_student_verification_success_15_percent_discount(self):
        """Test POST /api/verify/student verifies accredited student and grants 15% discount."""
        res = self.client.post(
            "/api/verify/student",
            json={
                "user_id": self.user_id,
                "student_id": "IITB-2026-CS-409",
                "university_email": "rohan@cse.iitb.ac.in",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertTrue(data["student_verified"])
        self.assertEqual(data["discount_rate"], 0.15)  # Exactly 15% discount
        self.assertEqual(data["university_email"], "rohan@cse.iitb.ac.in")
        self.assertEqual(data["verification_mode"], "mock")
        self.assertFalse(data["external_verified"])

        # CRITICAL PRIVACY INVARIANT: Ensure raw student ID is NEVER stored
        raw_id = "IITB-2026-CS-409"
        expected_hash = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
        self.assertEqual(data["student_id_token"], expected_hash)

        with self.app.app_context():
            u = User.query.get(self.user_id)
            self.assertTrue(u.is_student_verified)
            self.assertEqual(u.student_discount_rate, 0.15)
            self.assertEqual(u.student_id_hash, expected_hash)
            # Raw student ID is nowhere on the record
            self.assertNotEqual(u.student_id_hash, raw_id)

    def test_student_verification_rejects_non_educational_email(self):
        """Test POST /api/verify/student rejects personal/commercial domains."""
        res = self.client.post(
            "/api/verify/student",
            json={
                "user_id": self.user_id,
                "student_id": "STU-9999",
                "university_email": "rohan.freelancer@gmail.com",
            },
        )
        self.assertEqual(res.status_code, 422)
        err = res.get_json()["error"]
        self.assertEqual(err["code"], "STUDENT_VERIFICATION_FAILED")
        self.assertIn("educational institution", err["message"])

    def test_student_verification_missing_fields(self):
        """Test validation error when student ID or email is absent."""
        res = self.client.post("/api/verify/student", json={"student_id": "STU-123"})
        self.assertEqual(res.status_code, 400)

    # =========================================================================
    # 3. AADHAAR VERIFICATION TESTS
    # =========================================================================

    def test_aadhaar_verification_privacy_and_tokenization(self):
        """Test POST /api/verify/aadhaar tokenizes via SHA-256 and never stores raw 12 digits."""
        raw_aadhaar = "999988887777"
        expected_hash = hashlib.sha256(raw_aadhaar.encode("utf-8")).hexdigest()

        res = self.client.post(
            "/api/verify/aadhaar",
            json={
                "user_id": self.user_id,
                "aadhaar_number": raw_aadhaar,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertTrue(data["aadhaar_verified"])
        self.assertEqual(data["masked_aadhaar"], "XXXX-XXXX-7777")
        self.assertEqual(data["aadhaar_token"], expected_hash)
        self.assertEqual(data["verification_mode"], "mock")

        with self.app.app_context():
            u = User.query.get(self.user_id)
            self.assertEqual(u.aadhaar_hash, expected_hash)
            self.assertEqual(u.kyc_status, "VERIFIED")
            # Raw Aadhaar is never saved in database
            self.assertNotEqual(u.aadhaar_hash, raw_aadhaar)

    def test_aadhaar_verification_invalid_length(self):
        """Test that invalid digit count fails validation."""
        res = self.client.post(
            "/api/verify/aadhaar",
            json={
                "user_id": self.user_id,
                "aadhaar_number": "12345",  # Too short
            },
        )
        self.assertEqual(res.status_code, 422)

    # =========================================================================
    # 4. HOST VERIFICATION TESTS (DISCOM + UPI PENNY-DROP)
    # =========================================================================

    def test_host_verification_success(self):
        """Test POST /api/verify/host successfully verifies DISCOM and UPI beneficiary."""
        res = self.client.post(
            "/api/verify/host",
            json={
                "user_id": self.host_user_id,
                "discom_consumer_no": "1029384756",
                "discom_provider": "Adani Electricity Mumbai",
                "upi_vpa": "anita.sharma@okhdfcbank",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertTrue(data["host_verified"])
        self.assertTrue(data["discom_verified"])
        self.assertTrue(data["upi_verified"])
        self.assertEqual(data["discom_provider"], "Adani Electricity Mumbai")
        self.assertEqual(data["upi_vpa"], "anita.sharma@okhdfcbank")
        self.assertEqual(data["verification_mode"], "mock")
        self.assertFalse(data["external_verified"])  # Clearly identifies development mock

        expected_consumer_hash = hashlib.sha256("1029384756".encode("utf-8")).hexdigest()
        self.assertEqual(data["discom_consumer_token"], expected_consumer_hash)

        with self.app.app_context():
            h = User.query.get(self.host_user_id)
            self.assertTrue(h.is_host_verified)
            self.assertEqual(h.discom_provider, "Adani Electricity Mumbai")
            self.assertEqual(h.discom_consumer_hash, expected_consumer_hash)
            self.assertEqual(h.upi_vpa, "anita.sharma@okhdfcbank")

    def test_host_verification_rejects_unknown_discom(self):
        """Test POST /api/verify/host rejects unregistered DISCOM provider."""
        res = self.client.post(
            "/api/verify/host",
            json={
                "user_id": self.host_user_id,
                "discom_consumer_no": "1029384756",
                "discom_provider": "Fictional Electricity Corporation",
                "upi_vpa": "anita@okhdfcbank",
            },
        )
        self.assertEqual(res.status_code, 422)
        err = res.get_json()["error"]
        self.assertEqual(err["code"], "HOST_VERIFICATION_FAILED")
        self.assertFalse(err["discom_verified"])

    def test_host_verification_rejects_invalid_upi_vpa(self):
        """Test POST /api/verify/host rejects malformed UPI VPA."""
        res = self.client.post(
            "/api/verify/host",
            json={
                "user_id": self.host_user_id,
                "discom_consumer_no": "1029384756",
                "discom_provider": "Tata Power Mumbai",
                "upi_vpa": "invalid-vpa-without-at-symbol",
            },
        )
        self.assertEqual(res.status_code, 422)
        err = res.get_json()["error"]
        self.assertEqual(err["code"], "HOST_VERIFICATION_FAILED")
        self.assertFalse(err["upi_verified"])


if __name__ == "__main__":
    unittest.main()
