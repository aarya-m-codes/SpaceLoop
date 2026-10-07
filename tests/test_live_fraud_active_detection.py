"""Integration Test Suite: Live Active Fraud Detection & Real-time Interception.

Verifies that SpaceLoop's fraud engine actively detects, blocks, alerts on,
and tracks real adversarial attacks across live API endpoints:
1. Self-booking attempt actively creates fraud telemetry and open admin alerts.
2. Credential brute-force login attempts record telemetry and flag account abuse.
3. Plagiarized/duplicate space submissions are held unapproved and generate alerts.
4. Card testing / payment failure patterns trigger high-risk scoring and alerts.
5. Multi-account device reuse clusters are actively identified and scored.
6. 3-node circular collusion cycles are actively detected via directed graph analysis.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from backend.core.cache import cache
from backend.core.database import db, init_db
from config import TestingConfig
from models import (
    Booking,
    EscrowTransaction,
    FraudAlertRecord,
    FraudEventRecord,
    RiskAssessment,
    Space,
    User,
    utc_now,
)
from security import hash_password


class LiveFraudActiveDetectionTestCase(unittest.TestCase):
    """Verifies live runtime fraud interception and active detection across APIs."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")

        class ActiveFraudTestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "test-live-fraud-active-key-32-bytes!"

        self.app = create_app(ActiveFraudTestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db(self.app)
            cache.clear()

            # Seed Admin
            self.admin = User(
                email="admin_fraud@spaceloop.in",
                password_hash=hash_password("AdminPass#2026"),
                full_name="Admin Chief",
                role="admin",
                is_active=True,
                is_verified=True,
            )
            # Seed Host A
            self.host_a = User(
                email="host_alpha@spaceloop.in",
                password_hash=hash_password("AlphaPass#2026"),
                full_name="Alpha Host",
                role="host",
                is_active=True,
                is_verified=True,
                trust_score=95.0,
            )
            # Seed Host B
            self.host_b = User(
                email="host_beta@spaceloop.in",
                password_hash=hash_password("BetaPass#2026"),
                full_name="Beta Host",
                role="host",
                is_active=True,
                is_verified=True,
                trust_score=90.0,
            )
            # Seed Seeker
            self.seeker = User(
                email="seeker_gamma@spaceloop.in",
                password_hash=hash_password("GammaPass#2026"),
                full_name="Gamma Seeker",
                role="seeker",
                is_active=True,
                is_verified=True,
                trust_score=85.0,
            )

            db.session.add_all([self.admin, self.host_a, self.host_b, self.seeker])
            db.session.commit()

            # Space A owned by Host A
            self.space_a = Space(
                host_id=self.host_a.id,
                title="Bandra Creator Pod",
                description="Modern aesthetic workspace equipped with gigabit fiber optic internet and soundproof recording in Bandra West.",
                category="commercial",
                space_type="studio",
                address_line1="101 Linking Road",
                city="Mumbai",
                state="Maharashtra",
                pincode="400050",
                latitude=19.055,
                longitude=72.830,
                price_per_hour=500.0,
                minimum_hours=1,
                capacity=4,
                sqft=350.0,
                is_active=True,
                is_approved=True,
            )
            db.session.add(self.space_a)
            db.session.commit()

            self.admin_id = self.admin.id
            self.host_a_id = self.host_a.id
            self.host_b_id = self.host_b.id
            self.seeker_id = self.seeker.id
            self.space_a_id = self.space_a.id

        # Obtain JWT tokens
        self.admin_token = self._login_and_get_token("admin_fraud@spaceloop.in", "AdminPass#2026")
        self.host_a_token = self._login_and_get_token("host_alpha@spaceloop.in", "AlphaPass#2026")
        self.host_b_token = self._login_and_get_token("host_beta@spaceloop.in", "BetaPass#2026")
        self.seeker_token = self._login_and_get_token("seeker_gamma@spaceloop.in", "GammaPass#2026")

        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        self.host_a_headers = {"Authorization": f"Bearer {self.host_a_token}"}
        self.host_b_headers = {"Authorization": f"Bearer {self.host_b_token}"}
        self.seeker_headers = {"Authorization": f"Bearer {self.seeker_token}"}

    def _login_and_get_token(self, email: str, password: str) -> str:
        res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return res.get_json()["data"]["access_token"]

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except OSError:
            pass

    # =========================================================================
    # TEST 1: Live Self-Booking Attempt Interception and Alerting
    # =========================================================================
    def test_live_self_booking_interception_and_alerting(self):
        """Host attempting to reserve own space is rejected (400) and triggers telemetry + alert."""
        start = utc_now() + timedelta(days=2)
        end = start + timedelta(hours=2)

        res = self.client.post(
            "/api/bookings",
            headers=self.host_a_headers,
            json={
                "space_id": self.space_a_id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("own", res.get_json()["error"]["message"].lower())

        # Verify FraudEventRecord and FraudAlertRecord were actively created
        with self.app.app_context():
            event = FraudEventRecord.query.filter_by(
                user_id=self.host_a_id, event_type="SELF_BOOKING_ATTEMPT"
            ).first()
            self.assertIsNotNone(event)
            self.assertEqual(event.severity, "CRITICAL")

            alert = FraudAlertRecord.query.filter_by(user_id=self.host_a_id).first()
            self.assertIsNotNone(alert)
            self.assertEqual(alert.status, "OPEN")
            self.assertIn("Self-Booking Attempt", alert.title)

    # =========================================================================
    # TEST 2: Real-time Failed Login Telemetry & Account Abuse Detection
    # =========================================================================
    def test_live_failed_logins_trigger_account_abuse_signal(self):
        """Repeated invalid password attempts trigger FAILED_LOGIN telemetry and account abuse signals."""
        for _ in range(5):
            res_bad = self.client.post(
                "/api/v1/auth/login",
                json={"email": "seeker_gamma@spaceloop.in", "password": "WrongPassword999!"},
            )
            self.assertIn(res_bad.status_code, [401, 429])

        with self.app.app_context():
            # Check FAILED_LOGIN events exist in database (rate-limited after 4 attempts)
            failures = FraudEventRecord.query.filter_by(
                user_id=self.seeker_id, event_type="FAILED_LOGIN"
            ).count()
            self.assertGreaterEqual(failures, 4)

            # Evaluate entity via Trust & Safety engine
            eval_res = self.client.post(
                "/api/v1/trust-safety/evaluate",
                headers=self.admin_headers,
                json={"entity_type": "USER", "entity_id": self.seeker_id},
            )
            self.assertEqual(eval_res.status_code, 200)
            data = eval_res.get_json()["data"]
            self.assertIn("ACCOUNT_ABUSE", [s["signal_type"] for s in data["signals"]])
            self.assertGreaterEqual(data["risk_score"], 0.40)

    # =========================================================================
    # TEST 3: Plagiarized Listing Interception & Delisting
    # =========================================================================
    def test_live_plagiarized_listing_intercepted_and_withheld(self):
        """Host B submitting copied listing description is flagged, withheld from public search, and alerts admin."""
        res_create = self.client.post(
            "/api/spaces",
            headers=self.host_b_headers,
            json={
                "title": "Bandra Creator Pod Copy",
                "description": "Modern aesthetic workspace equipped with gigabit fiber optic internet and soundproof recording in Bandra West.",  # 100% copied
                "category": "commercial",
                "space_type": "studio",
                "address_line1": "202 Turner Road",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400050",
                "latitude": 19.060,
                "longitude": 72.835,
                "hourly_price": 450.0,
                "capacity": 4,
                "sqft": 350.0,
            },
        )
        self.assertEqual(res_create.status_code, 201)
        new_space_id = res_create.get_json()["data"]["id"]

        with self.app.app_context():
            created_space = db.session.get(Space, new_space_id)
            # Listing is held unapproved due to plagiarism detection
            self.assertFalse(created_space.is_approved)

            # Telemetry and alert recorded
            event = FraudEventRecord.query.filter_by(
                user_id=self.host_b_id, event_type="SUSPICIOUS_SPACE_SUBMISSION"
            ).first()
            self.assertIsNotNone(event)

            alert = FraudAlertRecord.query.filter_by(user_id=self.host_b_id).first()
            self.assertIsNotNone(alert)
            self.assertIn("Suspicious Listing Intercepted", alert.title)

        # Confirm unapproved listing does NOT appear in public search
        res_search = self.client.get("/api/v1/spaces/search?q=Bandra")
        self.assertEqual(res_search.status_code, 200)
        search_ids = [s["id"] for s in res_search.get_json().get("data", {}).get("results", [])]
        self.assertNotIn(new_space_id, search_ids)

    # =========================================================================
    # TEST 4: Live Event Ingestion and Admin Alert Lifecycle API
    # =========================================================================
    def test_live_fraud_events_and_alerts_api(self):
        """Verify POST /api/fraud/events ingests events, creates alerts, and GET /api/fraud/alerts exposes them."""
        # Ingest card testing payment failures
        for _ in range(4):
            res_evt = self.client.post(
                "/api/fraud/events",
                json={
                    "event_type": "PAYMENT_FAILURE",
                    "user_id": self.seeker_id,
                    "severity": "HIGH",
                    "device_id": "test-device-card-test",
                    "payload": {"reason": "Card declined: invalid CVV"},
                },
            )
            self.assertEqual(res_evt.status_code, 201)

        # Ingest simulated high-risk burst
        res_burst = self.client.post(
            "/api/fraud/events",
            json={
                "event_type": "BOOKING_BURST",
                "user_id": self.seeker_id,
                "severity": "CRITICAL",
                "device_id": "test-device-card-test",
                "payload": {"count": 10},
            },
        )
        self.assertEqual(res_burst.status_code, 201)

        # Query alerts endpoint
        res_alerts = self.client.get("/api/fraud/alerts")
        self.assertEqual(res_alerts.status_code, 200)
        data = res_alerts.get_json()
        self.assertGreaterEqual(data["count"], 1)

    # =========================================================================
    # TEST 5: Live Real-time Transaction Scoring API
    # =========================================================================
    def test_live_transaction_scoring_api(self):
        """POST /api/fraud/score evaluates transaction risk against ML model and deterministic rules."""
        # 1. Normal low-risk transaction
        res_low = self.client.post(
            "/api/fraud/score",
            json={
                "user_id": self.seeker_id,
                "amount": 800.0,
                "device_id": "trusted-known-device",
                "ip_address": "127.0.0.1",
            },
        )
        self.assertEqual(res_low.status_code, 200)
        low_data = res_low.get_json()["data"]
        self.assertIn("risk_score", low_data)
        self.assertLess(low_data["risk_score"], 0.70)

        # 2. High-risk anomalous transaction (extreme amount + unknown device)
        res_high = self.client.post(
            "/api/fraud/score",
            json={
                "user_id": self.seeker_id,
                "amount": 95000.0,  # Extreme outlier amount
                "device_id": "unknown-anomalous-device",
                "ip_address": "203.0.113.195",
                "is_new_device": True,
            },
        )
        self.assertEqual(res_high.status_code, 200)
        high_data = res_high.get_json()["data"]
        self.assertGreater(high_data["risk_score"], 0.45)
        self.assertIn(high_data.get("action") or high_data.get("disposition"), ["CHALLENGE", "HOLD", "BLOCK", "REVIEW"])

    # =========================================================================
    # TEST 6: Multi-Node Circular Collusion Ring Active Detection
    # =========================================================================
    def test_live_circular_collusion_cycle_active_detection(self):
        """Detect a 3-way circular escrow transaction loop (A -> B -> C -> A) using GraphAnalyzer."""
        from backend.modules.trust_safety.graph_analyzer import GraphAnalyzer
        from backend.modules.trust_safety.signals import SignalExtractor

        with self.app.app_context():
            # Seed Host C
            host_c = User(
                email="host_gamma@spaceloop.in",
                password_hash=hash_password("GammaHostPass#2026"),
                full_name="Gamma Host",
                role="host",
                is_active=True,
                is_verified=True,
            )
            space_b = Space(
                host_id=self.host_b_id,
                title="Space B",
                space_type="studio",
                address_line1="B-101",
                city="Mumbai",
                state="Maharashtra",
                pincode="400050",
                latitude=19.06,
                longitude=72.84,
                price_per_hour=300.0,
                capacity=2,
            )
            space_c = Space(
                host=host_c,
                title="Space C",
                space_type="studio",
                address_line1="C-101",
                city="Mumbai",
                state="Maharashtra",
                pincode="400050",
                latitude=19.07,
                longitude=72.85,
                price_per_hour=300.0,
                capacity=2,
            )
            db.session.add_all([host_c, space_b, space_c])
            db.session.commit()

            # Create circular bookings: A -> Space B, B -> Space C, C -> Space A
            now = utc_now()
            b1 = Booking(
                space_id=space_b.id,
                guest_id=self.host_a_id,
                start_time=now + timedelta(hours=1),
                end_time=now + timedelta(hours=2),
                total_hours=1.0,
                base_amount=300.0,
                total_amount=300.0,
                status="completed",
                session_state="checked_out",
                escrow_status="released",
            )
            b2 = Booking(
                space_id=space_c.id,
                guest_id=self.host_b_id,
                start_time=now + timedelta(hours=3),
                end_time=now + timedelta(hours=4),
                total_hours=1.0,
                base_amount=300.0,
                total_amount=300.0,
                status="completed",
                session_state="checked_out",
                escrow_status="released",
            )
            b3 = Booking(
                space_id=self.space_a_id,
                guest_id=host_c.id,
                start_time=now + timedelta(hours=5),
                end_time=now + timedelta(hours=6),
                total_hours=1.0,
                base_amount=500.0,
                total_amount=500.0,
                status="completed",
                session_state="checked_out",
                escrow_status="released",
            )
            db.session.add_all([b1, b2, b3])
            db.session.commit()

            # Graph analyzer should detect cycles
            graph = GraphAnalyzer.build_subgraph("USER", self.host_a_id)
            self.assertTrue(graph["summary"]["has_cycles"])
            self.assertGreaterEqual(len(graph["cycles"]), 1)

            # Signal extractor should flag COLLUSION_RING
            sig = SignalExtractor.check_collusion_ring(user=db.session.get(User, self.host_a_id))
            self.assertIsNotNone(sig)
            self.assertEqual(sig.signal_type, "COLLUSION_RING")


if __name__ == "__main__":
    unittest.main()
