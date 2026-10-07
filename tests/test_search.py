"""Test suite for SpaceLoop Discovery, Multilingual NLP Search, and Matching Engine."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app import create_app
from backend.core.database import db
from backend.modules.nlp.parser import QueryParser
from backend.modules.search.keyword_engine import KeywordEngine
from backend.modules.search.matcher import AIMatcher
from backend.modules.search.pipeline import DiscoveryPipeline
from backend.modules.search.ranking import RankingEngine
from backend.modules.search.vector_engine import VectorEngine
from config import TestingConfig
from models import Booking, Space, User, utc_now
from security import hash_password


class SearchTestCase(unittest.TestCase):
    """Test suite verifying the 6-stage discovery pipeline, multilingual NLP, and matching engine."""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed test users and spaces
        self._seed_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _seed_test_data(self):
        # Host 1 (Bengaluru, Trust score: 100)
        host1 = User(
            email="host.blr@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Bengaluru Host",
            role="HOST",
            trust_score=100.0,
            is_active=True,
            is_verified=True,
        )
        # Host 2 (Mumbai, Trust score: 80)
        host2 = User(
            email="host.mum@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Mumbai Host",
            role="HOST",
            trust_score=80.0,
            is_active=True,
            is_verified=True,
        )
        # Host 3 (Pune, Trust score: 95)
        host3 = User(
            email="host.pune@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Pune Host",
            role="HOST",
            trust_score=95.0,
            is_active=True,
            is_verified=True,
        )
        db.session.add_all([host1, host2, host3])
        db.session.commit()

        # Space 1: Indiranagar Quiet Tech Desk (Bengaluru)
        self.space_indiranagar = Space(
            host_id=host1.id,
            title="Indiranagar Quiet Fiber Desk",
            description="Dedicated ergonomic desk with high-speed fiber internet and silent zone in Indiranagar Bengaluru.",
            space_type="desk",
            category="commercial",
            address_line1="100 Feet Rd, Indiranagar",
            neighborhood="Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            pincode="560038",
            latitude=12.9784,
            longitude=77.6408,
            price_per_hour=250.0,
            capacity=1,
            amenities=["wifi", "quiet", "power_backup", "coffee"],
            ai_lighting="Warm Architectural LED",
            ai_noise_level="Acoustically Isolated (<32dB Quiet)",
            ai_power_access="Dedicated surge-protected outlets",
            recommended_uses=["Coding", "Focused Work", "Writing"],
            is_active=True,
            is_approved=True,
        )

        # Space 2: Whitefield Coworking Desk (Bengaluru, ~15km from Indiranagar)
        self.space_whitefield = Space(
            host_id=host1.id,
            title="Whitefield Tech Hub Workstation",
            description="Lively open coworking workstation in ITPL Whitefield.",
            space_type="desk",
            category="commercial",
            address_line1="ITPL Main Rd, Whitefield",
            neighborhood="Whitefield",
            city="Bengaluru",
            state="Karnataka",
            pincode="560066",
            latitude=12.9698,
            longitude=77.7499,
            price_per_hour=400.0,
            capacity=4,
            amenities=["wifi", "ac", "parking"],
            ai_lighting="Bright fluorescent",
            ai_noise_level="Moderate open floor (<55dB)",
            is_active=True,
            is_approved=True,
        )

        # Space 3: BKC Boardroom & Meeting Pod (Mumbai)
        self.space_bkc = Space(
            host_id=host2.id,
            title="BKC Executive Meeting Room & Studio",
            description="State-of-the-art meeting room with 4K projector, podcast mics, and AC in Bandra Kurla Complex Mumbai.",
            space_type="meeting_room",
            category="commercial",
            address_line1="G Block, BKC",
            neighborhood="BKC",
            city="Mumbai",
            state="Maharashtra",
            pincode="400051",
            latitude=19.0657,
            longitude=72.8687,
            price_per_hour=1200.0,
            capacity=8,
            amenities=["projector", "ac", "wifi", "whiteboard", "parking"],
            ai_noise_level="Soundproofed conference room (<35dB)",
            recommended_uses=["Client Presentations", "Podcasts", "Team Sprints"],
            is_active=True,
            is_approved=True,
        )

        # Space 4: Kothrud Study Haven (Pune)
        self.space_kothrud = Space(
            host_id=host3.id,
            title="Kothrud Peaceful Study Cabin",
            description="Silent study and reading cabin in Kothrud Pune with high-speed WiFi and air conditioning.",
            space_type="room",
            category="commercial",
            address_line1="Paud Road, Kothrud",
            neighborhood="Kothrud",
            city="Pune",
            state="Maharashtra",
            pincode="411038",
            latitude=18.5074,
            longitude=73.8077,
            price_per_hour=200.0,
            capacity=2,
            amenities=["wifi", "ac", "quiet"],
            ai_noise_level="Whisper Quiet (<30dB)",
            recommended_uses=["Study", "Reading", "Deep Work"],
            is_active=True,
            is_approved=True,
        )

        db.session.add_all([
            self.space_indiranagar,
            self.space_whitefield,
            self.space_bkc,
            self.space_kothrud,
        ])
        db.session.commit()

    # =========================================================================
    # 1. Multilingual NLP Entity Extraction Tests
    # =========================================================================

    def test_nlp_english_query(self):
        """Verify English entity extraction for location, budget, duration, date, and amenities."""
        query = "Quiet desk in Indiranagar under 500 with wifi for 2 hours tomorrow"
        parsed = QueryParser.parse_query(query)

        self.assertEqual(parsed["city"], "Bengaluru")
        self.assertEqual(parsed["neighborhood"], "Indiranagar")
        self.assertEqual(parsed["space_type"], "desk")
        self.assertEqual(parsed["budget"], 500.0)
        self.assertEqual(parsed["duration_hours"], 2.0)
        self.assertIn("wifi", parsed["amenities"])
        self.assertIn("quiet", parsed["amenities"])
        self.assertIsNotNone(parsed["date"])

    def test_nlp_hinglish_query(self):
        """Verify Hinglish entity extraction (Indiranagar mein quiet desk chahiye wifi ke sath)."""
        query = "Indiranagar mein quiet desk chahiye wifi ke sath under 500 kal 2 ghante ke liye"
        parsed = QueryParser.parse_query(query)

        self.assertEqual(parsed["city"], "Bengaluru")
        self.assertEqual(parsed["neighborhood"], "Indiranagar")
        self.assertEqual(parsed["budget"], 500.0)
        self.assertEqual(parsed["duration_hours"], 2.0)
        self.assertEqual(parsed["space_type"], "desk")
        self.assertIn("wifi", parsed["amenities"])
        self.assertIn("quiet", parsed["amenities"])

    def test_nlp_marathi_query(self):
        """Verify Marathi entity extraction with Devanagari script."""
        query = "पुण्यात कोथरूड येथे अभ्यासासाठी शांत जागा वायफाय सह 300 रुपयांच्या आत उद्या 3 तास"
        parsed = QueryParser.parse_query(query)

        self.assertEqual(parsed["city"], "Pune")
        self.assertEqual(parsed["neighborhood"], "Kothrud")
        self.assertEqual(parsed["budget"], 300.0)
        self.assertEqual(parsed["duration_hours"], 3.0)
        self.assertIn("wifi", parsed["amenities"])
        self.assertIn("quiet", parsed["amenities"])
        self.assertEqual(parsed["use_case"], "study")

    def test_nlp_team_meeting_query(self):
        """Verify capacity, meeting room typology, and projector extraction in Mumbai."""
        query = "BKC Mumbai me team of 6 ke liye meeting room with projector budget 1500"
        parsed = QueryParser.parse_query(query)

        self.assertEqual(parsed["city"], "Mumbai")
        self.assertEqual(parsed["neighborhood"], "BKC")
        self.assertEqual(parsed["capacity"], 6)
        self.assertEqual(parsed["budget"], 1500.0)
        self.assertIn("meeting_room", [parsed["space_type"], "meeting_room"])
        self.assertIn("projector", parsed["amenities"])

    # =========================================================================
    # 2. Vector & Keyword Engines
    # =========================================================================

    def test_deterministic_vectorizer(self):
        """Verify 256-dimensional concept-cluster hash vectorizer and cosine similarity."""
        vec1 = VectorEngine.get_deterministic_embedding("Quiet desk with high speed wifi for coding in Bengaluru")
        vec2 = VectorEngine.get_deterministic_embedding("Silent workstation fiber internet software developer Bangalore")
        vec_unrelated = VectorEngine.get_deterministic_embedding("Wedding hall with catering and DJ sound system")

        self.assertEqual(len(vec1), 256)
        self.assertEqual(len(vec2), 256)

        sim_related = VectorEngine.cosine_similarity(vec1, vec2)
        sim_unrelated = VectorEngine.cosine_similarity(vec1, vec_unrelated)

        self.assertGreater(sim_related, 0.50)
        self.assertGreater(sim_related, sim_unrelated)

    def test_keyword_similarity(self):
        """Verify Jaccard keyword similarity and amenity coverage."""
        sim = KeywordEngine.calculate_similarity(
            query="quiet fiber desk with wifi and coffee",
            space=self.space_indiranagar,
            requested_amenities=["wifi", "quiet"],
        )
        self.assertGreater(sim, 0.60)

    # =========================================================================
    # 3. Ranking Engine Component Tests
    # =========================================================================

    def test_ranking_price_scoring(self):
        """Verify price score: 1.0 inside budget, linearly degrading when over budget."""
        # 1.0 inside budget
        self.assertEqual(RankingEngine.calculate_price_score(price_per_hour=250.0, budget=500.0), 1.0)
        self.assertEqual(RankingEngine.calculate_price_score(price_per_hour=500.0, budget=500.0), 1.0)

        # 50% over budget -> 0.5
        score_over = RankingEngine.calculate_price_score(price_per_hour=750.0, budget=500.0)
        self.assertAlmostEqual(score_over, 0.50, places=2)

        # 100%+ over budget -> 0.0
        score_way_over = RankingEngine.calculate_price_score(price_per_hour=1200.0, budget=500.0)
        self.assertEqual(score_way_over, 0.0)

    def test_ranking_geo_scoring(self):
        """Verify geo score: 1.0 within 2km, degrading to 0 at 25km."""
        # Distance within 2km (exact same point -> 1.0)
        score_close, dist_close = RankingEngine.calculate_geo_score(
            space_lat=12.9784,
            space_lng=77.6408,
            user_lat=12.9784,
            user_lng=77.6408,
        )
        self.assertEqual(score_close, 1.0)
        self.assertLessEqual(dist_close, 0.01)

        # Distance ~12km (Indiranagar to Whitefield)
        score_mid, dist_mid = RankingEngine.calculate_geo_score(
            space_lat=12.9698,
            space_lng=77.7499,
            user_lat=12.9784,
            user_lng=77.6408,
        )
        self.assertTrue(0.0 < score_mid < 1.0)
        self.assertGreater(dist_mid, 10.0)

        # Distance > 25km (e.g. Bengaluru to Mumbai -> 0.0)
        score_far, dist_far = RankingEngine.calculate_geo_score(
            space_lat=19.0760,
            space_lng=72.8777,
            user_lat=12.9784,
            user_lng=77.6408,
        )
        self.assertEqual(score_far, 0.0)
        self.assertGreater(dist_far, 500.0)

    def test_ranking_trust_scoring(self):
        """Verify host trust score normalization to [0.0, 1.0]."""
        self.assertEqual(RankingEngine.calculate_trust_score(100.0), 1.0)
        self.assertEqual(RankingEngine.calculate_trust_score(80.0), 0.8)
        self.assertEqual(RankingEngine.calculate_trust_score(0.0), 0.0)

    # =========================================================================
    # 4. Six-Stage Hybrid Pipeline Tests
    # =========================================================================

    def test_pipeline_search_indiranagar(self):
        """Verify pipeline execution: Indiranagar space ranks #1 for Indiranagar query."""
        res = DiscoveryPipeline.search(
            query="quiet desk with wifi in Indiranagar under 500",
        )
        items = res.get("items", [])
        self.assertGreater(len(items), 0)

        top_match = items[0]
        self.assertEqual(top_match["id"], self.space_indiranagar.id)
        self.assertIn("score_breakdown", top_match)
        self.assertGreaterEqual(top_match["score"], 0.70)
        self.assertEqual(top_match["score_breakdown"]["s_price"], 1.0)

    def test_pipeline_booking_availability_conflict(self):
        """Verify availability calculation marks occupied space as unavailable."""
        # Create a confirmed booking for tomorrow 10:00 to 12:00 UTC
        tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
        booking_start = datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=10)
        booking_end = booking_start + timedelta(hours=2)

        conflicting_booking = Booking(
            space_id=self.space_indiranagar.id,
            guest_id=1,
            start_time=booking_start,
            end_time=booking_end,
            total_hours=2.0,
            base_amount=500.0,
            total_amount=590.0,
            status="CONFIRMED",
        )
        db.session.add(conflicting_booking)
        db.session.commit()

        # Query during that exact slot (tomorrow at 10:00 for 2 hours)
        res = DiscoveryPipeline.search(
            query="quiet desk in Indiranagar",
            date=tomorrow.isoformat(),
            hours=2.0,
        )

        indira_result = next((item for item in res["items"] if item["id"] == self.space_indiranagar.id), None)
        self.assertIsNotNone(indira_result)
        self.assertFalse(indira_result["is_available"])

    # =========================================================================
    # 5. REST API Endpoints: /api/spaces/search and /api/spaces/ai-match
    # =========================================================================

    def test_api_search_endpoint_post(self):
        """Verify POST /api/spaces/search returns structured results and parsed constraints."""
        res = self.client.post(
            "/api/spaces/search",
            json={
                "query": "quiet desk in Indiranagar under 500 with wifi for 2 hours tomorrow",
                "budget": 500.0,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("items", data)
        self.assertIn("parsed_constraints", data)
        self.assertGreaterEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["neighborhood"], "Indiranagar")

    def test_api_ai_match_endpoint_post(self):
        """Verify POST /api/spaces/ai-match returns top_matches and match_explanation."""
        res = self.client.post(
            "/api/spaces/ai-match",
            json={
                "query": "Kothrud Pune peaceful study room under 300",
                "top_k": 3,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("top_matches", data)
        self.assertIn("match_explanation", data)
        self.assertTrue(len(data["match_explanation"]) > 20)
        self.assertEqual(data["top_matches"][0]["neighborhood"], "Kothrud")

    # =========================================================================
    # 6. Simulated AI Outage Tests
    # =========================================================================

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False)
    def test_search_during_ai_outage_missing_key(self):
        """Verify search continues seamlessly without GEMINI_API_KEY using deterministic pipeline."""
        res = self.client.post(
            "/api/spaces/search",
            json={"query": "quiet desk in Indiranagar with wifi under 500"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertGreaterEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["id"], self.space_indiranagar.id)

    @patch("google.genai.Client")
    def test_search_and_match_during_simulated_ai_exception(self, mock_genai):
        """Verify search and ai-match continue 100% when Gemini raises unhandled network/API exceptions."""
        mock_instance = MagicMock()
        mock_instance.models.generate_content.side_effect = RuntimeError("503 Service Unavailable: Gemini Offline")
        mock_instance.models.embed_content.side_effect = ConnectionError("Connection refused to AI backend")
        mock_genai.return_value = mock_instance

        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"}):
            # Test 1: Search endpoint
            search_res = self.client.post(
                "/api/spaces/search",
                json={"query": "quiet desk in Indiranagar under 500 with wifi"},
            )
            self.assertEqual(search_res.status_code, 200)
            items = search_res.get_json()["data"]["items"]
            self.assertGreater(len(items), 0)

            # Test 2: AI Match endpoint
            match_res = self.client.post(
                "/api/spaces/ai-match",
                json={"query": "Indiranagar quiet desk under 500"},
            )
            self.assertEqual(match_res.status_code, 200)
            data = match_res.get_json()["data"]
            self.assertIn("top_matches", data)
            self.assertIn("match_explanation", data)
            # Explanation must be synthesized deterministically without failing
            self.assertIn("Indiranagar", data["match_explanation"])
            self.assertGreater(len(data["top_matches"]), 0)


if __name__ == "__main__":
    unittest.main()
