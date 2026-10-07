"""Comprehensive Test Suite for SpaceLoop Semantic AI Search Engine.

Covers:
1. Semantic understanding & paraphrasing equivalence
2. Constraint safety (budget ceiling, capacity floor, active status, booking collisions, radius)
3. Combined natural-language query ("I need a quiet place for 3 people to work tomorrow from 2 to 6 PM, near the university, under ₹150/hour.")
4. Failure handling (impossible constraints -> 0 results, missing noise data, booking conflict removal)
5. Embedding persistence, versioning, caching, and rebuild
6. Deterministic 256d concept-cluster fallback during simulated Gemini failure
7. Explanation accuracy & grounded match reasons verification
8. REST API endpoints (POST/GET /api/v1/search, POST /api/v1/search/embeddings/rebuild)
9. LoopBot service integration
"""

import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app import create_app
from backend.core.database import db
from backend.modules.ai.tools import LoopBotTools
from backend.modules.nlp.parser import QueryParser
from backend.modules.search.keyword_engine import KeywordEngine
from backend.modules.search.matcher import AIMatcher
from backend.modules.search.pipeline import DiscoveryPipeline, semantic_search
from backend.modules.search.ranking import RankingEngine
from backend.modules.search.vector_engine import VectorEngine
from config import TestingConfig
from models import Booking, Space, SpaceEmbedding, User
from security import hash_password


