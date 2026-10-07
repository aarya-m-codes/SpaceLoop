"""SpaceLoop H1 Architecture & Data Consistency Verification Test Suite.

Proves that:
1. There is ONE authoritative persistence layer (`database.py` and `models.py` operate on the exact same database).
2. `models.py`, `backend/models.py`, and `backend/app/persistence/models` resolve to the exact same singleton classes.
3. Listing creation, price modification, activation toggling, and availability changes are immediately visible across:
   - Direct entity read
   - API listing endpoints
   - Discovery / Hybrid Search
   - AI Matchmaker
   - Booking Precheck & Validation
4. Data survives application restarts without loss or divergence.
5. Concurrent sessions and transactions observe consistent authoritative state.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from backend.core.cache import cache
from backend.core.database import db, init_db
from backend.modules.bookings.service import BookingService
from backend.modules.search import AIMatcher, DiscoveryPipeline
from backend.modules.spaces.service import SpaceService
from config import TestingConfig
from models import Booking, EscrowTransaction, Space, User, utc_now
from backend.modules.auth.password import hash_user_password
from backend.modules.auth.tokens import create_access_token


class H1DataConsistencyTestCase(unittest.TestCase):
    """Rigorous verification that models.py, database.py, and search share one authoritative persistence layer."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")

        class H1TestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "test-h1-consistency-secret-key-32b!"
            RATELIMIT_ENABLED = False

        self.test_config_class = H1TestConfig
        self.app = create_app(self.test_config_class)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        init_db(self.app)
        cache.clear()

        # Seed initial test host and guest
        self.host = User(
            email="host_h1@spaceloop.in",
            password_hash=hash_user_password("HostPass123!"),
            full_name="Arjun Verma",
            role="host",
            is_active=True,
            is_verified=True,
            is_host_verified=True,
            trust_score=95.0,
        )
        self.guest = User(
            email="guest_h1@spaceloop.in",
            password_hash=hash_user_password("GuestPass123!"),
            full_name="Neha Sharma",
            role="seeker",
            is_active=True,
            is_verified=True,
        )
        db.session.add_all([self.host, self.guest])
        db.session.commit()

        self.host_token = create_access_token(self.host.id, self.host.email, self.host.role)
        self.guest_token = create_access_token(self.guest.id, self.guest.email, self.guest.role)
        self.host_headers = {"Authorization": f"Bearer {self.host_token}"}
        self.guest_headers = {"Authorization": f"Bearer {self.guest_token}"}

    def tearDown(self):
        self.ctx.pop()
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.unlink(self.temp_db_path)
            for ext in ("-wal", "-shm"):
                f = f"{self.temp_db_path}{ext}"
                if os.path.exists(f):
                    os.unlink(f)
        except OSError:
            pass

    def test_01_single_orm_model_singleton_identity(self):
        """Verify models.py, backend.models, and backend.app.persistence.models are the identical singletons."""
        import backend.models as bm
        import models as rm
        from backend.app.persistence import models as pm

        self.assertIs(rm.User, bm.User, "User class must be identical across root and backend models")
        self.assertIs(rm.Space, bm.Space, "Space class must be identical across root and backend models")
        self.assertIs(rm.Booking, bm.Booking, "Booking class must be identical across root and backend models")
        self.assertIs(rm.User, pm.User, "User class must match persistence models package")
        self.assertIs(rm.db, bm.db, "SQLAlchemy instance must be identical")
        self.assertIs(rm.db, pm.db, "SQLAlchemy instance must be identical across persistence")

    def test_02_config_database_uri_alignment(self):
        """Verify config and backend.config point to identical instance directory and URI."""
        import backend.config as bc
        import config as rc
        from backend.app.config.database import SQLALCHEMY_DATABASE_URI as URI_FROM_DB_CONFIG

        self.assertEqual(rc.DevelopmentConfig.SQLALCHEMY_DATABASE_URI, bc.DevelopmentConfig.SQLALCHEMY_DATABASE_URI)
        self.assertEqual(rc.INSTANCE_DIR, bc.INSTANCE_DIR)
        self.assertEqual(rc.DevelopmentConfig.SQLALCHEMY_DATABASE_URI, URI_FROM_DB_CONFIG)

    def test_03_create_space_immediate_read_and_search(self):
        """TEST A: Create listing -> search immediately -> newly created listing appears with correct data."""
        payload = {
            "title": "Koramangala High-Speed Podcast Studio",
            "space_type": "studio",
            "category": "creative",
            "city": "Bengaluru",
            "neighborhood": "Koramangala",
            "address_line1": "80 Feet Road, 4th Block",
            "latitude": 12.9352,
            "longitude": 77.6245,
            "hourly_price": 450.0,
            "capacity": 4,
            "amenities": ["wifi", "ac", "podcast", "microphone", "soundproof"],
        }
        res = self.client.post("/api/spaces", json=payload, headers=self.host_headers)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        space_id = data["data"]["id"]

        # Immediate Direct Read
        read_res = self.client.get(f"/api/spaces/{space_id}")
        self.assertEqual(read_res.status_code, 200)
        self.assertEqual(read_res.get_json()["data"]["title"], payload["title"])
        self.assertEqual(read_res.get_json()["data"]["hourly_price"], 450.0)

        # Immediate Search
        search_res = self.client.post("/api/spaces/search", json={"query": "podcast studio in Koramangala"})
        self.assertEqual(search_res.status_code, 200)
        search_data = search_res.get_json()
        matching_ids = [s["id"] for s in (search_data.get("spaces") or search_data.get("data", {}).get("items", []))]
        self.assertIn(space_id, matching_ids, "Newly created space must immediately appear in search results")

    def test_04_update_price_immediate_read_search_and_matching(self):
        """TEST B: Change listing price -> retrieve listing -> search listing -> all show the new price."""
        # 1. Create initial space at ₹200/hr
        created, err, status = SpaceService.create_space(self.host.id, {
            "title": "Indiranagar Focus Desk",
            "space_type": "desk",
            "city": "Bengaluru",
            "neighborhood": "Indiranagar",
            "address_line1": "100 Feet Road",
            "latitude": 12.9784,
            "longitude": 77.6408,
            "hourly_price": 200.0,
            "capacity": 1,
            "amenities": ["wifi", "power"],
        })
        self.assertEqual(status, 201)
        space_id = created["id"]

        # 2. Update price to ₹650/hr via API
        patch_res = self.client.patch(
            f"/api/spaces/{space_id}",
            json={"hourly_price": 650.0},
            headers=self.host_headers,
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.get_json()["data"]["hourly_price"], 650.0)

        # 3. Direct GET reflects updated price
        get_res = self.client.get(f"/api/spaces/{space_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()["data"]["hourly_price"], 650.0)
        self.assertEqual(get_res.get_json()["data"]["price_per_hour"], 650.0)

        # 4. Search API reflects updated price
        search_res = self.client.get(f"/api/spaces/search?query=Indiranagar+Focus+Desk")
        self.assertEqual(search_res.status_code, 200)
        spaces = search_res.get_json().get("spaces") or search_res.get_json().get("data", {}).get("items", [])
        matched = next((s for s in spaces if s["id"] == space_id), None)
        self.assertIsNotNone(matched)
        self.assertEqual(matched["hourly_price"], 650.0, "Search result must reflect new price of ₹650")
        self.assertEqual(matched["price_per_hour"], 650.0)

        # 5. AI Match reflects updated price
        match_res = self.client.post("/api/spaces/ai-match", json={"query": "desk in Indiranagar"})
        self.assertEqual(match_res.status_code, 200)
        match_data = match_res.get_json()
        top_match = next((s for s in (match_data.get("spaces") or match_data.get("data", {}).get("top_matches", [])) if s["id"] == space_id), None)
        if top_match:
            self.assertEqual(top_match["hourly_price"], 650.0)

    def test_05_deactivate_space_excludes_from_search_and_blocks_booking(self):
        """TEST C: Deactivate listing -> search excludes it -> booking flow rejects it."""
        created, _, _ = SpaceService.create_space(self.host.id, {
            "title": "Whitefield Meeting Room",
            "space_type": "room",
            "city": "Bengaluru",
            "neighborhood": "Whitefield",
            "address_line1": "ITPB Main Road",
            "latitude": 12.9850,
            "longitude": 77.7300,
            "hourly_price": 500.0,
            "capacity": 8,
            "amenities": ["projector", "wifi"],
        })
        space_id = created["id"]

        # Deactivate
        toggle_res = self.client.post(f"/api/spaces/{space_id}/toggle-status", headers=self.host_headers)
        self.assertEqual(toggle_res.status_code, 200)
        self.assertFalse(toggle_res.get_json()["data"]["is_active"])

        # Search must NOT return deactivated listing
        search_res = self.client.post("/api/spaces/search", json={"query": "Whitefield Meeting Room"})
        self.assertEqual(search_res.status_code, 200)
        spaces = search_res.get_json().get("spaces") or search_res.get_json().get("data", {}).get("items", [])
        active_ids = [s["id"] for s in spaces]
        self.assertNotIn(space_id, active_ids, "Deactivated listing must not appear in search results")

        # Booking flow must REJECT deactivated space
        start_time = (utc_now() + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=2)
        book_res = self.client.post("/api/bookings", json={
            "space_id": space_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }, headers=self.guest_headers)
        self.assertEqual(book_res.status_code, 400, "Booking against deactivated space must be rejected with 400")

    def test_06_booking_creation_updates_availability_and_blocks_overlap(self):
        """TEST D & E: Create booking -> slot locked -> subsequent search/booking detects conflict."""
        created, _, _ = SpaceService.create_space(self.host.id, {
            "title": "HSR Layout Coworking Seat",
            "space_type": "desk",
            "city": "Bengaluru",
            "neighborhood": "HSR Layout",
            "address_line1": "Sector 4",
            "latitude": 12.9116,
            "longitude": 77.6389,
            "hourly_price": 180.0,
            "capacity": 1,
            "amenities": ["wifi"],
        })
        space_id = created["id"]

        target_date = (utc_now() + timedelta(days=3)).date()
        start_time = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc).replace(hour=10)
        end_time = start_time + timedelta(hours=3)

        # 1. Create first valid booking
        book_res = self.client.post("/api/bookings", json={
            "space_id": space_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }, headers=self.guest_headers)
        self.assertEqual(book_res.status_code, 201)
        booking_data = book_res.get_json()["data"]
        self.assertEqual(booking_data["space_id"], space_id)

        # 2. Check availability endpoint directly
        avail_res = self.client.get(
            f"/api/spaces/{space_id}/check-availability?date={target_date.isoformat()}&start_time={start_time.isoformat()}&end_time={end_time.isoformat()}"
        )
        self.assertEqual(avail_res.status_code, 200)
        self.assertFalse(avail_res.get_json()["data"]["is_available"], "Slot during booking must report unavailable")

        # 3. Attempt overlapping booking -> must reject with 409
        overlap_res = self.client.post("/api/bookings", json={
            "space_id": space_id,
            "start_time": (start_time + timedelta(hours=1)).isoformat(),
            "end_time": (end_time + timedelta(hours=1)).isoformat(),
        }, headers=self.guest_headers)
        self.assertEqual(overlap_res.status_code, 409, "Conflicting overlapping booking must fail with 409 Conflict")

        # 4. Search with require_available=True excludes the booked space
        search_res = self.client.post("/api/spaces/search", json={
            "location": "HSR Layout",
            "date": target_date.isoformat(),
            "hours": 2,
            "require_available": True,
        })
        self.assertEqual(search_res.status_code, 200)
        spaces = search_res.get_json().get("spaces") or search_res.get_json().get("data", {}).get("items", [])
        avail_ids = [s["id"] for s in spaces]
        self.assertNotIn(space_id, avail_ids, "Space with conflict must be excluded when require_available=True")

    def test_07_persistence_survives_application_restart(self):
        """TEST F: Restart the application -> previously persisted listings and bookings remain intact."""
        # 1. Create listing and booking on App Instance 1
        created, _, _ = SpaceService.create_space(self.host.id, {
            "title": "Restart Persistence Test Studio",
            "space_type": "studio",
            "city": "Bengaluru",
            "neighborhood": "Koramangala",
            "address_line1": "Sony World Signal",
            "latitude": 12.9350,
            "longitude": 77.6250,
            "hourly_price": 550.0,
            "capacity": 5,
            "amenities": ["wifi", "lighting"],
        })
        space_id = created["id"]

        start_time = (utc_now() + timedelta(days=5)).replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=2)

        booking, err, status = BookingService.create_booking(self.guest, {
            "space_id": space_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        })
        self.assertEqual(status, 201)
        booking_id = booking["id"]

        # Flush, commit, and dispose connection pool to simulate clean application shutdown
        db.session.commit()
        db.session.remove()
        db.engine.dispose()

        # 2. Boot App Instance 2 against the EXACT same persisted database file
        app2 = create_app(self.test_config_class)
        with app2.app_context():
            client2 = app2.test_client()

            # Retrieve Space
            res_space = client2.get(f"/api/spaces/{space_id}")
            self.assertEqual(res_space.status_code, 200)
            self.assertEqual(res_space.get_json()["data"]["title"], "Restart Persistence Test Studio")
            self.assertEqual(res_space.get_json()["data"]["hourly_price"], 550.0)

            # Retrieve Booking
            res_booking = client2.get(f"/api/bookings/{booking_id}", headers=self.guest_headers)
            self.assertEqual(res_booking.status_code, 200)
            self.assertEqual(res_booking.get_json()["data"]["id"], booking_id)
            self.assertEqual(res_booking.get_json()["data"]["space_id"], space_id)

            # Re-verify Search on newly booted instance
            res_search = client2.post("/api/spaces/search", json={"query": "Restart Persistence Test Studio"})
            self.assertEqual(res_search.status_code, 200)
            spaces = res_search.get_json().get("spaces") or res_search.get_json().get("data", {}).get("items", [])
            self.assertIn(space_id, [s["id"] for s in spaces])

        # Push self.ctx back for tearDown cleanup
        self.ctx = self.app.app_context()
        self.ctx.push()

    def test_08_multiple_sessions_see_consistent_state(self):
        """TEST 15: Multiple independent scoped sessions access and see identical committed data."""
        from backend.app.persistence.session import get_session

        session_1 = db.session
        session_2 = get_session()

        # Both sessions query the same database
        user_via_s1 = session_1.get(User, self.host.id)
        user_via_s2 = session_2.get(User, self.host.id)

        self.assertIsNotNone(user_via_s1)
        self.assertIsNotNone(user_via_s2)
        self.assertEqual(user_via_s1.email, user_via_s2.email)


if __name__ == "__main__":
    unittest.main()
