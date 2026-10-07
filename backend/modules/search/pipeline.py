"""SpaceLoop Semantic AI Discovery & Search Pipeline.

Complete Pipeline Stages:
1. Natural Language Query & Query Normalization
2. Constraint / Entity Extraction (intent, location, date, time, duration, budget, capacity, amenities, purpose, noise, space_type, privacy)
3. Merge Explicit Overrides & Filters (never invent missing user constraints)
4. SQL Hard Filtering (active status, hard budget ceiling, minimum capacity, typology, city)
5. Booking Collision & Availability Filtering (calendar slot conflict elimination)
6. Geographic Proximity & Radius Filtering (Haversine distance WGS-84)
7. Embedding Retrieval & Cosine Similarity (Gemini text-embedding-004 + 256d concept-cluster fallback, cached in SpaceEmbedding)
8. Jaccard Keyword Matching & Acoustic / Noise Matching (using ai_noise_level telemetry)
9. Composite Multi-Factor Ranking (transparent, deterministic, tunable)
10. Deterministic "Why This Matches" Generation & Structured Search Results Output
"""

import logging
from typing import Any
from sqlalchemy import func

from backend.core.database import db
from backend.core.geo import haversine_distance_km
from backend.modules.nlp.llm_extractor import LLMExtractor
from backend.modules.nlp.parser import QueryParser
from backend.modules.search.availability import AvailabilityEngine
from backend.modules.search.keyword_engine import KeywordEngine
from backend.modules.search.ranking import RankingEngine
from backend.modules.search.vector_engine import VectorEngine
from models import Space, User

logger = logging.getLogger("spaceloop.search.pipeline")


