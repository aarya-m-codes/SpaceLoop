"""AI Matching and Recommendation Explainer for SpaceLoop.

Generates structured match explanations for top recommended spaces.
Guarantees 100% deterministic fallback during AI downtime.
"""

import logging
import os
from typing import Any

from backend.modules.search.pipeline import DiscoveryPipeline

logger = logging.getLogger("spaceloop.search.matcher")


class AIMatcher:
    """Matches spaces and synthesizes human-readable match explanations."""

    @classmethod
    def match(
        cls,
        query: str | None = None,
        date: str | None = None,
        hours: float | None = None,
        budget: float | None = None,
        location: Any = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Execute hybrid search and generate top matches with natural language explanation."""
        search_res = DiscoveryPipeline.search(
            query=query,
            date=date,
            hours=hours,
            budget=budget,
            location=location,
            page=1,
            limit=top_k,
        )

        top_matches = search_res.get("items", [])
        constraints = search_res.get("parsed_constraints", {})

        # Generate explanation
        explanation = cls.generate_match_explanation(
            query=query,
            constraints=constraints,
            top_matches=top_matches,
        )

        return {
            "top_matches": top_matches,
            "match_explanation": explanation,
            "parsed_constraints": constraints,
            "total_matches": search_res.get("total", 0),
        }

    @classmethod
    def generate_match_explanation(
        cls,
        query: str | None,
        constraints: dict[str, Any],
        top_matches: list[dict[str, Any]],
    ) -> str:
        """Synthesize match rationale using Gemini if available, with deterministic fallback."""
        if not top_matches:
            return "No matching spaces currently available matching all requested criteria. Try expanding your search radius or budget."

        best_match = top_matches[0]
        api_key = os.getenv("GEMINI_API_KEY")

        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                summary_context = (
                    f"User Query: {query}\n"
                    f"Top Match: {best_match.get('title')} in {best_match.get('neighborhood')}, {best_match.get('city')}\n"
                    f"Hourly Price: INR {best_match.get('hourly_price')}\n"
                    f"Amenities: {best_match.get('amenities')}\n"
                    f"Noise Level: {best_match.get('ai_noise_level')}\n"
                    f"Distance: {best_match.get('score_breakdown', {}).get('distance_km')} km\n"
                    f"Host Trust Score: {best_match.get('score_breakdown', {}).get('s_trust', 1.0) * 100}%\n"
                )
                prompt = (
                    f"You are SpaceLoop AI Assistant. Write a concise, 2-sentence explanation of why this space "
                    f"is the top recommendation for the user's physical space search.\n\n{summary_context}"
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as exc:
                logger.warning(f"Gemini match explanation failed ({exc}), engaging deterministic generator.")

        # Deterministic explanation generator
        return cls._deterministic_explanation(query, constraints, best_match, len(top_matches))

    @staticmethod
    def _deterministic_explanation(
        query: str | None,
        constraints: dict[str, Any],
        best: dict[str, Any],
        total_found: int,
    ) -> str:
        """Construct deterministic explanation tailored to matched criteria."""
        title = best.get("title", "this space")
        neighborhood = best.get("neighborhood") or best.get("city", "the area")
        city = best.get("city", "India")
        price = best.get("hourly_price", 0.0)
        breakdown = best.get("score_breakdown", {})
        distance = breakdown.get("distance_km")

        parts = []

        # Location & title
        loc_str = f"in {neighborhood}, {city}" if neighborhood != city else f"in {city}"
        if distance is not None:
            parts.append(f"'{title}' is your top match {loc_str} (approx. {distance} km away).")
        else:
            parts.append(f"'{title}' is your top match {loc_str}.")

        # Price / Budget
        user_budget = constraints.get("budget")
        if user_budget and price <= user_budget:
            parts.append(f"At ₹{price:g}/hr, it sits comfortably within your ₹{user_budget:g} budget.")
        else:
            parts.append(f"It is available at ₹{price:g}/hr.")

        # Capacity
        user_cap = constraints.get("capacity")
        space_cap = best.get("capacity")
        if user_cap and space_cap:
            parts.append(f"Fits your group of {user_cap} (Capacity: {space_cap}).")

        # Amenities / Environment
        amenities = best.get("amenities") or []
        noise = best.get("ai_noise_level")
        if noise and ("quiet" in noise.lower() or "sound" in noise.lower()):
            parts.append(f"It features verified quiet acoustics ({noise}) and key amenities ({', '.join(amenities[:3])}).")
        elif amenities:
            parts.append(f"It provides essential amenities including {', '.join(amenities[:3])}.")

        # Availability
        if best.get("is_available") is False:
            parts.append("Note: currently occupied for requested time slot.")

        # Trust score
        trust_val = breakdown.get("s_trust", 1.0)
        trust_pct = int(trust_val * 100)
        if trust_pct >= 90:
            parts.append(f"Hosted by a verified host with a {trust_pct}% trust score.")

        return " ".join(parts)
