"""Six-stage hybrid discovery pipeline for SpaceLoop.

Pipeline Stages:
1. Parse natural-language query.
2. Extract structured constraints.
3. Apply SQL hard filters.
4. Calculate booking availability.
5. Calculate semantic similarity (Vector + Keyword).
6. Calculate composite ranking (S_vector, S_keyword, S_price, S_geo, S_trust).
"""

import logging
from typing import Any
from sqlalchemy import func

from backend.core.database import db
from backend.modules.nlp.llm_extractor import LLMExtractor
from backend.modules.nlp.parser import QueryParser
from backend.modules.search.availability import AvailabilityEngine
from backend.modules.search.keyword_engine import KeywordEngine
from backend.modules.search.ranking import RankingEngine
from backend.modules.search.vector_engine import VectorEngine
from models import Space, User

logger = logging.getLogger("spaceloop.search.pipeline")


class DiscoveryPipeline:
    """Orchestrates the six-stage hybrid discovery, NLP search, and matching engine."""

    @classmethod
    def search(
        cls,
        query: str | None = None,
        date: str | None = None,
        hours: float | None = None,
        budget: float | None = None,
        location: Any = None,
        page: int = 1,
        limit: int = 20,
        require_available: bool = False,
    ) -> dict[str, Any]:
        """Execute the six-stage hybrid search pipeline."""

        # -------------------------------------------------------------
        # STAGE 1 & 2: Parse natural-language query & extract constraints
        # -------------------------------------------------------------
        constraints = LLMExtractor.extract_constraints(query)

        # Merge explicit request overrides
        if budget is not None:
            try:
                constraints["budget"] = float(budget)
            except (ValueError, TypeError):
                pass

        if date is not None:
            constraints["date"] = str(date).strip()

        if hours is not None:
            try:
                constraints["duration_hours"] = float(hours)
            except (ValueError, TypeError):
                pass

        if location is not None:
            if isinstance(location, dict):
                lat = location.get("lat") or location.get("latitude")
                lng = location.get("lng") or location.get("longitude")
                if lat is not None and lng is not None:
                    constraints["latitude"] = float(lat)
                    constraints["longitude"] = float(lng)
                if location.get("city"):
                    constraints["city"] = str(location["city"]).strip()
                if location.get("neighborhood"):
                    constraints["neighborhood"] = str(location["neighborhood"]).strip()
            elif isinstance(location, str) and location.strip():
                loc_parsed = QueryParser.extract_location(location)
                if loc_parsed.get("city"):
                    constraints["city"] = loc_parsed["city"]
                if loc_parsed.get("neighborhood"):
                    constraints["neighborhood"] = loc_parsed["neighborhood"]
                if loc_parsed.get("lat") and loc_parsed.get("lng"):
                    constraints["latitude"] = loc_parsed["lat"]
                    constraints["longitude"] = loc_parsed["lng"]

        # -------------------------------------------------------------
        # STAGE 3: Apply SQL hard filters
        # -------------------------------------------------------------
        sql_query = Space.query.filter(Space.is_active.is_(True), Space.is_approved.is_(True))

        target_city = constraints.get("city")
        if target_city:
            # Check if matching spaces exist in this city
            city_count = sql_query.filter(func.lower(Space.city) == target_city.lower()).count()
            if city_count > 0:
                sql_query = sql_query.filter(func.lower(Space.city) == target_city.lower())

        target_capacity = constraints.get("capacity")
        if target_capacity and target_capacity > 1:
            sql_query = sql_query.filter(Space.capacity >= target_capacity)

        target_space_type = constraints.get("space_type")
        if target_space_type:
            type_count = sql_query.filter(func.lower(Space.space_type) == target_space_type.lower()).count()
            if type_count > 0:
                sql_query = sql_query.filter(func.lower(Space.space_type) == target_space_type.lower())

        candidates = sql_query.all()

        # Fallback if hard filtering eliminated all spaces
        if not candidates:
            candidates = Space.query.filter(Space.is_active.is_(True)).all()

        # -------------------------------------------------------------
        # STAGE 4: Calculate booking availability
        # -------------------------------------------------------------
        availability_map: dict[int, tuple[bool, str | None]] = {}
        for space in candidates:
            is_avail, reason = AvailabilityEngine.check_space_availability(
                space_id=space.id,
                date_str=constraints.get("date"),
                time_str=constraints.get("time"),
                duration_hours=constraints.get("duration_hours"),
            )
            availability_map[space.id] = (is_avail, reason)

        if require_available:
            candidates = [s for s in candidates if availability_map[s.id][0]]

        # -------------------------------------------------------------
        # STAGE 5 & 6: Semantic similarity & Composite ranking
        # -------------------------------------------------------------
        query_text = query or (
            f"{constraints.get('space_type') or ''} "
            f"{constraints.get('city') or ''} "
            f"{' '.join(constraints.get('amenities') or [])} "
            f"{constraints.get('use_case') or ''}"
        ).strip()

        # Vector embedding of the search query
        query_vec = VectorEngine.get_embedding(query_text)

        ranked_results: list[dict[str, Any]] = []

        for space in candidates:
            # Stage 5A: Vector similarity
            space_doc = VectorEngine.build_space_document(space)
            space_vec = VectorEngine.get_embedding(space_doc)
            s_vector = VectorEngine.cosine_similarity(query_vec, space_vec)

            # Stage 5B: Keyword similarity
            s_keyword = KeywordEngine.calculate_similarity(
                query=query_text,
                space=space,
                requested_amenities=constraints.get("amenities"),
            )

            # Stage 6: Composite ranking calculation
            is_avail, avail_reason = availability_map.get(space.id, (True, None))

            # Retrieve host trust score
            host_trust = space.host.trust_score if space.host else 100.0

            ranking_info = RankingEngine.calculate_score(
                s_vector=s_vector,
                s_keyword=s_keyword,
                price_per_hour=space.price_per_hour,
                budget=constraints.get("budget"),
                space_lat=space.latitude,
                space_lng=space.longitude,
                user_lat=constraints.get("latitude"),
                user_lng=constraints.get("longitude"),
                host_trust_score=host_trust,
                search_city=constraints.get("city"),
                space_city=space.city,
                is_available=is_avail,
            )

            space_data = space.to_dict()
            space_data["score"] = ranking_info["score"]
            space_data["score_breakdown"] = ranking_info["breakdown"]
            space_data["is_available"] = is_avail
            space_data["availability_status"] = avail_reason

            ranked_results.append(space_data)

        # Sort descending by composite score
        ranked_results.sort(key=lambda x: x["score"], reverse=True)

        # Pagination
        total = len(ranked_results)
        offset = (page - 1) * limit
        paginated_items = ranked_results[offset : offset + limit]
        total_pages = (total + limit - 1) // limit if total > 0 else 1

        return {
            "items": paginated_items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "parsed_constraints": constraints,
        }
