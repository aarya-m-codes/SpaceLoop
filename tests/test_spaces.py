import io
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from backend.core.cache import cache
from backend.core.database import db, init_db
from config import TestingConfig
from models import Booking, Review, Space, User, utc_now
from security import hash_password


class SpacesTestCase(unittest.TestCase):
    """Test suite for SpaceLoop physical-space marketplace endpoints and business rules."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")

        class SpaceTestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "test-spaces-secret-key-32-bytes!"

        self.app = create_app(SpaceTestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db(self.app)
            cache.clear()

            # Create Host 1
            self.host = User(
                email="host1@spaceloop.in",
                password_hash=hash_password("HostPassword#2026"),
                full_name="Vikram Seth",
                role="host",
                is_active=True,
                is_verified=True,
                trust_score=100.0,
            )
            # Create Host 2 (for unauthorized edit tests)
            self.host2 = User(
                email="host2@spaceloop.in",
                password_hash=hash_password("HostPassword#2026"),
                full_name="Kavita Rao",
                role="host",
                is_active=True,
                is_verified=True,
                trust_score=100.0,
            )
            # Create Guest
            self.guest = User(
                email="guest1@spaceloop.in",
                password_hash=hash_password("GuestPassword#2026"),
                full_name="Rohan Mehra",
                role="seeker",
                is_active=True,
                is_verified=True,
            )
            # Create Admin
            self.admin = User(
                email="admin@spaceloop.in",
                password_hash=hash_password("AdminPassword#2026"),
                full_name="Admin User",
                role="admin",
                is_active=True,
                is_verified=True,
            )

            db.session.add_all([self.host, self.host2, self.guest, self.admin])
            db.session.commit()

            self.host_id = self.host.id
            self.host2_id = self.host2.id
            self.guest_id = self.guest.id
            self.admin_id = self.admin.id

        # Obtain auth tokens
        self.host_token = self._login_and_get_token("host1@spaceloop.in", "HostPassword#2026")
        self.host2_token = self._login_and_get_token("host2@spaceloop.in", "HostPassword#2026")
        self.guest_token = self._login_and_get_token("guest1@spaceloop.in", "GuestPassword#2026")
        self.admin_token = self._login_and_get_token("admin@spaceloop.in", "AdminPassword#2026")

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
                os.unlink(self.temp_db_path)
            for ext in ("-wal", "-shm"):
                f = f"{self.temp_db_path}{ext}"
                if os.path.exists(f):
                    os.unlink(f)
        except OSError:
            pass

    def _sample_space_payload(self) -> dict:
        return {
            "title": "Indiranagar High-Speed Desk",
            "description": "Ergonomic workspace with high-speed fiber internet in 100ft Rd.",
            "category": "commercial",
            "space_type": "desk",
            "hourly_price": 150.0,
            "minimum_hours": 2,
            "location": "100 Feet Road, Indiranagar",
            "neighborhood": "Indiranagar",
            "city": "Bengaluru",
            "latitude": 12.9784,
            "longitude": 77.6408,
            "sqft": 450.0,
            "capacity": 8,
            "amenities": ["High-Speed WiFi", "Ergonomic Chairs", "Power Backup"],
            "rules": "Quiet hours after 6 PM.",
            "geofence_radius": 50.0,
            "physical_access_type": "smart_lock",
        }

    def test_create_space_and_validation(self):
        """1. Verify space creation, validation, AI fallback attributes, and QR token."""
        # Missing title or too short
        bad_payload = self._sample_space_payload()
        bad_payload["title"] = "ab"
        res_bad_title = self.client.post(
            "/api/spaces",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json=bad_payload,
        )
        self.assertEqual(res_bad_title.status_code, 400)
        self.assertIn("Title must be between", res_bad_title.get_json()["error"]["message"])

        # Invalid price (<= 0)
        bad_payload = self._sample_space_payload()
        bad_payload["hourly_price"] = 0
        res_bad_price = self.client.post(
            "/api/spaces",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json=bad_payload,
        )
        self.assertEqual(res_bad_price.status_code, 400)

        # Invalid capacity (< 1)
        bad_payload = self._sample_space_payload()
        bad_payload["capacity"] = 0
        res_bad_cap = self.client.post(
            "/api/spaces",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json=bad_payload,
        )
        self.assertEqual(res_bad_cap.status_code, 400)

        # Invalid coordinates (lat > 90)
        bad_payload = self._sample_space_payload()
        bad_payload["latitude"] = 95.0
        res_bad_coord = self.client.post(
            "/api/spaces",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json=bad_payload,
        )
        self.assertEqual(res_bad_coord.status_code, 400)

        # Successful creation
        good_payload = self._sample_space_payload()
        res = self.client.post(
            "/api/spaces",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json=good_payload,
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["data"]
        self.assertEqual(data["title"], "Indiranagar High-Speed Desk")
        self.assertEqual(data["city"], "Bengaluru")
        self.assertEqual(data["hourly_price"], 150.0)
        self.assertEqual(data["minimum_hours"], 2)
        self.assertEqual(data["capacity"], 8)
        self.assertIn("ROOM-", data["room_qr_token"])
        self.assertTrue(data["active_status"])

        # Check AI-derived attributes exist (even without API key)
        self.assertIsNotNone(data["ai_lighting"])
        self.assertIsNotNone(data["ai_noise_level"])
        self.assertIsNotNone(data["ai_power_access"])
        self.assertGreater(len(data["recommended_uses"]), 0)

    def test_public_discovery_and_filtering(self):
        """2. Verify public discovery without auth and faceted query filters."""
        # Create spaces in different cities
        p1 = self._sample_space_payload()
        p1["city"] = "Bengaluru"
        p1["hourly_price"] = 150.0
        self.client.post("/api/spaces", headers={"Authorization": f"Bearer {self.host_token}"}, json=p1)

        p2 = self._sample_space_payload()
        p2["title"] = "BKC Executive Meeting Room"
        p2["city"] = "Mumbai"
        p2["space_type"] = "meeting_room"
        p2["hourly_price"] = 500.0
        self.client.post("/api/spaces", headers={"Authorization": f"Bearer {self.host_token}"}, json=p2)

        # Public list without auth
        res_all = self.client.get("/api/spaces")
        self.assertEqual(res_all.status_code, 200)
        self.assertEqual(res_all.get_json()["data"]["total"], 2)

        # Filter by city
        res_blr = self.client.get("/api/spaces?city=Bengaluru")
        self.assertEqual(res_blr.status_code, 200)
        self.assertEqual(res_blr.get_json()["data"]["total"], 1)
        self.assertEqual(res_blr.get_json()["data"]["items"][0]["city"], "Bengaluru")

        # Filter by price max
        res_price = self.client.get("/api/spaces?max_price=200")
        self.assertEqual(res_price.status_code, 200)
        self.assertEqual(res_price.get_json()["data"]["total"], 1)

    def test_owner_only_editing(self):
        """3. Verify owner-only editing and unauthorized modification prevention."""
        # Create space under host 1
        create_res = self.client.post(
            "/api/spaces",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json=self._sample_space_payload(),
        )
        space_id = create_res.get_json()["data"]["id"]

        # Attempt to edit as Host 2 (different owner) -> 403 Forbidden
        hack_res = self.client.put(
            f"/api/spaces/{space_id}",
            headers={"Authorization": f"Bearer {self.host2_token}"},
            json={"title": "Hacked Title"},
        )
        self.assertEqual(hack_res.status_code, 403)

        # Attempt to edit unauthenticated -> 401
        anon_client = self.app.test_client()
        anon_res = anon_client.put(f"/api/spaces/{space_id}", json={"title": "Anon Edit"})
        self.assertEqual(anon_res.status_code, 401)

        # Owner edit succeeds
        edit_res = self.client.put(
            f"/api/spaces/{space_id}",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json={"title": "Updated Title by Owner", "hourly_price": 220.0},
        )
        self.assertEqual(edit_res.status_code, 200)
        self.assertEqual(edit_res.get_json()["data"]["title"], "Updated Title by Owner")
        self.assertEqual(edit_res.get_json()["data"]["hourly_price"], 220.0)

    def test_owner_only_toggle_status(self):
        """4. Verify owner-only activation and deactivation toggle."""
        create_res = self.client.post(
            "/api/spaces",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json=self._sample_space_payload(),
        )
        space_id = create_res.get_json()["data"]["id"]

        # Host 2 cannot toggle Host 1's listing
        bad_toggle = self.client.post(
            f"/api/spaces/{space_id}/toggle-status",
            headers={"Authorization": f"Bearer {self.host2_token}"},
        )
        self.assertEqual(bad_toggle.status_code, 403)

        # Owner toggles to inactive
        togg1 = self.client.post(
            f"/api/spaces/{space_id}/toggle-status",
            headers={"Authorization": f"Bearer {self.host_token}"},
        )
        self.assertEqual(togg1.status_code, 200)
        self.assertFalse(togg1.get_json()["data"]["is_active"])

        # Inactive space is omitted from public discovery list
        pub_list = self.client.get("/api/spaces")
        self.assertEqual(pub_list.get_json()["data"]["total"], 0)

        # Owner toggles back to active
        togg2 = self.client.post(
            f"/api/spaces/{space_id}/toggle-status",
            headers={"Authorization": f"Bearer {self.host_token}"},
        )
        self.assertEqual(togg2.status_code, 200)
        self.assertTrue(togg2.get_json()["data"]["is_active"])

    def test_check_availability(self):
        """5. Verify availability checks and slot overlap collision detection."""
        create_res = self.client.post(
            "/api/spaces",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json=self._sample_space_payload(),
        )
        space_id = create_res.get_json()["data"]["id"]

        # Invalid date format
        bad_date = self.client.get(f"/api/spaces/{space_id}/check-availability?date=invalid-date")
        self.assertEqual(bad_date.status_code, 400)

        # Initial check with no bookings
        avail_res = self.client.get(f"/api/spaces/{space_id}/check-availability?date=2026-10-15")
        self.assertEqual(avail_res.status_code, 200)
        self.assertTrue(avail_res.get_json()["data"]["is_available"])
        self.assertEqual(len(avail_res.get_json()["data"]["booked_slots"]), 0)

        # Add confirmed booking
        start_t = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)
        end_t = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)
        with self.app.app_context():
            b = Booking(
                space_id=space_id,
                guest_id=self.guest_id,
                start_time=start_t,
                end_time=end_t,
                total_hours=4.0,
                base_amount=600.0,
                total_amount=670.0,
                status="CONFIRMED",
            )
            db.session.add(b)
            db.session.commit()

        # Slot query overlapping 11:00 to 13:00 -> not available
        req_start = "2026-10-15T11:00:00Z"
        req_end = "2026-10-15T13:00:00Z"
        check_overlap = self.client.get(
            f"/api/spaces/{space_id}/check-availability?start_time={req_start}&end_time={req_end}"
        )
        self.assertEqual(check_overlap.status_code, 200)
        self.assertFalse(check_overlap.get_json()["data"]["is_available"])

        # Slot query after booking (15:00 to 17:00) -> available
        req_start_free = "2026-10-15T15:00:00Z"
        req_end_free = "2026-10-15T17:00:00Z"
        check_free = self.client.get(
            f"/api/spaces/{space_id}/check-availability?start_time={req_start_free}&end_time={req_end_free}"
        )
        self.assertEqual(check_free.status_code, 200)
        self.assertTrue(check_free.get_json()["data"]["is_available"])

    def test_reviews_and_host_trust_score(self):
        """6. Verify completed-booking review requirement, rating calculation, and trust score hook."""
        create_res = self.client.post(
            "/api/spaces",
            headers={"Authorization": f"Bearer {self.host_token}"},
            json=self._sample_space_payload(),
        )
        space_id = create_res.get_json()["data"]["id"]

        # Guest has NOT booked yet -> review attempt rejected with 403
        bad_rev = self.client.post(
            f"/api/spaces/{space_id}/reviews",
            headers={"Authorization": f"Bearer {self.guest_token}"},
            json={"rating": 5, "comment": "Never stayed here!"},
        )
        self.assertEqual(bad_rev.status_code, 403)
        self.assertIn("completed stay", bad_rev.get_json()["error"]["message"])

        # Add a completed booking for this guest
        with self.app.app_context():
            completed_booking = Booking(
                space_id=space_id,
                guest_id=self.guest_id,
                start_time=utc_now() - timedelta(days=2),
                end_time=utc_now() - timedelta(days=2, hours=-3),
                total_hours=3.0,
                base_amount=450.0,
                total_amount=500.0,
                status="COMPLETED",
            )
            db.session.add(completed_booking)
            db.session.commit()
            booking_id = completed_booking.id

        # Submit verified review
        rev_res = self.client.post(
            f"/api/spaces/{space_id}/reviews",
            headers={"Authorization": f"Bearer {self.guest_token}"},
            json={"rating": 5, "comment": "Outstanding wifi and ergonomic setup!", "booking_id": booking_id},
        )
        self.assertEqual(rev_res.status_code, 201)
        self.assertEqual(rev_res.get_json()["data"]["rating"], 5)
        self.assertTrue(rev_res.get_json()["data"]["is_verified_stay"])

        # Check space average rating updated
        space_res = self.client.get(f"/api/spaces/{space_id}")
        self.assertEqual(space_res.get_json()["data"]["average_rating"], 5.0)
        self.assertEqual(space_res.get_json()["data"]["total_reviews"], 1)

        # Check host trust score updated via hook (5.0 * 20 = 100.0)
        with self.app.app_context():
            h = db.session.get(User, self.host_id)
            self.assertEqual(h.trust_score, 100.0)

        # Verify duplicate review on same booking rejected
        dup_rev = self.client.post(
            f"/api/spaces/{space_id}/reviews",
            headers={"Authorization": f"Bearer {self.guest_token}"},
            json={"rating": 4, "comment": "Second review attempt", "booking_id": booking_id},
        )
        self.assertEqual(dup_rev.status_code, 409)

    def test_photo_upload_and_validation(self):
        """7. Verify 5MB upload limit and magic byte file-header verification."""
        # 1. Reject non-image / disguised file (e.g. text file pretending to be jpg)
        fake_file = io.BytesIO(b"This is a disguised python or shell script")
        res_fake = self.client.post(
            "/api/spaces/upload-photo",
            headers={"Authorization": f"Bearer {self.host_token}"},
            data={"photo": (fake_file, "script.jpg")},
            content_type="multipart/form-data",
        )
        self.assertEqual(res_fake.status_code, 400)
        self.assertIn("Invalid image format", res_fake.get_json()["error"]["message"])

        # 2. Reject file exceeding 5MB
        oversized = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * (5 * 1024 * 1024 + 100))
        res_large = self.client.post(
            "/api/spaces/upload-photo",
            headers={"Authorization": f"Bearer {self.host_token}"},
            data={"photo": (oversized, "large.jpg")},
            content_type="multipart/form-data",
        )
        self.assertEqual(res_large.status_code, 413)

        # 3. Valid JPEG with proper binary magic bytes (\xff\xd8\xff\xe0)
        valid_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 200)
        res_ok = self.client.post(
            "/api/spaces/upload-photo",
            headers={"Authorization": f"Bearer {self.host_token}"},
            data={"photo": (valid_jpeg, "valid_workspace.jpg")},
            content_type="multipart/form-data",
        )
        self.assertEqual(res_ok.status_code, 201)
        url = res_ok.get_json()["data"]["url"]
        self.assertTrue(url.startswith("/uploads/"))

        # Verify uploaded photo can be fetched via GET /uploads/<filename>
        get_photo = self.client.get(url)
        self.assertEqual(get_photo.status_code, 200)

    def test_ai_scan_and_assist_adapters(self):
        """8. Verify AI scan and listing assist endpoints with deterministic fallbacks."""
        # AI scan
        scan_res = self.client.post("/api/spaces/ai-scan", json={
            "space_type": "studio",
            "category": "creative",
            "amenities": ["Soundproofed", "Podcast Microphones"],
        })
        self.assertEqual(scan_res.status_code, 200)
        data = scan_res.get_json()["data"]
        self.assertIn("Studio", data["ai_lighting"])
        self.assertIn("dB", data["ai_noise_level"])
        self.assertIn("Podcast Recording", data["recommended_uses"])

        # Assist listing
        assist_res = self.client.post("/api/spaces/assist-listing", json={
            "title": "Koramangala Pod",
            "space_type": "private_office",
            "neighborhood": "Koramangala",
            "city": "Bengaluru",
        })
        self.assertEqual(assist_res.status_code, 200)
        adata = assist_res.get_json()["data"]
        self.assertIn("suggested_description", adata)
        self.assertGreater(adata["suggested_hourly_price"], 0)
        self.assertIn("suggested_rules", adata)


if __name__ == "__main__":
    unittest.main()
