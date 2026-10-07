"""Comprehensive Adversarial Test Suite for SpaceLoop Fraud & Trust & Safety Architectures.

Validates:
SYSTEM A: Marketplace Trust & Safety Engine
- Behavioral Signal Extraction: SELF_BOOKING, COLLUSION_RING, VELOCITY_SPIKE, DEVICE_REUSE, DISCOM_MISMATCH, RAPID_DISPUTE
- Multi-partite Graph relationships & circular cycle detection (A -> B -> A, A -> B -> C -> A)
- Forensic narrative generation with 3-tier fallback (Groq -> Gemini -> Deterministic)
- Strict Admin-only authorization enforcement on /api/v1/trust-safety/* endpoints

SYSTEM B: Autonomous ML Fraud Engine
- Continuous numerical behavioral feature extraction
- Isolation Forest anomaly detection with deterministic statistical fallback
- Real-time event ingestion (POST /api/fraud/events) and alert creation
- Decision thresholds (BLOCK >= 0.80, HOLD/REVIEW >= 0.60, CHALLENGE >= 0.40, ALLOW < 0.40)
- Critical Safety Invariant: High ML anomaly without deterministic policy validation is capped below 0.80 (REVIEW), NEVER auto-banned
- Explainability of all risk decisions
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from backend.core.cache import cache
from backend.core.database import db, init_db
from config import TestingConfig
from fraud_engine.feature_extractor import FeatureExtractor
from fraud_engine.isolation_forest import IsolationForestAnomalyDetector
from fraud_engine.rules import PolicyRuleEngine
from fraud_engine.scorer import FraudRiskScorer
from fraud_engine.service import FraudEngineService
from models import Booking, DeviceSession, FraudAlertRecord, FraudEventRecord, RiskAssessment, Space, User, utc_now
from security import hash_password


class FraudAndTrustSafetyTestCase(unittest.TestCase):
    """Adversarial and functional test suite for Fraud & Trust & Safety engines."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")

        class FraudTestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "test-fraud-key-32-bytes-secure!!"

        self.app = create_app(FraudTestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db(self.app)
            cache.clear()

            # Seed Admin
            self.admin = User(
                email="admin_safety@spaceloop.in",
                password_hash=hash_password("AdminPass#2026"),
                full_name="Compliance Admin",
                role="admin",
                is_active=True,
                is_verified=True,
            )
            # Seed Host A
            self.host_a = User(
                email="host_a@spaceloop.in",
                password_hash=hash_password("HostPass#2026"),
                full_name="Amitabh Host",
                role="host",
                is_active=True,
                is_verified=True,
                trust_score=95.0,
            )
            # Seed Host B
            self.host_b = User(
                email="host_b@spaceloop.in",
                password_hash=hash_password("HostPass#2026"),
                full_name="Bharat Host",
                role="host",
                is_active=True,
                is_verified=True,
                trust_score=90.0,
            )
            # Seed Seeker / Guest
            self.seeker = User(
                email="seeker1@spaceloop.in",
                password_hash=hash_password("SeekerPass#2026"),
                full_name="Chetan Seeker",
                role="seeker",
                is_active=True,
                is_verified=True,
                trust_score=80.0,
            )

            db.session.add_all([self.admin, self.host_a, self.host_b, self.seeker])
            db.session.commit()

            # Space A owned by Host A
            self.space_a = Space(
                host_id=self.host_a.id,
                title="Andheri Sound Studio",
                category="commercial",
                space_type="studio",
                address_line1="Veera Desai Road",
                city="Mumbai",
                state="Maharashtra",
                pincode="400053",
                latitude=19.1363,
                longitude=72.8276,
                price_per_hour=500.0,
                minimum_hours=2,
                capacity=5,
                is_active=True,
                is_approved=True,
            )
            # Space B owned by Host B
            self.space_b = Space(
                host_id=self.host_b.id,
                title="Bandra Creator Loft",
                category="commercial",
                space_type="desk",
                address_line1="Hill Road",
                city="Mumbai",
                state="Maharashtra",
                pincode="400050",
                latitude=19.0596,
                longitude=72.8295,
                price_per_hour=400.0,
                minimum_hours=1,
                capacity=4,
                is_active=True,
                is_approved=True,
            )
            db.session.add_all([self.space_a, self.space_b])
            db.session.commit()

            self.admin_id = self.admin.id
            self.host_a_id = self.host_a.id
            self.host_b_id = self.host_b.id
            self.seeker_id = self.seeker.id
            self.space_a_id = self.space_a.id
            self.space_b_id = self.space_b.id

        # Obtain JWT tokens
        self.admin_token = self._login_and_get_token("admin_safety@spaceloop.in", "AdminPass#2026")
        self.host_a_token = self._login_and_get_token("host_a@spaceloop.in", "HostPass#2026")
        self.seeker_token = self._login_and_get_token("seeker1@spaceloop.in", "SeekerPass#2026")

    def _login_and_get_token(self, email: str, password: str) -> str:
        res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return res.get_json()["data"]["access_token"]

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
    # SYSTEM A TESTS: Trust & Safety Engine
    # =========================================================================

    def test_system_a_self_booking_signal(self):
        """Test behavioral extraction of SELF_BOOKING when a host books their own space."""
        from backend.modules.trust_safety.signals import SignalExtractor

        with self.app.app_context():
            # Host A books Space A
            host = User.query.get(self.host_a_id)
            space = Space.query.get(self.space_a_id)

            signal = SignalExtractor.check_self_booking(user=host, space=space)
            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "SELF_BOOKING")
            self.assertEqual(signal.severity, "CRITICAL")
            self.assertGreaterEqual(signal.weight, 0.85)
            self.assertIn("identical to host_id", signal.evidence[0])

    def test_system_a_collusion_ring_two_node_cycle(self):
        """Test detection of 2-node reciprocal collusion ring (A -> B and B -> A)."""
        from backend.modules.trust_safety.graph_analyzer import GraphAnalyzer
        from backend.modules.trust_safety.signals import SignalExtractor

        with self.app.app_context():
            # Host A books Space B (owned by Host B)
            b1 = Booking(
                space_id=self.space_b_id,
                guest_id=self.host_a_id,
                start_time=utc_now() + timedelta(hours=2),
                end_time=utc_now() + timedelta(hours=4),
                total_hours=2.0,
                base_amount=800.0,
                total_amount=800.0,
                status="completed",
                session_state="checked_out",
                escrow_status="released",
            )
            # Host B books Space A (owned by Host A)
            b2 = Booking(
                space_id=self.space_a_id,
                guest_id=self.host_b_id,
                start_time=utc_now() + timedelta(hours=5),
                end_time=utc_now() + timedelta(hours=7),
                total_hours=2.0,
                base_amount=1000.0,
                total_amount=1000.0,
                status="completed",
                session_state="checked_out",
                escrow_status="released",
            )
            db.session.add_all([b1, b2])
            db.session.commit()

            # Signal extractor should flag COLLUSION_RING for Host A
            host_a = User.query.get(self.host_a_id)
            signal = SignalExtractor.check_collusion_ring(user=host_a)
            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "COLLUSION_RING")
            self.assertEqual(signal.severity, "CRITICAL")
            self.assertIn("Reciprocal 2-cycle detected", signal.evidence[0])

            # Graph analyzer should detect the reciprocal loop
            subgraph = GraphAnalyzer.build_subgraph("USER", self.host_a_id)
            self.assertTrue(subgraph["summary"]["has_cycles"])
            self.assertGreaterEqual(len(subgraph["cycles"]), 1)
            self.assertEqual(subgraph["cycles"][0]["cycle_type"], "RECIPROCAL_PAIR")

    def test_system_a_velocity_spike_signal(self):
        """Test extraction of VELOCITY_SPIKE when bookings flood rapidly."""
        from backend.modules.trust_safety.signals import SignalExtractor

        with self.app.app_context():
            # Inject 4 rapid bookings for seeker within last 5 minutes
            for i in range(4):
                b = Booking(
                    space_id=self.space_a_id,
                    guest_id=self.seeker_id,
                    start_time=utc_now() + timedelta(days=i + 1),
                    end_time=utc_now() + timedelta(days=i + 1, hours=2),
                    total_hours=2.0,
                    base_amount=1000.0,
                    total_amount=1000.0,
                    status="pending",
                    created_at=utc_now() - timedelta(minutes=2),
                )
                db.session.add(b)
            db.session.commit()

            seeker = User.query.get(self.seeker_id)
            signal = SignalExtractor.check_velocity_spike(user=seeker)
            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "VELOCITY_SPIKE")
            self.assertIn("High booking velocity", signal.evidence[0])

    def test_system_a_device_reuse_signal(self):
        """Test extraction of DEVICE_REUSE when multiple accounts share hardware fingerprint."""
        from backend.modules.trust_safety.signals import SignalExtractor

        with self.app.app_context():
            shared_fingerprint = "hw-fingerprint-macbook-m3-pro-8899"
            # Host A and Seeker both register telemetry with identical hardware device fingerprint
            ev1 = FraudEventRecord(
                user_id=self.host_a_id,
                device_fingerprint=shared_fingerprint,
                event_type="LOGIN",
                severity="INFO",
            )
            ev2 = FraudEventRecord(
                user_id=self.seeker_id,
                device_fingerprint=shared_fingerprint,
                event_type="LOGIN",
                severity="INFO",
            )
            db.session.add_all([ev1, ev2])
            db.session.commit()

            host_a = User.query.get(self.host_a_id)
            signal = SignalExtractor.check_device_reuse(user=host_a, device_fingerprint=shared_fingerprint)
            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "DEVICE_REUSE")
            self.assertIn("shared across 2 distinct user accounts", signal.evidence[0])

    def test_system_a_discom_mismatch_signal(self):
        """Test extraction of DISCOM_MISMATCH when utility board conflicts with geography."""
        from backend.modules.trust_safety.signals import SignalExtractor

        with self.app.app_context():
            space = Space.query.get(self.space_a_id)  # Mumbai space
            # Provide BESCOM (Bangalore) for a Mumbai space
            ctx = {
                "discom_provider": "BESCOM Karnataka",
                "discom_consumer_no": "KA-1029384756",
            }
            signal = SignalExtractor.check_discom_mismatch(space=space, context=ctx)
            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "DISCOM_MISMATCH")
            self.assertEqual(signal.severity, "HIGH")
            self.assertIn("does not operate in Mumbai", signal.evidence[0])

    def test_system_a_rapid_dispute_signal(self):
        """Test extraction of RAPID_DISPUTE on exploitative post-check-in dispute."""
        from backend.modules.trust_safety.signals import SignalExtractor

        with self.app.app_context():
            checkin = utc_now() - timedelta(minutes=2)
            dispute_time = utc_now()  # 120 seconds after check-in

            b = Booking(
                space_id=self.space_a_id,
                guest_id=self.seeker_id,
                start_time=utc_now() - timedelta(minutes=10),
                end_time=utc_now() + timedelta(hours=2),
                total_hours=2.0,
                base_amount=1000.0,
                total_amount=1000.0,
                status="DISPUTED",
                session_state="checked_in",
                escrow_status="disputed",
                check_in_time=checkin,
                updated_at=dispute_time,
            )
            db.session.add(b)
            db.session.commit()

            seeker = User.query.get(self.seeker_id)
            signal = SignalExtractor.check_rapid_dispute(user=seeker, booking=b)
            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "RAPID_DISPUTE")
            self.assertIn("Dispute filed", signal.evidence[0])

    def test_system_a_forensic_narrative_outage_resilience(self):
        """Test narrative generation completes deterministically during simulated AI outage."""
        from backend.modules.trust_safety.narrative_generator import ForensicNarrativeGenerator
        from backend.modules.trust_safety.signals import BehavioralSignal

        signals = [
            BehavioralSignal(
                signal_type="COLLUSION_RING",
                severity="CRITICAL",
                weight=0.92,
                title="Circular Collusion Ring Identified",
                description="Detected closed-loop circular transaction graph.",
                evidence=["User 1 -> User 2 -> User 1"],
            )
        ]
        graph_summary = {
            "has_cycles": True,
            "cycles": [{"description": "User #1 -> User #2 -> User #1", "cycle_type": "RECIPROCAL_PAIR"}],
            "has_device_clustering": False,
        }

        # Simulate full AI outage
        os.environ["SIMULATE_AI_OUTAGE"] = "true"
        try:
            narrative = ForensicNarrativeGenerator.generate(
                entity_type="USER",
                entity_id=1,
                signals=signals,
                graph_summary=graph_summary,
                risk_score=0.92,
                action="BLOCK",
            )
            self.assertIn("SpaceLoop Trust & Safety Forensic Audit", narrative)
            self.assertIn("COLLUSION_RING", narrative)
            self.assertIn("BLOCK", narrative)
        finally:
            os.environ.pop("SIMULATE_AI_OUTAGE", None)

    def test_system_a_admin_only_endpoints(self):
        """Test that /api/v1/trust-safety/* endpoints strictly require Admin privileges."""
        # 1. Unauthenticated (using fresh client without auth cookie) -> 401
        fresh_client = self.app.test_client()
        res = fresh_client.get("/api/v1/trust-safety/assessments")
        self.assertEqual(res.status_code, 401)

        # 2. Authenticated as Seeker (non-admin) -> 403 Forbidden
        res = self.client.get(
            "/api/v1/trust-safety/assessments",
            headers={"Authorization": f"Bearer {self.seeker_token}"},
        )
        self.assertEqual(res.status_code, 403)

        # 3. Authenticated as Host (non-admin) -> 403 Forbidden
        res = self.client.post(
            "/api/v1/trust-safety/evaluate",
            headers={"Authorization": f"Bearer {self.host_a_token}"},
            json={"entity_type": "USER", "entity_id": self.host_a_id},
        )
        self.assertEqual(res.status_code, 403)

        # 4. Authenticated as Admin -> 200 OK
        res = self.client.post(
            "/api/v1/trust-safety/evaluate",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={"entity_type": "USER", "entity_id": self.host_a_id},
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertEqual(data["entity_type"], "USER")
        self.assertIn("risk_score", data)
        self.assertIn("narrative", data)

        # 5. Admin lists assessments
        res = self.client.get(
            "/api/v1/trust-safety/assessments",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.get_json()["count"], 1)

        # 6. Admin fetches multi-partite graph
        res = self.client.get(
            f"/api/v1/trust-safety/graph/USER/{self.host_a_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(res.status_code, 200)
        graph_data = res.get_json()["data"]
        self.assertIn("nodes", graph_data)
        self.assertIn("edges", graph_data)

    # =========================================================================
    # SYSTEM B TESTS: Autonomous ML Fraud Engine
    # =========================================================================

    def test_system_b_feature_extraction(self):
        """Test continuous numerical feature extraction."""
        with self.app.app_context():
            seeker = User.query.get(self.seeker_id)
            extracted = FeatureExtractor.extract_features(
                user=seeker,
                amount=5000.0,
                ip_address="203.0.113.45",
                device_fingerprint="device-token-xyz-123",
                context={"network_behavior": 0.45},
            )
            features = extracted["features"]
            vector = extracted["vector"]

            self.assertIn("account_age_days", features)
            self.assertIn("booking_velocity_1h", features)
            self.assertIn("amount_anomalies", features)
            self.assertIn("listing_price_variance", features)
            self.assertIn("ip_sharing_count", features)
            self.assertIn("device_sharing_count", features)
            self.assertIn("network_behavior", features)
            self.assertEqual(len(vector), 8)

    def test_system_b_isolation_forest_statistical_fallback(self):
        """Test statistical baseline anomaly calculation without external model artifact."""
        clean_vector = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05]
        score_clean = IsolationForestAnomalyDetector.score(clean_vector)
        self.assertEqual(score_clean["engine_mode"], "DETERMINISTIC_STATISTICAL_FALLBACK")
        self.assertLess(score_clean["anomaly_score"], 0.25)

        anomaly_vector = [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.95]
        score_anomaly = IsolationForestAnomalyDetector.score(anomaly_vector)
        self.assertGreater(score_anomaly["anomaly_score"], 0.80)
        self.assertTrue(score_anomaly["is_anomaly"])

    def test_system_b_decision_thresholds(self):
        """Test strict implementation of decision thresholds:
        - risk >= 0.80 => BLOCK
        - risk >= 0.60 => HOLD / REVIEW
        - risk >= 0.40 => CHALLENGE / MFA / KYC
        - risk < 0.40  => ALLOW
        """
        # 1. ALLOW (< 0.40)
        f_allow = {"account_age_days": 100.0, "booking_velocity_1h": 0.0}
        v_allow = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05]
        res_allow = FraudRiskScorer.evaluate(f_allow, v_allow)
        self.assertLess(res_allow["risk_score"], 0.40)
        self.assertEqual(res_allow["decision"], "ALLOW")

        # 2. CHALLENGE / MFA / KYC (0.40 <= risk < 0.60)
        f_chal = {"account_age_days": 10.0, "network_behavior": 0.85}
        v_chal = [0.2, 0.2, 0.2, 0.3, 0.0, 0.3, 0.3, 0.85]
        res_chal = FraudRiskScorer.evaluate(f_chal, v_chal)
        self.assertGreaterEqual(res_chal["risk_score"], 0.40)
        self.assertLess(res_chal["risk_score"], 0.60)
        self.assertEqual(res_chal["decision"], "CHALLENGE / MFA / KYC")

        # 3. HOLD / REVIEW (0.60 <= risk < 0.80)
        f_rev = {"device_sharing_count": 3, "account_age_days": 0.5, "raw_amount": 25000.0}
        v_rev = [0.01, 0.3, 0.3, 0.6, 0.0, 0.5, 0.8, 0.5]
        res_rev = FraudRiskScorer.evaluate(f_rev, v_rev)
        self.assertGreaterEqual(res_rev["risk_score"], 0.60)
        self.assertLess(res_rev["risk_score"], 0.80)
        self.assertEqual(res_rev["decision"], "HOLD / REVIEW")

        # 4. BLOCK (>= 0.80 with deterministic policy rule)
        f_block = {"booking_velocity_1h": 8.0}
        v_block = [0.0, 1.0, 1.0, 0.8, 0.0, 0.5, 0.8, 0.8]
        ctx_block = {"blacklisted_device": True}  # Deterministic policy validation
        res_block = FraudRiskScorer.evaluate(f_block, v_block, context=ctx_block)
        self.assertGreaterEqual(res_block["risk_score"], 0.80)
        self.assertEqual(res_block["decision"], "BLOCK")

    def test_system_b_critical_safety_invariant_prevents_ml_autoban(self):
        """CRITICAL INVARIANT:
        Do not automatically ban users solely because an ML model produced an anomaly score
        without deterministic policy validation.
        """
        # Vector produces extreme ML anomaly
        extreme_ml_vector = [0.0, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
        features = {
            "account_age_days": 0.1,
            "booking_velocity_1h": 2.0,  # Below flood threshold
            "raw_amount": 1000.0,        # Standard amount
        }
        # No deterministic policy violation provided in context
        clean_ctx = {}

        evaluation = FraudRiskScorer.evaluate(features, extreme_ml_vector, context=clean_ctx)

        # ML anomaly score is high
        self.assertGreaterEqual(evaluation["ml_anomaly_score"], 0.80)
        # But composite risk score MUST be capped below 0.80 and route to HOLD / REVIEW, NOT BLOCK
        self.assertTrue(evaluation["governance_capped"])
        self.assertLess(evaluation["risk_score"], 0.80)
        self.assertEqual(evaluation["decision"], "HOLD / REVIEW")
        self.assertNotEqual(evaluation["decision"], "BLOCK")
        self.assertIn("Automatic account block suppressed", evaluation["governance_reason"])

    def test_system_b_api_event_ingestion_and_alert_generation(self):
        """Test POST /api/fraud/events ingests telemetry and spawns alert on high risk."""
        # 1. Ingest clean event
        res_clean = self.client.post(
            "/api/fraud/events",
            json={
                "user_id": self.seeker_id,
                "event_type": "PAGE_VIEW",
                "severity": "INFO",
                "ip_address": "127.0.0.1",
            },
        )
        self.assertEqual(res_clean.status_code, 201)
        clean_data = res_clean.get_json()["data"]
        self.assertFalse(clean_data["alert_created"])

        # 2. Ingest suspicious event with confirmed policy violation
        res_threat = self.client.post(
            "/api/fraud/events",
            json={
                "user_id": self.host_a_id,
                "event_type": "SUSPICIOUS_ESCROW_DISPUTE",
                "severity": "CRITICAL",
                "device_fingerprint": "blacklisted-fraud-hw-9911",
                "payload": {
                    "blacklisted_device": True,
                    "amount": 45000.0,
                },
            },
        )
        self.assertEqual(res_threat.status_code, 201)
        threat_data = res_threat.get_json()["data"]
        self.assertTrue(threat_data["alert_created"])
        self.assertIsNotNone(threat_data["alert_id"])
        self.assertEqual(threat_data["decision"], "BLOCK")

        # 3. Query alerts via GET /api/fraud/alerts
        res_alerts = self.client.get("/api/fraud/alerts?status=OPEN")
        self.assertEqual(res_alerts.status_code, 200)
        alerts_json = res_alerts.get_json()
        self.assertGreaterEqual(alerts_json["count"], 1)

    def test_system_b_api_realtime_score(self):
        """Test POST /api/fraud/score returns complete evaluation and explainability."""
        res = self.client.post(
            "/api/fraud/score",
            json={
                "user_id": self.seeker_id,
                "amount": 1200.0,
                "ip_address": "49.36.12.100",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("risk_score", data)
        self.assertIn("decision", data)
        self.assertIn("ml_anomaly_score", data)
        self.assertIn("threshold_applied", data)
        self.assertIn("explanation", data)


if __name__ == "__main__":
    unittest.main()