class SemanticSearchTestCase(unittest.TestCase):
    """End-to-end tests for the SpaceLoop Semantic AI Search Engine."""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self._seed_test_corpus()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _seed_test_corpus(self):
        # Host 1 (Trust 100%)
        self.host1 = User(
            email="host.verified@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Verified University Host",
            role="HOST",
            trust_score=100.0,
            is_active=True,
            is_verified=True,
        )
        # Host 2 (Trust 80%)
        self.host2 = User(
            email="host.commercial@spaceloop.in",
            password_hash=hash_password("Pass#1234"),
            full_name="Commercial Host",
            role="HOST",
            trust_score=80.0,
            is_active=True,
            is_verified=True,
        )
        db.session.add_all([self.host1, self.host2])
        db.session.commit()

        # Space A: Perfect match (Budget <= 150, Capacity >= 3, Quiet, Near university)
        # Price: ₹120/hr, Capacity: 4
        self.space_a = Space(
            host_id=self.host1.id,
            title="University Campus Quiet Research Studio",
            description="Peaceful study and focused work studio right beside university campus with high-speed Wi-Fi.",
            space_type="room",
            category="commercial",
            address_line1="Near University Main Gate, Indiranagar",
            neighborhood="Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            pincode="560038",
            latitude=12.9780,
            longitude=77.6400,
            price_per_hour=120.0,
            capacity=4,
            amenities=["wifi", "power_backup", "quiet"],
            ai_lighting="Architectural daylight LED",
            ai_noise_level="Acoustically Isolated (<32dB Quiet)",
            ai_power_access="Dedicated workstation surge outlets",
            recommended_uses=["Study", "Focused Work", "Research"],
            is_active=True,
            is_approved=True,
        )

        # Space B: Over-budget space (Price: ₹300/hr, Capacity: 6) -> Must NEVER match under ₹150
        self.space_b = Space(
            host_id=self.host2.id,
            title="High-End Executive Boardroom",
            description="Luxury boardroom with presentation displays and premium espresso machine.",
            space_type="meeting_room",
            category="commercial",
            address_line1="100 Feet Rd, Indiranagar",
            neighborhood="Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            pincode="560038",
            latitude=12.9785,
            longitude=77.6405,
            price_per_hour=300.0,
            capacity=6,
            amenities=["wifi", "projector", "coffee", "ac"],
            ai_lighting="Warm luxury ambient",
            ai_noise_level="Soundproofed conference room (<35dB)",
            is_active=True,
            is_approved=True,
        )

        # Space C: Under-capacity space (Price: ₹100/hr, Capacity: 1 solo desk) -> Must NEVER match for 3 people
        self.space_c = Space(
            host_id=self.host1.id,
            title="Solo Silent Focus Pod",
            description="Single person silent study booth with ergonomic chair.",
            space_type="desk",
            category="commercial",
            address_line1="CMH Road, Indiranagar",
            neighborhood="Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            pincode="560038",
            latitude=12.9782,
            longitude=77.6402,
            price_per_hour=100.0,
            capacity=1,
            amenities=["wifi", "quiet"],
            ai_noise_level="Whisper Quiet (<30dB)",
            is_active=True,
            is_approved=True,
        )

        # Space D: Inactive / Unapproved Space (Price: ₹90/hr, Capacity: 5) -> Must NEVER match
        self.space_d = Space(
            host_id=self.host2.id,
            title="Unapproved Basement Hall",
            description="Raw space pending moderator inspection.",
            space_type="room",
            category="commercial",
            address_line1="Old Airport Rd",
            neighborhood="Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            pincode="560008",
            latitude=12.9600,
            longitude=77.6500,
            price_per_hour=90.0,
            capacity=5,
            amenities=["wifi"],
            is_active=False,
            is_approved=False,
        )

        # Space E: Distant Space (Whitefield ~15km away, Price: ₹130/hr, Capacity: 5)
        self.space_e = Space(
            host_id=self.host1.id,
            title="Whitefield Quiet Team Pod",
            description="Quiet workspace in Whitefield for group work with internet.",
            space_type="room",
            category="commercial",
            address_line1="ITPL Main Road, Whitefield",
            neighborhood="Whitefield",
            city="Bengaluru",
            state="Karnataka",
            pincode="560066",
            latitude=12.9698,
            longitude=77.7499,
            price_per_hour=130.0,
            capacity=5,
            amenities=["wifi", "quiet"],
            ai_noise_level="Low (<42dB)",
            is_active=True,
            is_approved=True,
        )

        # Space F: Space with missing/unrecorded noise telemetry
        self.space_f = Space(
            host_id=self.host2.id,
            title="Unmeasured Acoustic Studio",
            description="Studio space without recorded sound level sensor data.",
            space_type="room",
            category="commercial",
            address_line1="Koramangala 5th Block",
            neighborhood="Koramangala",
            city="Bengaluru",
            state="Karnataka",
            pincode="560095",
            latitude=12.9352,
            longitude=77.6245,
            price_per_hour=140.0,
            capacity=4,
            amenities=["wifi"],
            ai_noise_level=None,  # Missing noise data
            is_active=True,
            is_approved=True,
        )

        db.session.add_all([
            self.space_a,
            self.space_b,
            self.space_c,
            self.space_d,
            self.space_e,
            self.space_f,
        ])
        db.session.commit()

    # =========================================================================
    # 1. Canonical End-to-End Search Test
    # =========================================================================

    def test_canonical_nl_query_end_to_end(self):
        """Test canonical prompt query:

        'I need a quiet place for 3 people to work tomorrow from 2 to 6 PM, near the university, under ₹150/hour.'
        """
        query = (
            "I need a quiet place for 3 people to work tomorrow from 2 to 6 PM, near the university, under ₹150/hour."
        )

        res = semantic_search(query=query)

        self.assertTrue(res.get("total", 0) > 0)
        items = res.get("items", [])
        self.assertTrue(len(items) > 0)

        # 1. Top match must be Space A (University Campus Quiet Research Studio)
        top_match = items[0]
        self.assertEqual(top_match["id"], self.space_a.id)

        # 2. Hard constraints verified on every returned candidate
        for item in items:
            # Price MUST be <= 150
            self.assertLessEqual(item["price_per_hour"], 150.0)
            # Capacity MUST be >= 3
            self.assertGreaterEqual(item["capacity"], 3)
            # Listing MUST be active and approved
            self.assertTrue(item["is_active"])
            self.assertTrue(item["is_approved"])

        # 3. Space B (₹300/hr) must NEVER be in results
        b_ids = [it["id"] for it in items]
        self.assertNotIn(self.space_b.id, b_ids)

        # 4. Space C (capacity 1) must NEVER be in results
        self.assertNotIn(self.space_c.id, b_ids)

        # 5. Space D (inactive) must NEVER be in results
        self.assertNotIn(self.space_d.id, b_ids)

        # 6. Verify parsed constraints
        parsed = res["parsed_constraints"]
        self.assertEqual(parsed["capacity"], 3)
        self.assertEqual(parsed["budget"], 150.0)
        self.assertEqual(parsed["start_time"], "14:00")
        self.assertEqual(parsed["end_time"], "18:00")
        self.assertEqual(parsed["duration_hours"], 4.0)
        self.assertEqual(parsed["noise_preference"], "quiet")
        self.assertEqual(parsed["landmark"], "university")

        # 7. Verify grounded match reasons
        reasons = top_match.get("match_reasons", [])
        self.assertTrue(len(reasons) >= 3)
        reasons_text = " ".join(reasons)
        self.assertIn("Fits 3 people", reasons_text)
        self.assertIn("Within your ₹150/hr budget", reasons_text)
        self.assertIn("Verified quiet environment", reasons_text)

    # =========================================================================
    # 2. Semantic Understanding & Equivalence
    # =========================================================================

    def test_semantic_equivalence_paraphrases(self):
        """Verify that semantic variations ('quiet workspace', 'peaceful place to work', 'low-noise study area')

        all retrieve semantically related spaces with high similarity.
        """
        queries = [
            "quiet research room for 3 people in Indiranagar",
            "peaceful place to work for 3 people in Indiranagar",
            "low-noise study area for 3 people in Indiranagar",
        ]

        for q in queries:
            res = semantic_search(query=q)
            items = res.get("items", [])
            self.assertGreater(len(items), 0)
            # Top match should be Space A (Quiet Research Studio with capacity 4)
            self.assertEqual(items[0]["id"], self.space_a.id, f"Failed for query: '{q}'")
            # Vector similarity breakdown must be positive and indicate strong match
            self.assertGreater(items[0]["score_breakdown"]["s_vector"], 0.30)


    # =========================================================================
    # 3. Strict Hard Constraint Safety
    # =========================================================================

    def test_budget_constraint_safety_never_bypassed_by_similarity(self):
        """Verify that even with 100% semantic similarity, a space exceeding budget is strictly eliminated."""
        # Query specifically mentions features only Space B has ("luxury boardroom presentation displays")
        # BUT with an impossible budget of ₹200/hr (Space B costs ₹300)
        res = semantic_search(
            query="luxury boardroom with presentation displays and premium espresso machine under 200",
            budget=200.0,
        )
        items = res.get("items", [])
        for item in items:
            self.assertLessEqual(item["price_per_hour"], 200.0)
            self.assertNotEqual(item["id"], self.space_b.id)

    def test_capacity_constraint_safety(self):
        """Verify that a solo desk (capacity 1) is never returned when a group of 4 is requested."""
        res = semantic_search(
            query="silent focus booth for a group of 4",
            capacity=4,
        )
        items = res.get("items", [])
        for item in items:
            self.assertGreaterEqual(item["capacity"], 4)
            self.assertNotEqual(item["id"], self.space_c.id)

    def test_impossible_constraints_return_empty_results_no_fallback(self):
        """Verify that when no space matches explicit constraints (e.g. ₹50/hr budget),

        empty results are returned rather than bypassing constraints.
        """
        res = semantic_search(
            query="quiet workspace under 50",
            budget=50.0,
        )
        self.assertEqual(res["total"], 0)
        self.assertEqual(len(res["items"]), 0)

    def test_radius_constraint_filtering(self):
        """Verify that spaces outside the specified radius are filtered out."""
        # User is at Indiranagar (12.9780, 77.6400) looking within 3 km
        # Space A is ~0 km, Space E (Whitefield) is ~15 km away
        res = semantic_search(
            query="quiet room within 3 km",
            location={"lat": 12.9780, "lng": 77.6400, "radius_km": 3.0},
        )
        items = res.get("items", [])
        item_ids = [it["id"] for it in items]
        self.assertIn(self.space_a.id, item_ids)
        self.assertNotIn(self.space_e.id, item_ids)

    # =========================================================================
    # 4. Booking Collision & Availability Filtering
    # =========================================================================

    def test_booking_collision_elimination(self):
        """Verify that when a space has a conflicting booking, require_available=True eliminates it."""
        tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
        booking_start = datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=14)
        booking_end = booking_start + timedelta(hours=4)

        # Occupy Space A tomorrow from 14:00 to 18:00
        conflict = Booking(
            space_id=self.space_a.id,
            guest_id=1,
            start_time=booking_start,
            end_time=booking_end,
            total_hours=4.0,
            base_amount=480.0,
            total_amount=504.0,
            status="CONFIRMED",
        )
        db.session.add(conflict)
        db.session.commit()

        # Search during that exact slot (14:00 to 18:00) with require_available=True
        res = semantic_search(
            query="quiet workspace for 3 people tomorrow from 2 to 6 PM under 150",
            require_available=True,
        )

        item_ids = [it["id"] for it in res["items"]]
        # Space A must NOT be in available candidates
        self.assertNotIn(self.space_a.id, item_ids)
        # Space E (also under 150, capacity 5, available) should be present
        self.assertIn(self.space_e.id, item_ids)

    # =========================================================================
    # 5. Missing Noise Data Handling
    # =========================================================================

    def test_missing_noise_data_explicitly_handled(self):
        """Verify that when a space has no noise telemetry (Space F), noise data is NOT invented."""
        noise_score, reason = KeywordEngine.calculate_noise_score("quiet", self.space_f)

        self.assertEqual(noise_score, 0.50)
        self.assertIn("unverified", reason.lower())
        self.assertIn("no noise telemetry", reason.lower())

    # =========================================================================
    # 6. Embedding Persistence, Cache, and Versioning
    # =========================================================================

    def test_embedding_persistence_and_cache(self):
        """Verify SpaceEmbedding is persisted and reused without regeneration when content is unchanged."""
        # 1. Generate and persist embedding for Space A
        emb1 = VectorEngine.get_or_create_space_embedding(self.space_a)
        self.assertGreater(len(emb1), 0)

        # 2. Check record exists in database
        record = SpaceEmbedding.query.filter_by(space_id=self.space_a.id).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.embedding_version, "v1")
        self.assertIsNotNone(record.content_hash)
        old_hash = record.content_hash

        # 3. Subsequent call should reuse persisted embedding without recomputing
        emb2 = VectorEngine.get_or_create_space_embedding(self.space_a)
        self.assertEqual(emb1, emb2)

        # 4. Modify space content -> content_hash changes -> embedding safely regenerated
        self.space_a.description = "Updated brand-new description with high acoustic isolation."
        db.session.commit()

        emb3 = VectorEngine.get_or_create_space_embedding(self.space_a)
        updated_record = SpaceEmbedding.query.filter_by(space_id=self.space_a.id).first()
        self.assertNotEqual(old_hash, updated_record.content_hash)

    def test_embedding_batch_rebuild(self):
        """Verify safe rebuild mechanism across all spaces."""
        summary = VectorEngine.rebuild_embeddings(force=True)
        self.assertGreaterEqual(summary["total_evaluated"], 5)
        self.assertEqual(summary["updated"], summary["total_evaluated"])

    # =========================================================================
    # 7. Deterministic Fallback During Simulated Outage
    # =========================================================================

    def test_deterministic_fallback_reproducibility(self):
        """Verify deterministic 256d vectorizer yields identical vectors for identical inputs."""
        text = "Quiet private workspace suitable for focused study for 3 people"
        v1 = VectorEngine.get_deterministic_embedding(text)
        v2 = VectorEngine.get_deterministic_embedding(text)

        self.assertEqual(len(v1), 256)
        self.assertEqual(v1, v2)

    @patch("google.genai.Client")
    def test_search_during_gemini_api_failure(self, mock_genai):
        """Verify search pipeline functions 100% when Gemini raises 503 or network exceptions."""
        mock_instance = MagicMock()
        mock_instance.models.embed_content.side_effect = ConnectionError("Gemini Embeddings Service Offline")
        mock_instance.models.generate_content.side_effect = RuntimeError("Gemini Generative API Offline")
        mock_genai.return_value = mock_instance

        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"}):
            res = semantic_search(
                query="quiet room for 3 people under 150",
            )
            self.assertGreater(res["total"], 0)
            self.assertEqual(res["items"][0]["id"], self.space_a.id)

    # =========================================================================
    # 8. REST API Endpoints
    # =========================================================================

    def test_api_v1_search_post(self):
        """Verify POST /api/v1/search endpoint with query, location, and filters."""
        res = self.client.post(
            "/api/v1/search",
            json={
                "query": "quiet workspace for 3 people under 150",
                "filters": {"budget": 150.0, "capacity": 3},
            },
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["success"])
        self.assertIn("data", body)
        self.assertIn("items", body)
        self.assertIn("parsed_constraints", body)
        self.assertGreater(body["total"], 0)
        self.assertEqual(body["items"][0]["id"], self.space_a.id)
        self.assertIn("match_reasons", body["items"][0])

    def test_api_v1_search_get(self):
        """Verify GET /api/v1/search endpoint with query parameters."""
        res = self.client.get(
            "/api/v1/search?q=quiet+workspace&budget=150&capacity=3",
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["success"])
        self.assertGreater(body["total"], 0)

    def test_api_v1_search_embeddings_rebuild(self):
        """Verify POST /api/v1/search/embeddings/rebuild endpoint."""
        res = self.client.post(
            "/api/v1/search/embeddings/rebuild",
            json={"force": True},
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["success"])
        self.assertIn("total_evaluated", body["data"])

    # =========================================================================
    # 9. LoopBot Integration Contract
    # =========================================================================

    def test_loopbot_search_spaces_tool_contract(self):
        """Verify LoopBot's search_spaces tool invokes semantic search and returns structured cards."""
        tool_res = LoopBotTools.search_spaces(
            query="quiet room for 3 people under 150",
            budget=150.0,
            capacity=3,
            limit=5,
        )
        self.assertTrue(tool_res["success"])
        self.assertGreater(tool_res["count"], 0)
        spaces = tool_res["spaces"]
        self.assertEqual(spaces[0]["id"], self.space_a.id)
        self.assertIn("match_reasons", spaces[0])
        self.assertIn("parsed_constraints", tool_res)


if __name__ == "__main__":
    unittest.main()
