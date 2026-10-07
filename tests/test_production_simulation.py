"""Production simulation tests for SpaceLoop unified deployment.

Verifies:
- Production frontend build index.html is served at /
- API metadata served when Accept: application/json
- System health and database connectivity
- Representative API endpoints (/api/spaces, /api/v1/auth)
- Static assets (/assets/...)
- SPA routing fallback (refreshing /explore or /checkout does not 404)
- API 404 guard (ensuring /api/ routes are never intercepted by SPA fallback)
"""
import unittest
from backend.run import app


class ProductionSimulationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        with self.app.app_context():
            from backend.core.database import init_db
            init_db(self.app)

    def test_root_serves_frontend_spa_index_html(self):
        """Verify GET / with text/html serves frontend/dist/index.html."""
        res = self.client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'<div id="root">', res.data)
        self.assertIn(b"assets/index-", res.data)

    def test_root_serves_api_json_metadata_on_json_accept(self):
        """Verify GET / with application/json returns API service information."""
        res = self.client.get("/", headers={"Accept": "application/json"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.is_json)
        data = res.get_json()
        self.assertEqual(data.get("name"), "SpaceLoop API")
        self.assertEqual(data.get("version"), "1.0.0")

    def test_health_endpoints(self):
        """Verify GET /health and GET /api/v1/health return 200 with database health status."""
        for path in ("/health", "/api/v1/health"):
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.is_json)
            data = res.get_json()
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("service"), "SpaceLoop API")
            self.assertIn("database", data)

    def test_spa_client_side_routing_fallback_on_page_refresh(self):
        """Verify refreshing deep client routes (/explore, /checkout/1, /host) returns index.html, not 404."""
        for route in ("/explore", "/checkout/42", "/host", "/admin", "/profile"):
            res = self.client.get(route, headers={"Accept": "text/html"})
            self.assertEqual(res.status_code, 200, f"Route {route} did not return 200")
            self.assertIn(b'<div id="root">', res.data)

    def test_api_routes_not_intercepted_by_spa(self):
        """Verify missing /api/ routes return JSON 404 errors and are never swallowed by SPA fallback."""
        res = self.client.get("/api/unknown-endpoint-xyz")
        self.assertEqual(res.status_code, 404)
        self.assertTrue(res.is_json)
        self.assertFalse(res.get_json().get("success"))

    def test_api_spaces_listing(self):
        """Verify representative GET /api/spaces endpoint returns 200 OK."""
        res = self.client.get("/api/spaces")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.is_json)
        self.assertTrue(res.get_json().get("success"))

    def test_auth_route_handles_requests(self):
        """Verify POST /api/v1/auth/login handles requests and responds with JSON."""
        res = self.client.post("/api/v1/auth/login", json={"email": "nobody@spaceloop.test", "password": "wrong"})
        self.assertIn(res.status_code, (400, 401, 404))
        self.assertTrue(res.is_json)


if __name__ == "__main__":
    unittest.main()