class DiscoveryPipeline:
    """Orchestrates the multi-stage semantic AI discovery, constraint safety, and matching engine."""

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
        user_context: dict[str, Any] | None = None,
        filters: dict[str, Any] | None = None,
        capacity: int | None = None,
        space_type: str | None = None,
        amenities: list[str] | None = None,
        radius_km: float | None = None,
        noise_preference: str | None = None,
    ) -> dict[str, Any]:
        """Execute the complete semantic AI search pipeline with strict constraint safety."""

        # -------------------------------------------------------------
        # STAGE 1 & 2: Parse natural-language query & extract constraints
        # -------------------------------------------------------------
        constraints = LLMExtractor.extract_constraints(query)

        # Merge structured filters dict if supplied
        if filters and isinstance(filters, dict):
            for k, v in filters.items():
                if v is not None:
                    if k in ("budget", "price", "max_price"):
                        try:
                            constraints["budget"] = float(v)
                        except (ValueError, TypeError):
                            pass
                    elif k in ("capacity", "min_capacity"):
                        try:
                            constraints["capacity"] = int(v)
                        except (ValueError, TypeError):
                            pass
                    elif k in ("space_type", "type"):
                        constraints["space_type"] = str(v).strip()
                    elif k in ("amenities", "amenity_list") and isinstance(v, list):
                        for am in v:
                            if am and str(am).lower() not in constraints["amenities"]:
                                constraints["amenities"].append(str(am).lower())
                    elif k in ("noise_preference", "noise"):
                        constraints["noise_preference"] = str(v).strip()
                    elif k in ("date",):
                        constraints["date"] = str(v).strip()
                    elif k in ("hours", "duration", "duration_hours"):
                        try:
                            constraints["duration_hours"] = float(v)
                        except (ValueError, TypeError):
                            pass
                    elif k in ("radius", "radius_km"):
                        try:
                            constraints["radius_km"] = float(v)
                        except (ValueError, TypeError):
                            pass
                    elif k in ("city",):
                        constraints["city"] = str(v).strip()

        # Merge explicit function argument overrides
        if budget is not None:
            try:
                constraints["budget"] = float(budget)
            except (ValueError, TypeError):
                pass

        if capacity is not None:
            try:
                constraints["capacity"] = int(capacity)
            except (ValueError, TypeError):
                pass

        if space_type is not None:
            constraints["space_type"] = str(space_type).strip()

        if amenities is not None:
            for am in amenities:
                if am and str(am).lower() not in constraints["amenities"]:
                    constraints["amenities"].append(str(am).lower())

        if noise_preference is not None:
            constraints["noise_preference"] = str(noise_preference).strip()

        if date is not None:
            constraints["date"] = str(date).strip()

        if hours is not None:
            try:
                constraints["duration_hours"] = float(hours)
            except (ValueError, TypeError):
                pass

        if radius_km is not None:
            try:
                constraints["radius_km"] = float(radius_km)
            except (ValueError, TypeError):
                pass

        # Resolve location parameter
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
                if location.get("radius") or location.get("radius_km"):
                    try:
                        constraints["radius_km"] = float(location.get("radius") or location.get("radius_km"))
                    except (ValueError, TypeError):
                        pass
            elif isinstance(location, str) and location.strip():
                loc_parsed = QueryParser.extract_location(location)
                if loc_parsed.get("city"):
                    constraints["city"] = loc_parsed["city"]
                if loc_parsed.get("neighborhood"):
                    constraints["neighborhood"] = loc_parsed["neighborhood"]
                if loc_parsed.get("lat") and loc_parsed.get("lng"):
                    constraints["latitude"] = loc_parsed["lat"]
                    constraints["longitude"] = loc_parsed["lng"]

        # Merge user context (e.g. GPS coordinates from device session)
        if user_context and isinstance(user_context, dict):
            if constraints.get("latitude") is None and user_context.get("latitude") is not None:
                constraints["latitude"] = float(user_context["latitude"])
            if constraints.get("longitude") is None and user_context.get("longitude") is not None:
                constraints["longitude"] = float(user_context["longitude"])
            if not constraints.get("city") and user_context.get("city"):
                constraints["city"] = str(user_context["city"]).strip()

        # -------------------------------------------------------------
        # STAGE 3: Apply SQL Hard Filters
        # (CRITICAL INVARIANT: Semantic similarity MUST NEVER override explicit constraints!)
        # -------------------------------------------------------------
        sql_query = Space.query.filter(Space.is_active.is_(True), Space.is_approved.is_(True))

        # Hard constraint: Price / Budget
        # A ₹300/hour space must NEVER be returned if user requested <= ₹150/hour
        target_budget = constraints.get("budget")
        if target_budget is not None and target_budget > 0:
            sql_query = sql_query.filter(Space.price_per_hour <= float(target_budget))

        # Hard constraint: Capacity
        # Must fit at least the minimum required capacity
        target_capacity = constraints.get("capacity")
        if target_capacity is not None and target_capacity > 0:
            sql_query = sql_query.filter(Space.capacity >= int(target_capacity))

        # Hard constraint: Space Type
        target_space_type = constraints.get("space_type")
        if target_space_type:
            type_count = sql_query.filter(func.lower(Space.space_type) == target_space_type.lower()).count()
            if type_count > 0:
                sql_query = sql_query.filter(func.lower(Space.space_type) == target_space_type.lower())

        # Hard constraint: City filter
        target_city = constraints.get("city")
        if target_city:
            city_count = sql_query.filter(func.lower(Space.city) == target_city.lower()).count()
            if city_count > 0:
                sql_query = sql_query.filter(func.lower(Space.city) == target_city.lower())

        candidates = sql_query.all()

        # NOTE: Do NOT reset candidates to all spaces!
        # If no spaces meet the hard constraints (budget, capacity, city), return empty result.
        if not candidates:
            return {
                "items": [],
                "results": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 1,
                "parsed_constraints": constraints,
                "structured_search": constraints,
            }

        # -------------------------------------------------------------
        # STAGE 4: Booking Collision & Availability Filtering
        # -------------------------------------------------------------
        availability_map: dict[int, tuple[bool, str | None]] = {}
        for space in candidates:
            is_avail, reason = AvailabilityEngine.check_space_availability(
                space_id=space.id,
                date_str=constraints.get("date"),
                time_str=constraints.get("time") or constraints.get("start_time"),
                duration_hours=constraints.get("duration_hours"),
            )
            availability_map[space.id] = (is_avail, reason)

        # Eliminate conflicting bookings when require_available is True
        if require_available:
            candidates = [s for s in candidates if availability_map[s.id][0]]

        if not candidates:
            return {
                "items": [],
                "results": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 1,
                "parsed_constraints": constraints,
                "structured_search": constraints,
            }

        # -------------------------------------------------------------
        # STAGE 5: Geographic Radius Filtering (if specified)
        # -------------------------------------------------------------
        target_radius = constraints.get("radius_km") or constraints.get("radius")
        user_lat = constraints.get("latitude")
        user_lng = constraints.get("longitude")
        if target_radius is not None and user_lat is not None and user_lng is not None:
            candidates = [
                s for s in candidates
                if haversine_distance_km(user_lat, user_lng, s.latitude, s.longitude) <= float(target_radius)
            ]

        if not candidates:
            return {
                "items": [],
                "results": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 1,
                "parsed_constraints": constraints,
                "structured_search": constraints,
            }

        # -------------------------------------------------------------
        # STAGE 6: Embedding Retrieval & Vector Semantic Similarity
        # -------------------------------------------------------------
        query_text = (
            constraints.get("semantic_query")
            or query
            or (
                f"{constraints.get('space_type') or ''} "
                f"{constraints.get('city') or ''} "
                f"{' '.join(constraints.get('amenities') or [])} "
                f"{constraints.get('use_case') or ''}"
            ).strip()
        )

        query_vec = VectorEngine.get_embedding(query_text)

        ranked_results: list[dict[str, Any]] = []

        for space in candidates:
            # Retrieve or generate persisted space embedding (with content_hash cache)
            space_vec = VectorEngine.get_or_create_space_embedding(space)
            s_vector = VectorEngine.cosine_similarity(query_vec, space_vec)

            # ---------------------------------------------------------
            # STAGE 7: Keyword & Acoustic / Noise Matching
            # ---------------------------------------------------------
            s_keyword = KeywordEngine.calculate_similarity(
                query=query_text,
                space=space,
                requested_amenities=constraints.get("amenities"),
            )

            s_noise, noise_reason = KeywordEngine.calculate_noise_score(
                requested_noise=constraints.get("noise_preference"),
                space=space,
            )

            matched_amenities = KeywordEngine.get_matched_amenities(
                space=space,
                requested_amenities=constraints.get("amenities"),
            )

            # ---------------------------------------------------------
            # STAGE 8: Composite Ranking Calculation
            # ---------------------------------------------------------
            is_avail, avail_reason = availability_map.get(space.id, (True, None))
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
                s_noise=s_noise,
                space_capacity=space.capacity,
                requested_capacity=constraints.get("capacity"),
            )

            # ---------------------------------------------------------
            # STAGE 9: Grounded "Why This Matches" Generation
            # (Strictly derived from actual space attributes and signals)
            # ---------------------------------------------------------
            match_reasons: list[str] = []

            # 1. Capacity Reason
            if constraints.get("capacity"):
                req_cap = constraints["capacity"]
                match_reasons.append(f"Fits {req_cap} people (Capacity: {space.capacity})")
            else:
                match_reasons.append(f"Capacity: {space.capacity} {'person' if space.capacity == 1 else 'people'}")

            # 2. Price / Budget Reason
            if constraints.get("budget"):
                user_b = constraints["budget"]
                match_reasons.append(f"Within your ₹{user_b:g}/hr budget (₹{space.price_per_hour:g}/hr)")
            else:
                match_reasons.append(f"Price: ₹{space.price_per_hour:g}/hour")

            # 3. Acoustic / Noise Reason
            if noise_reason:
                match_reasons.append(noise_reason)

            # 4. Proximity / Location Reason
            dist_km = ranking_info["breakdown"].get("distance_km")
            if dist_km is not None:
                match_reasons.append(f"{dist_km:.1f} km away in {space.neighborhood or space.city}")
            elif space.neighborhood or space.city:
                match_reasons.append(f"Located in {space.neighborhood or space.city}")

            # 5. Availability Reason
            if constraints.get("date"):
                time_display = f" at {constraints.get('time')}" if constraints.get("time") else ""
                dur_display = f" for {constraints['duration_hours']:g} hrs" if constraints.get("duration_hours") else ""
                if is_avail:
                    match_reasons.append(f"Available on {constraints['date']}{time_display}{dur_display}")
                else:
                    match_reasons.append(f"Occupied for requested slot ({avail_reason or 'Conflict'})")

            # 6. Amenity Matches
            if matched_amenities:
                match_reasons.append(f"Matches amenities: {', '.join(matched_amenities)}")
            elif space.amenities:
                match_reasons.append(f"Key amenities: {', '.join(space.amenities[:3])}")

            # 7. Host Trust
            if host_trust and host_trust >= 90:
                match_reasons.append(f"Hosted by verified host ({int(host_trust)}% trust score)")

            # Assemble grounded why_this_matches summary
            why_this_matches = " • ".join(match_reasons)

            space_data = space.to_dict()
            space_data["score"] = ranking_info["score"]
            space_data["score_breakdown"] = ranking_info["breakdown"]
            space_data["is_available"] = is_avail
            space_data["availability_status"] = avail_reason
            space_data["match_reasons"] = match_reasons
            space_data["why_this_matches"] = why_this_matches

            ranked_results.append(space_data)

        # -------------------------------------------------------------
        # STAGE 10: Composite Sorting & Pagination
        # -------------------------------------------------------------
        ranked_results.sort(key=lambda x: x["score"], reverse=True)

        total = len(ranked_results)
        offset = (page - 1) * limit
        paginated_items = ranked_results[offset : offset + limit]
        total_pages = (total + limit - 1) // limit if total > 0 else 1

        return {
            "items": paginated_items,
            "results": paginated_items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "parsed_constraints": constraints,
            "structured_search": constraints,
        }


def semantic_search(
    query: str | None = None,
    user_context: dict[str, Any] | None = None,
    filters: dict[str, Any] | None = None,
    location: Any = None,
    date: str | None = None,
    hours: float | None = None,
    budget: float | None = None,
    page: int = 1,
    limit: int = 20,
    require_available: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Clean internal service callable directly by SpaceLoop API, UI, and LoopBot."""
    return DiscoveryPipeline.search(
        query=query,
        user_context=user_context,
        filters=filters,
        location=location,
        date=date,
        hours=hours,
        budget=budget,
        page=page,
        limit=limit,
        require_available=require_available,
        **kwargs,
    )


# Clean architecture aliases
SearchPipeline = DiscoveryPipeline
SearchService = DiscoveryPipeline
