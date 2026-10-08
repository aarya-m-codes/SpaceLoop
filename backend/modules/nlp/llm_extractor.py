"""LLM-assisted query constraint extractor with automatic deterministic fallback.

Guarantees 100% availability during external AI downtime or network partition.
"""

import json
import logging
import os
from typing import Any

from backend.modules.nlp.parser import QueryParser

logger = logging.getLogger("spaceloop.nlp.llm")


class LLMExtractor:
    """Combines Gemini structured extraction with guaranteed deterministic fallback."""

    @classmethod
    def extract_constraints(cls, query: str | None) -> dict[str, Any]:
        """Extract structured query constraints with zero-hard-dependency fallback."""
        # 1. Deterministic extraction is ALWAYS computed as baseline guarantee
        baseline = QueryParser.parse_query(query)
        if not query or not query.strip():
            return baseline

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return baseline

        # 2. Attempt Gemini extraction if API key configured
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = (
                f"Extract physical space search constraints from this query (English, Hindi, Marathi, Garhwali, Kumaoni, or Jaunsari):\n"
                f"\"{query}\"\n\n"
                f"Respond ONLY with a JSON object containing keys: "
                f"city, neighborhood, date, time, duration_hours, budget, capacity, space_type, amenities, use_case. "
                f"Use null for unspecified fields. For amenities provide list of strings."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            if response and response.text:
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]

                parsed_llm = json.loads(raw_text.strip())

                # Merge LLM nuances on top of verified deterministic baseline
                for key in ["city", "neighborhood", "date", "time", "duration_hours", "budget", "capacity", "space_type", "use_case"]:
                    if parsed_llm.get(key) is not None and baseline.get(key) is None:
                        baseline[key] = parsed_llm[key]

                if parsed_llm.get("amenities") and isinstance(parsed_llm["amenities"], list):
                    for am in parsed_llm["amenities"]:
                        if am and am.lower() not in baseline["amenities"]:
                            baseline["amenities"].append(am.lower())

                baseline["extractor"] = "gemini+deterministic"
                return baseline

        except Exception as exc:
            logger.warning(f"LLM constraint extraction failed ({exc}), gracefully using deterministic parser.")

        baseline["extractor"] = "deterministic"
        return baseline
