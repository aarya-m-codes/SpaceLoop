import os
import tempfile
import unittest
from pathlib import Path
from sqlalchemy import inspect, text

from app import create_app
from backend.core.cache import InMemoryCache
from backend.core.database import check_database_health, db, init_db
from backend.core.geo import (
    haversine_distance_meters,
    is_within_geofence,
    validate_coordinates,
)
from config import (
    BaseConfig,
    ProductionConfig,
    TestingConfig,
    normalize_database_url,
)
from security import hash_password, verify_password


class FoundationTestCase(unittest.TestCase):
    """Test suite verifying the Phase 1 SpaceLoop backend foundation."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        
        class CustomTestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"

        self.app = create_app(CustomTestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db(self.app)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.unlink(self.temp_db_path)
            # Remove WAL / SHM files if created
            wal = f"{self.temp_db_path}-wal"
            shm = f"{self.temp_db_path}-shm"
            if os.path.exists(wal):
                os.unlink(wal)
            if os.path.exists(shm):
                os.unlink(shm)
        except OSError:
            pass

    def test_app_starts(self):
        """1. Verify that the Flask application initializes and reports testing mode."""
        self.assertIsNotNone(self.app)
        self.assertTrue(self.app.config["TESTING"])

    def test_database_connects(self):
        """2. Verify that the database connects and executes basic queries."""
        with self.app.app_context():
            with db.engine.connect() as conn:
                res = conn.execute(text("SELECT 1")).scalar()
                self.assertEqual(res, 1)

    def test_sqlite_wal_is_enabled(self):
        """3. Verify that SQLite journal_mode is configured to WAL."""
        with self.app.app_context():
            with db.engine.connect() as conn:
                journal_mode = conn.execute(text("PRAGMA journal_mode")).scalar()
                self.assertEqual(journal_mode.lower(), "wal")

    def test_sqlite_foreign_keys_are_enabled(self):
        """4. Verify that SQLite foreign keys constraint checking is enabled."""
        with self.app.app_context():
            with db.engine.connect() as conn:
                fk_status = conn.execute(text("PRAGMA foreign_keys")).scalar()
                self.assertEqual(fk_status, 1)

    def test_sqlite_performance_pragmas(self):
        """Verify the full suite of mandated SQLite performance PRAGMAs."""
        with self.app.app_context():
            with db.engine.connect() as conn:
                sync_mode = conn.execute(text("PRAGMA synchronous")).scalar()
                busy_timeout = conn.execute(text("PRAGMA busy_timeout")).scalar()
                temp_store = conn.execute(text("PRAGMA temp_store")).scalar()
                mmap_size = conn.execute(text("PRAGMA mmap_size")).scalar()

                self.assertEqual(sync_mode, 1, "synchronous must be 1 (NORMAL)")
                self.assertEqual(busy_timeout, 5000, "busy_timeout must be 5000ms")
                self.assertEqual(temp_store, 2, "temp_store must be 2 (MEMORY)")
                self.assertEqual(mmap_size, 268435456, "mmap_size must be 256MB")

    def test_tables_are_created(self):
        """5. Verify that all 17 required SpaceLoop domain tables are created."""
        expected_tables = {
            "users",
            "spaces",
            "bookings",
            "escrow_transactions",
            "access_logs",
            "risk_assessments",
            "fraud_event_records",
            "fraud_alert_records",
            "password_reset_tokens",
            "email_verification_tokens",
            "mfa_recovery_codes",
            "device_sessions",
            "audit_logs",
            "email_logs",
            "space_inquiries",
            "reviews",
            "notifications",
        }

        with self.app.app_context():
            inspector = inspect(db.engine)
            actual_tables = set(inspector.get_table_names())
            for table in expected_tables:
                self.assertIn(table, actual_tables, f"Table '{table}' was not created in database.")

    def test_postgresql_url_configuration_is_accepted(self):
        """6. Verify PostgreSQL URL normalization and ProductionConfig handling."""
        # Test URL normalizer
        legacy_url = "postgres://spaceloop_user:secret@db.render.internal:5432/spaceloop"
        normalized = normalize_database_url(legacy_url)
        self.assertEqual(normalized, "postgresql://spaceloop_user:secret@db.render.internal:5432/spaceloop")

        # Test standard PostgreSQL URL remains unchanged
        standard_url = "postgresql://user:pass@localhost:5432/prod_db"
        self.assertEqual(normalize_database_url(standard_url), standard_url)

        # Test ProductionConfig defaults
        prod_cfg = ProductionConfig()
        self.assertTrue(prod_cfg.SQLALCHEMY_DATABASE_URI.startswith("postgresql://"))
        self.assertIn("pool_size", prod_cfg.SQLALCHEMY_ENGINE_OPTIONS)
        self.assertEqual(prod_cfg.SQLALCHEMY_ENGINE_OPTIONS["pool_pre_ping"], True)

    def test_health_endpoint_works(self):
        """7. Verify that the health check endpoint returns 200 with database status."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["service"], "SpaceLoop API")
        self.assertEqual(data["database"]["status"], "connected")
        self.assertEqual(data["database"]["dialect"], "sqlite")
        self.assertEqual(data["database"]["sqlite_journal_mode"], "wal")
        self.assertTrue(data["database"]["sqlite_foreign_keys"])

        # Also verify root /health alias
        alias_response = self.client.get("/health")
        self.assertEqual(alias_response.status_code, 200)

    def test_structured_error_responses(self):
        """Verify that HTTP errors return structured JSON envelopes."""
        # 404 Not Found
        res_404 = self.client.get("/api/v1/nonexistent-route")
        self.assertEqual(res_404.status_code, 404)
        data_404 = res_404.get_json()
        self.assertFalse(data_404["success"])
        self.assertEqual(data_404["error"]["code"], "NOT_FOUND")

        # 405 Method Not Allowed
        res_405 = self.client.post("/health")
        self.assertEqual(res_405.status_code, 405)
        data_405 = res_405.get_json()
        self.assertFalse(data_405["success"])
        self.assertEqual(data_405["error"]["code"], "METHOD_NOT_ALLOWED")

    def test_geo_utilities(self):
        """Verify Haversine geospatial calculations and geofence verification."""
        # Bengaluru coordinates: Indiranagar 100ft Rd vs nearby point (~30m away)
        lat1, lon1 = 12.978400, 77.640800
        lat2, lon2 = 12.978450, 77.640820

        dist = haversine_distance_meters(lat1, lon1, lat2, lon2)
        self.assertGreater(dist, 0)
        self.assertLess(dist, 50.0)

        inside, d = is_within_geofence(lat1, lon1, lat2, lon2, radius_meters=50.0)
        self.assertTrue(inside)

        # Far away point (e.g. Mumbai vs Bengaluru)
        mumbai_lat, mumbai_lon = 19.0760, 72.8777
        far_inside, far_d = is_within_geofence(lat1, lon1, mumbai_lat, mumbai_lon, radius_meters=50.0)
        self.assertFalse(far_inside)
        self.assertGreater(far_d, 500000)  # > 500 km

        # Coordinate validation
        self.assertTrue(validate_coordinates(12.9784, 77.6408))
        self.assertFalse(validate_coordinates(95.0, 77.6408))

    def test_cache_abstraction(self):
        """Verify cache operations, TTL, and deletion."""
        cache = InMemoryCache()
        cache.set("space:1:status", "available", ttl=60)
        self.assertEqual(cache.get("space:1:status"), "available")
        self.assertTrue(cache.has("space:1:status"))

        cache.delete("space:1:status")
        self.assertIsNone(cache.get("space:1:status"))

    def test_security_primitives(self):
        """Verify password hashing and verification."""
        pwd = "SecureHostPassword#2026"
        hashed = hash_password(pwd)
        self.assertNotEqual(pwd, hashed)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))


if __name__ == "__main__":
    unittest.main()
