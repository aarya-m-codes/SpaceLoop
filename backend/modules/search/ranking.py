"""Composite multi-factor ranking calculator for SpaceLoop discovery.

Implements the conceptual formula:
Score = (wv * S_vector) + (wk * S_keyword) + (wp * S_price) + (wg * S_geo) + (wt * S_trust)
"""

from typing import Any

from backend.core.geo import haversine_distance_km

# Canonical stage-6 ranking weights (sum to 1.00)
WEIGHT_VECTOR = 0.35
WEIGHT_KEYWORD = 0.20
WEIGHT_PRICE = 0.15
WEIGHT_GEO = 0.20
WEIGHT_TRUST = 0.10


class RankingEngine:
    """Calculates composite ranking scores across vector, keyword, price, geo, and trust."""

    @classmethod
    def calculate_score(
        cls,
        s_vector: float,
        s_keyword: float,
        price_per_hour: float,
        budget: float | None,
        space_lat: float,
        space_lng: float,
        user_lat: float | None,
        user_lng: float | None,
        host_trust_score: float | None,
        search_city: str | None = None,
        space_city: str | None = None,
        is_available: bool = True,
    ) -> dict[str, Any]:
        """Compute individual scores, composite score, and detailed diagnostic breakdown."""
        # 1. Vector score: clamped [0.0, 1.0]
        s_vec = max(0.0, min(1.0, float(s_vector)))

        # 2. Keyword score: clamped [0.0, 1.0]
        s_key = max(0.0, min(1.0, float(s_keyword)))

        # 3. Price score: 1.0 inside budget, linearly degrading when over budget
        s_price = cls.calculate_price_score(price_per_hour, budget)

        # 4. Geography score: Haversine distance, 1.0 within 2km, degrade to 0 at 25km
        s_geo, distance_km = cls.calculate_geo_score(
            space_lat=space_lat,
            space_lng=space_lng,
            user_lat=user_lat,
            user_lng=user_lng,
            search_city=search_city,
            space_city=space_city,
        )

        # 5. Trust score: Host Objective Trust Score normalized to [0, 1]
        s_trust = cls.calculate_trust_score(host_trust_score)

        # 6. Composite weighted combination
        raw_score = (
            (WEIGHT_VECTOR * s_vec)
            + (WEIGHT_KEYWORD * s_key)
            + (WEIGHT_PRICE * s_price)
            + (WEIGHT_GEO * s_geo)
            + (WEIGHT_TRUST * s_trust)
        )

        # Availability adjustment: deprioritize booked spaces
        availability_factor = 1.0 if is_available else 0.5
        final_score = round(max(0.0, min(1.0, raw_score * availability_factor)), 4)

        return {
            "score": final_score,
            "breakdown": {
                "s_vector": round(s_vec, 4),
                "s_keyword": round(s_key, 4),
                "s_price": round(s_price, 4),
                "s_geo": round(s_geo, 4),
                "s_trust": round(s_trust, 4),
                "distance_km": round(distance_km, 2) if distance_km is not None else None,
                "is_available": is_available,
            },
        }

    @staticmethod
    def calculate_price_score(price_per_hour: float, budget: float | None) -> float:
        """1.0 when inside budget; linearly degrade toward 0 when over budget."""
        if budget is None or budget <= 0:
            return 1.0

        if price_per_hour <= budget:
            return 1.0

        # Over budget: linear degradation based on percentage over budget
        # e.g., if price is 1.5x budget -> 0.5; if 2.0x budget -> 0.0
        degradation = (price_per_hour - budget) / budget
        score = max(0.0, 1.0 - degradation)
        return round(score, 4)

    @staticmethod
    def calculate_geo_score(
        space_lat: float,
        space_lng: float,
        user_lat: float | None,
        user_lng: float | None,
        search_city: str | None = None,
        space_city: str | None = None,
    ) -> tuple[float, float | None]:
        """Haversine distance score: 1.0 within 2km, linear degradation to 0 at 25km."""
        if user_lat is None or user_lng is None:
            # If no coordinates available, reward city match if present
            if search_city and space_city and search_city.lower() == space_city.lower():
                return 0.75, None
            return 0.50, None

        distance = haversine_distance_km(user_lat, user_lng, space_lat, space_lng)

        if distance <= 2.0:
            score = 1.0
        elif distance >= 25.0:
            score = 0.0
        else:
            # Linear decay from 2km to 25km (23km span)
            score = 1.0 - ((distance - 2.0) / 23.0)

        return round(max(0.0, min(1.0, score)), 4), distance

    @staticmethod
    def calculate_trust_score(host_trust_score: float | None) -> float:
        """Normalize host trust score (0 - 100) to range [0.0, 1.0]."""
        if host_trust_score is None:
            return 1.0  # Default verified baseline
        normalized = max(0.0, min(100.0, float(host_trust_score))) / 100.0
        return round(normalized, 4)
