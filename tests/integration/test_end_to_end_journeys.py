"""End-to-End Multi-Phase Integration Test Suite for SpaceLoop.

Validates the 6 Complete Marketplace Journeys:
1. JOURNEY 1 — SEEKER: Registration -> Email Verification -> Login -> Search -> View -> Check Availability -> Book -> Pay -> PIN Arrival -> Geofenced Check-in -> Space Use -> Checkout -> Inspection -> ₹100 Deposit Refund -> Review
2. JOURNEY 2 — HOST: Registration -> Host Verification (Discom & UPI) -> Listing Creation -> AI Scan -> Publish -> Booking Received -> Accept -> Check-in -> Completion -> Payout -> Trust Score Update
3. JOURNEY 3 — CANCELLATION: Booking -> Cancellation -> Exact Accounting (Keep 5% fee, Refund 100% rental + ₹100 deposit) -> Immutable Ledger
4. JOURNEY 4 — FRAUD: Telemetry Ingestion -> Feature Extraction -> Rule Engine -> Anomaly Detection -> Threshold Disposition (ALLOW/CHALLENGE/HOLD/BLOCK) -> Admin Alerts
5. JOURNEY 5 — AI FAILURE: Complete AI Provider Outage -> Deterministic Search, Parser & LoopBot Fallbacks -> Marketplace Operations 100% Available
6. JOURNEY 6 — PHYSICAL ACCESS: Temporal Guard -> 50m Haversine Geofence -> Rotating QR/PIN -> AccessLog Audit Trail -> Inspection -> Escrow Settlement
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app import create_app
from backend.core.database import db
from backend.modules.auth.tokens import create_access_token
from backend.modules.auth.password import hash_user_password
from config import TestingConfig
from models import (
    AccessLog,
    Booking,
    EscrowTransaction,
    Review,
    Space,
    User,
    utc_now,
)


class EndToEndJourneysTestCase(unittest.TestCase):
    """Complete End-to-End Multi-Phase Integration Suite."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")

        class E2ETestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "e2e-integration-secret-key-32-bytes!"
            RATELIMIT_ENABLED = False

        self.app = create_app(E2ETestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    # -------------------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------------------
    def _create_user(self, email="user@spaceloop.test", role="seeker", is_verified=True, is_admin=False):
        pwd_hash = hash_user_password("SecurePass123!")
        resolved_role = "ADMIN" if is_admin else role
        user = User(
            email=email.lower(),
            password_hash=pwd_hash,
            full_name="Marketplace User",
            role=resolved_role,
            is_verified=is_verified,
            trust_score=100.0,
        )
        db.session.add(user)
        db.session.commit()
        return user

    def _auth_headers(self, user):
        token = create_access_token(user_id=user.id, email=user.email, role=user.role)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _create_space(self, host, price=500.0, lat=19.0760, lng=72.8777):
        space = Space(
            host_id=host.id,
            title="Bandra Quiet Studio",
            description="Creative workspace with high-speed internet and AC.",
            space_type="studio",
            address_line1="Linking Road",
            city="Mumbai",
            state="Maharashtra",
            pincode="400050",
            latitude=lat,
            longitude=lng,
            geofence_radius=50.0,
            price_per_hour=price,
            minimum_hours=1,
            capacity=5,
            amenities=["wifi", "ac", "power_backup"],
            is_active=True,
            is_approved=True,
            created_at=utc_now(),
        )
        db.session.add(space)
        db.session.commit()
        return space

    # -------------------------------------------------------------------------
    # JOURNEY 1 — SEEKER
    # -------------------------------------------------------------------------
    def test_journey_1_seeker_lifecycle(self):
        """Trace Seeker journey: Register -> Verify Email -> Login -> Search -> View -> Precheck -> Book -> Pay -> Checkin (PIN/GPS) -> Use -> Checkout -> Inspection -> Deposit Refund -> Review."""
        # 1. Register
        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": "seeker.aarya@spaceloop.test",
            "password": "StrongPassword123!",
            "full_name": "Aarya Seeker",
            "role": "seeker",
        })
        self.assertEqual(reg_res.status_code, 201)
        data = reg_res.get_json()
        token = data.get("verification_token") or data.get("data", {}).get("verification_token")

        # 2. Verify Email
        verify_res = self.client.post("/api/v1/auth/verify-email", json={"token": token})
        self.assertEqual(verify_res.status_code, 200)

        # 3. Login
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "seeker.aarya@spaceloop.test",
            "password": "StrongPassword123!",
        })
        self.assertEqual(login_res.status_code, 200)
        auth_data = login_res.get_json()
        jwt_token = (
            auth_data.get("token")
            or auth_data.get("access_token")
            or (auth_data.get("data") and auth_data.get("data").get("access_token"))
        )
        headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"}

        # Host & Space Setup
        host = self._create_user(email="host.mumbai@spaceloop.test", role="host")
        space = self._create_space(host, price=500.0, lat=19.0760, lng=72.8777)

        # 4. Search for Space
        search_res = self.client.get("/api/spaces?city=Mumbai")
        self.assertEqual(search_res.status_code, 200)
        spaces = search_res.get_json().get("data", {}).get("items") or search_res.get_json().get("data", {}).get("spaces", [])
        self.assertTrue(any(s["id"] == space.id for s in spaces))

        # 5. View Space Details
        view_res = self.client.get(f"/api/spaces/{space.id}")
        self.assertEqual(view_res.status_code, 200)

        # 6. Check Availability / Pricing Precheck
        now = utc_now()
        start = (now + timedelta(hours=1)).isoformat()
        end = (now + timedelta(hours=3)).isoformat()
        precheck_res = self.client.post("/api/bookings/precheck", json={
            "space_id": space.id,
            "start_time": start,
            "end_time": end,
        }, headers=headers)
        self.assertEqual(precheck_res.status_code, 200)
        precheck_data = precheck_res.get_json().get("data", {})
        self.assertEqual(precheck_data["duration_hours"], 2.0)
        self.assertEqual(precheck_data["subtotal"], 1000.0)
        self.assertEqual(precheck_data["platform_fee"], 50.0) # 5%
        self.assertEqual(precheck_data["escrow_deposit"], 100.0) # ₹100 deposit
        self.assertEqual(precheck_data["final_amount"], 1150.0)

        # 7. Book & Pay (Micro-Escrow creation)
        book_res = self.client.post("/api/bookings", json={
            "space_id": space.id,
            "start_time": start,
            "end_time": end,
            "guest_count": 2,
        }, headers=headers)
        self.assertEqual(book_res.status_code, 201)
        booking = book_res.get_json()
        booking_id = booking.get("id") or booking.get("data", {}).get("id")

        # 8. Receive Arrival PIN
        arrival_pin = booking.get("arrival_pin") or booking.get("data", {}).get("arrival_pin")
        self.assertIsNotNone(arrival_pin)
        self.assertTrue(len(str(arrival_pin)) >= 4)

        # Host confirms booking
        host_headers = self._auth_headers(host)
        accept_res = self.client.post(f"/api/bookings/{booking_id}/accept", headers=host_headers)
        self.assertEqual(accept_res.status_code, 200)

        # 9. Arrive: GPS & PIN Check-in (within 50m geofence, override temporal for unit test)
        checkin_res = self.client.post(f"/api/bookings/{booking_id}/checkin", json={
            "arrival_pin": arrival_pin,
            "lat": 19.07602, # ~2 meters away
            "lng": 72.87771,
            "override_temporal": True,
        }, headers=headers)
        self.assertEqual(checkin_res.status_code, 200)
        checked_in_data = checkin_res.get_json().get("data", {})
        self.assertEqual(checked_in_data["session_state"], "checked_in")

        # 10. Use Space & Checkout with Inspection Photos
        checkout_res = self.client.post(f"/api/bookings/{booking_id}/checkout", json={
            "inspection_photos": ["uploads/inspection_clean_room.jpg"],
        }, headers=headers)
        self.assertEqual(checkout_res.status_code, 200)
        completed_data = checkout_res.get_json().get("data", {})
        self.assertEqual(completed_data["status"], "completed")

        # 11. Escrow Settlement: ₹100 Deposit returned to seeker, rental to host, 5% fee retained
        settle_res = self.client.post(f"/api/escrow/{booking_id}/checkout", json={
            "host_vpa": "host.verified@okaxis",
            "seeker_vpa": "seeker.aarya@okhdfcbank",
        }, headers=headers)
        self.assertEqual(settle_res.status_code, 200)
        settle_data = settle_res.get_json().get("data", {})
        self.assertEqual(settle_data["deposit_returned"], 100.0)
        self.assertEqual(settle_data["host_payout"], 1000.0)
        self.assertEqual(settle_data["platform_fee"], 50.0)

        # 12. Submit Verified Stay Review
        review_res = self.client.post(f"/api/spaces/{space.id}/reviews", json={
            "rating": 5,
            "comment": "Outstanding quiet studio, lightning-fast Wi-Fi!",
            "booking_id": booking_id,
        }, headers=headers)
        self.assertEqual(review_res.status_code, 201)

    # -------------------------------------------------------------------------
    # JOURNEY 2 — HOST
    # -------------------------------------------------------------------------
    def test_journey_2_host_lifecycle(self):
        """Trace Host journey: Register -> Verify Host (Discom/UPI) -> Listing Creation -> AI Space Scan -> Publish -> Booking Received -> Accept -> Check-in -> Completion -> Payout -> Trust Score Update."""
        # 1. Register Host
        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": "host.rohit@spaceloop.test",
            "password": "HostSecurePass123!",
            "full_name": "Rohit Host",
            "role": "host",
        })
        self.assertEqual(reg_res.status_code, 201)
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "host.rohit@spaceloop.test",
            "password": "HostSecurePass123!",
        })
        login_data = login_res.get_json()
        jwt_token = (
            login_data.get("token")
            or login_data.get("access_token")
            or (login_data.get("data") and login_data.get("data").get("access_token"))
        )
        headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"}
        host = User.query.filter_by(email="host.rohit@spaceloop.test").first()

        # 2. Verify Host with Discom Electricity & UPI Penny Drop
        verify_res = self.client.post("/api/verify/host", json={
            "discom_provider": "MSEDCL",
            "consumer_number": "123456789012",
            "upi_vpa": "rohit.host@okaxis",
        }, headers=headers)
        self.assertEqual(verify_res.status_code, 200)
        self.assertTrue(verify_res.get_json().get("data", {}).get("host_verified", False))

        # 3. Create Listing
        listing_res = self.client.post("/api/spaces", json={
            "title": "Versova Art Loft",
            "description": "Spacious sunlit art loft for creative workshops.",
            "space_type": "studio",
            "address_line1": "7 Bungalows",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400061",
            "latitude": 19.1319,
            "longitude": 72.8152,
            "price_per_hour": 750.0,
            "minimum_hours": 2,
            "capacity": 8,
            "amenities": ["natural_light", "easels", "wifi"],
        }, headers=headers)
        self.assertEqual(listing_res.status_code, 201)
        space_id = listing_res.get_json().get("data", {}).get("id")

        # 4. AI-assisted Space Scan
        scan_res = self.client.post("/api/spaces/ai-scan", json={
            "photo_url": "uploads/loft_wide_angle.jpg",
            "space_type": "studio",
        }, headers=headers)
        self.assertIn(scan_res.status_code, [200, 201])

        # 5. Publish Listing
        pub_res = self.client.put(f"/api/spaces/{space_id}", json={"is_active": True}, headers=headers)
        self.assertEqual(pub_res.status_code, 200)

        # Seeker Books Space
        seeker = self._create_user(email="guest.art@spaceloop.test", role="seeker")
        seeker_headers = self._auth_headers(seeker)
        start = (utc_now() + timedelta(hours=2)).isoformat()
        end = (utc_now() + timedelta(hours=5)).isoformat() # 3 hours = ₹2250

        book_res = self.client.post("/api/bookings", json={
            "space_id": space_id,
            "start_time": start,
            "end_time": end,
        }, headers=seeker_headers)
        self.assertEqual(book_res.status_code, 201)
        booking = book_res.get_json()
        b_id = booking.get("id") or booking.get("data", {}).get("id")
        arrival_pin = booking.get("arrival_pin") or booking.get("data", {}).get("arrival_pin")

        # 6. Host Receives Booking & Accepts
        accept_res = self.client.post(f"/api/bookings/{b_id}/accept", headers=headers)
        self.assertEqual(accept_res.status_code, 200)

        # 7. Check-in & Session Completes
        self.client.post(f"/api/bookings/{b_id}/checkin", json={
            "arrival_pin": arrival_pin,
            "lat": 19.1319,
            "lng": 72.8152,
            "override_temporal": True,
        }, headers=seeker_headers)

        self.client.post(f"/api/bookings/{b_id}/checkout", json={}, headers=seeker_headers)

        # 8. Host Receives Payout Settlement
        settle_res = self.client.post(f"/api/escrow/{b_id}/checkout", headers=headers)
        self.assertEqual(settle_res.status_code, 200)
        self.assertEqual(settle_res.get_json().get("data", {}).get("host_payout"), 2250.0)

        # 9. Review Submitted & Trust Score Updated
        rev_res = self.client.post(f"/api/spaces/{space_id}/reviews", json={
            "rating": 5,
            "comment": "Inspiring loft!",
            "booking_id": b_id,
        }, headers=seeker_headers)
        self.assertEqual(rev_res.status_code, 201)

        # Verify host trust score updated
        host_refreshed = db.session.get(User, host.id)
        self.assertGreaterEqual(host_refreshed.trust_score, 100.0)

    # -------------------------------------------------------------------------
    # JOURNEY 3 — CANCELLATION
    # -------------------------------------------------------------------------
    def test_journey_3_cancellation_lifecycle(self):
        """Trace Cancellation: Book -> Cancel -> Retain exactly 5% fee -> Return rental + ₹100 deposit -> Immutable Ledger."""
        host = self._create_user(email="host.cancel@spaceloop.test", role="host")
        space = self._create_space(host, price=1000.0)
        seeker = self._create_user(email="seeker.cancel@spaceloop.test", role="seeker")
        seeker_headers = self._auth_headers(seeker)

        # 1. Create Booking (2 hours = ₹2000 subtotal, ₹100 fee (5%), ₹100 deposit, total = ₹2200)
        start = (utc_now() + timedelta(hours=3)).isoformat()
        end = (utc_now() + timedelta(hours=5)).isoformat()
        book_res = self.client.post("/api/bookings", json={
            "space_id": space.id,
            "start_time": start,
            "end_time": end,
        }, headers=seeker_headers)
        self.assertEqual(book_res.status_code, 201)
        booking = book_res.get_json()
        b_id = booking.get("id") or booking.get("data", {}).get("id")

        # 2. Cancel Booking
        cancel_res = self.client.post(f"/api/bookings/{b_id}/cancel", json={
            "reason": "Change of plans for travel.",
        }, headers=seeker_headers)
        self.assertEqual(cancel_res.status_code, 200)

        # 3. Verify Exact Accounting in Escrow
        escrow_res = self.client.get(f"/api/escrow/{b_id}", headers=seeker_headers)
        self.assertEqual(escrow_res.status_code, 200)
        escrow_data = escrow_res.get_json().get("data", {})
        self.assertEqual(escrow_data["escrow_status"], "refunded")

        # Seeker receives: 100% rental (₹2000) + 100% deposit (₹100) = ₹2100
        ledger = escrow_data.get("ledger_transactions", [])
        refund_tx = next((tx for tx in ledger if tx["transaction_type"] == "refund"), None)
        fee_tx = next((tx for tx in ledger if tx["transaction_type"] == "fee"), None)

        self.assertIsNotNone(refund_tx)
        self.assertEqual(refund_tx["amount"], 2100.0) # Subtotal + deposit returned to seeker

        self.assertIsNotNone(fee_tx)
        self.assertEqual(fee_tx["amount"], 100.0) # Exactly 5% platform fee retained

        # 4. Double refund protection
        duplicate_cancel = self.client.post(f"/api/bookings/{b_id}/cancel", headers=seeker_headers)
        self.assertIn(duplicate_cancel.status_code, [400, 409])

    # -------------------------------------------------------------------------
    # JOURNEY 4 — FRAUD
    # -------------------------------------------------------------------------
    def test_journey_4_fraud_lifecycle(self):
        """Trace Fraud Intelligence: Activity Telemetry -> Feature Extraction -> Rule Engine -> Anomaly Detection -> Scoring -> Disposition -> Admin Alert."""
        host = self._create_user(email="fraud.host@spaceloop.test", role="host")
        seeker = self._create_user(email="fraud.seeker@spaceloop.test", role="seeker")

        # 1. Ingest Normal Telemetry
        event_res = self.client.post("/api/fraud/events", json={
            "event_type": "BOOKING_REQUEST",
            "user_id": seeker.id,
            "ip_address": "49.36.120.15",
            "device_fingerprint": "dev-mac-001",
            "amount": 500.0,
        })
        self.assertEqual(event_res.status_code, 201)

        # 2. Score Normal Transaction (Should be ALLOW)
        score_normal = self.client.post("/api/fraud/score", json={
            "user_id": seeker.id,
            "amount": 500.0,
            "ip_address": "49.36.120.15",
            "device_fingerprint": "dev-mac-001",
        })
        self.assertEqual(score_normal.status_code, 200)
        res_norm = score_normal.get_json().get("data", {})
        self.assertEqual(res_norm["decision"], "ALLOW")
        self.assertLess(res_norm["risk_score"], 0.40)

        # 3. Score Critical Collusion / Self-Booking (Should trigger BLOCK / HOLD)
        score_collusion = self.client.post("/api/fraud/score", json={
            "user_id": host.id,
            "host_id": host.id, # Self-booking pattern
            "amount": 95000.0, # Massive amount anomaly
            "velocity_last_hour": 15, # Velocity spike
            "shared_ip_with_host": True,
            "shared_device_with_host": True,
        })
        self.assertEqual(score_collusion.status_code, 200)
        res_coll = score_collusion.get_json().get("data", {})
        self.assertIn(res_coll["decision"], ["BLOCK", "HOLD / REVIEW", "CHALLENGE / MFA / KYC"])
        self.assertGreaterEqual(res_coll["risk_score"], 0.50)
        self.assertTrue(len(res_coll["triggered_rules"]) > 0)
        self.assertIn("explanation", res_coll)

        # 4. Admin Queries Actionable Alerts
        alerts_res = self.client.get("/api/fraud/alerts")
        self.assertEqual(alerts_res.status_code, 200)
        self.assertIn("alerts", alerts_res.get_json())

    # -------------------------------------------------------------------------
    # JOURNEY 5 — AI FAILURE RESILIENCE
    # -------------------------------------------------------------------------
    def test_journey_5_ai_failure_resilience(self):
        """Trace AI Failure Resilience: With Groq & Gemini disabled, Search, Matching, Booking, and LoopBot continue operating seamlessly."""
        host = self._create_user(email="ai.host@spaceloop.test", role="host")
        space = self._create_space(host, price=600.0)

        # Force external AI services to fail
        with patch.dict(os.environ, {"GROQ_API_KEY": "", "GEMINI_API_KEY": ""}):
            # 1. Search with natural language query in Hindi/Hinglish
            search_res = self.client.get("/api/spaces/search?q=Mumbai+Bandra+quiet+studio")
            self.assertEqual(search_res.status_code, 200)
            items = search_res.get_json().get("data", {}).get("items") or search_res.get_json().get("data", {}).get("spaces", [])
            self.assertTrue(len(items) > 0)

            # 2. LoopBot Chat with Multi-lingual Deterministic Fallback
            chat_hi = self.client.post("/api/ai/chat", json={
                "message": "मुझे मुंबई में शांतिपूर्ण वर्कस्पेस चाहिए", # Hindi query
            })
            self.assertEqual(chat_hi.status_code, 200)
            chat_hi_data = chat_hi.get_json()
            self.assertEqual(chat_hi_data.get("provider"), "deterministic")
            self.assertIn("response", chat_hi_data)
            self.assertTrue(len(chat_hi_data["response"]) > 10)

            # 3. Direct LoopBot Pricing Policy Query
            chat_policy = self.client.post("/api/ai/chat", json={
                "message": "What is the cancellation refund and deposit policy?",
            })
            self.assertEqual(chat_policy.status_code, 200)
            policy_resp = chat_policy.get_json().get("response", "")
            self.assertIn("5%", policy_resp)
            self.assertIn("100", policy_resp)

            # 4. Booking still completes with zero failure
            seeker = self._create_user(email="ai.seeker@spaceloop.test", role="seeker")
            seeker_headers = self._auth_headers(seeker)
            start = (utc_now() + timedelta(hours=4)).isoformat()
            end = (utc_now() + timedelta(hours=6)).isoformat()
            book_res = self.client.post("/api/bookings", json={
                "space_id": space.id,
                "start_time": start,
                "end_time": end,
            }, headers=seeker_headers)
            self.assertEqual(book_res.status_code, 201)

    # -------------------------------------------------------------------------
    # JOURNEY 6 — PHYSICAL ACCESS & GEOFENCING
    # -------------------------------------------------------------------------
    def test_journey_6_physical_access_geofencing(self):
        """Trace Physical Access: 15-minute temporal window guard, 50m Haversine radius, Rotating PIN, AccessLog audit, Inspection & Settlement."""
        host = self._create_user(email="geo.host@spaceloop.test", role="host")
        space = self._create_space(host, price=500.0, lat=19.076000, lng=72.877700) # Exact point
        seeker = self._create_user(email="geo.seeker@spaceloop.test", role="seeker")
        seeker_headers = self._auth_headers(seeker)
        host_headers = self._auth_headers(host)

        # 1. Create and confirm booking
        start_time = utc_now() + timedelta(hours=2) # 2 hours in the future
        end_time = start_time + timedelta(hours=2)
        book_res = self.client.post("/api/bookings", json={
            "space_id": space.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }, headers=seeker_headers)
        self.assertEqual(book_res.status_code, 201)
        booking = book_res.get_json()
        b_id = booking.get("id") or booking.get("data", {}).get("id")
        arrival_pin = booking.get("arrival_pin") or booking.get("data", {}).get("arrival_pin")

        # Confirm booking
        self.client.post(f"/api/bookings/{b_id}/accept", headers=host_headers)

        # 2. Check-in Too Early (>15 mins before start)
        early_res = self.client.post(f"/api/bookings/{b_id}/checkin", json={
            "arrival_pin": arrival_pin,
            "lat": 19.076000,
            "lng": 72.877700,
            "override_temporal": False,
        }, headers=seeker_headers)
        self.assertEqual(early_res.status_code, 400)
        self.assertIn("15 minutes", early_res.get_json().get("error", {}).get("message", ""))

        # Verify DENIED_TIME access log
        early_log = AccessLog.query.filter_by(booking_id=b_id, status="DENIED_TIME").first()
        self.assertIsNotNone(early_log)

        # 3. Check-in with Wrong PIN
        wrong_pin_res = self.client.post(f"/api/bookings/{b_id}/checkin", json={
            "arrival_pin": "999999", # Incorrect PIN
            "lat": 19.076000,
            "lng": 72.877700,
            "override_temporal": True,
        }, headers=seeker_headers)
        self.assertEqual(wrong_pin_res.status_code, 400)
        self.assertIn("Invalid arrival PIN", wrong_pin_res.get_json().get("error", {}).get("message", ""))

        # Verify DENIED_CREDENTIAL access log
        cred_log = AccessLog.query.filter_by(booking_id=b_id, status="DENIED_CREDENTIAL").first()
        self.assertIsNotNone(cred_log)

        # 4. Check-in Far Outside 50m Geofence (e.g. 500m away)
        far_res = self.client.post(f"/api/bookings/{b_id}/checkin", json={
            "arrival_pin": arrival_pin,
            "lat": 19.081000, # ~550 meters away
            "lng": 72.877700,
            "override_temporal": True,
            "override_geofence": False,
        }, headers=seeker_headers)
        self.assertEqual(far_res.status_code, 403)
        self.assertIn("Location verification failed", far_res.get_json().get("error", {}).get("message", ""))

        # Verify DENIED_LOCATION access log
        loc_log = AccessLog.query.filter_by(booking_id=b_id, status="DENIED_LOCATION").first()
        self.assertIsNotNone(loc_log)
        self.assertGreater(loc_log.distance_meters, 50.0)

        # 5. Legitimate Check-in Within 50m
        valid_res = self.client.post(f"/api/bookings/{b_id}/checkin", json={
            "arrival_pin": arrival_pin,
            "lat": 19.076015, # ~2 meters away
            "lng": 72.877705,
            "override_temporal": True,
        }, headers=seeker_headers)
        self.assertEqual(valid_res.status_code, 200)

        # Verify GRANTED access log
        granted_log = AccessLog.query.filter_by(booking_id=b_id, status="GRANTED").first()
        self.assertIsNotNone(granted_log)
        self.assertLessEqual(granted_log.distance_meters, 50.0)

        # 6. Checkout with Inspection Photos
        checkout_res = self.client.post(f"/api/bookings/{b_id}/checkout", json={
            "inspection_photos": ["uploads/checkout_inspection_01.jpg"],
        }, headers=seeker_headers)
        self.assertEqual(checkout_res.status_code, 200)

        # 7. Escrow Settlement
        settle_res = self.client.post(f"/api/escrow/{b_id}/checkout", headers=seeker_headers)
        self.assertEqual(settle_res.status_code, 200)
        self.assertEqual(settle_res.get_json().get("data", {}).get("deposit_returned"), 100.0)


if __name__ == "__main__":
    unittest.main()
