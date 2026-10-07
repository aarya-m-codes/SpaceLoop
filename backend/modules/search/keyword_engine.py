"""Keyword similarity engine for SpaceLoop.

Calculates Jaccard and token overlap across amenities, noise, vibe, typology, and listing content.
"""

import re
from typing import Any

from backend.modules.nlp.lexicons import AMENITY_SYNONYMS


class KeywordEngine:
    """Calculates lexical and token overlap similarity between search queries and space listings."""

    @classmethod
    def calculate_noise_score(
        cls,
        requested_noise: str | None,
        space: Any,
    ) -> tuple[float, str]:
        """Compute acoustic match score and explanatory diagnostic message.

        Understands semantic relationships:
        - quiet, peaceful, low noise, study-friendly, focused work
        - meeting, social, lively, collaborative
        Explicitly handles missing noise data rather than assuming or inventing.
        """
        if not requested_noise:
            return 1.0, "No acoustic preference requested."

        raw_noise = getattr(space, "ai_noise_level", None)
        if not raw_noise or not str(raw_noise).strip():
            # Explicit handling for unrecorded noise: never invent data
            return 0.50, "Acoustic level unverified (no noise telemetry recorded)."

        noise_lower = str(raw_noise).lower()
        requested = requested_noise.lower()

        # Target: Quiet / Silent / Study-friendly / Peaceful
        if requested in ("quiet", "silent", "peaceful", "study", "low noise", "focused work"):
            if any(term in noise_lower for term in ("isolated", "<30db", "<32db", "<35db", "whisper", "soundproof", "silent", "quiet")):
                return 1.0, f"Verified quiet environment ({raw_noise})."
            elif any(term in noise_lower for term in ("<40db", "<42db", "<45db", "low")):
                return 0.85, f"Low-noise environment ({raw_noise})."
            elif any(term in noise_lower for term in ("moderate", "<55db", "50-60db", "open floor")):
                return 0.35, f"Moderate noise environment ({raw_noise}) - ambient floor chatter."
            elif any(term in noise_lower for term in ("lively", "active", "social", "high")):
                return 0.10, f"Lively active environment ({raw_noise}) - not ideal for silent study."
            return 0.60, f"Acoustic profile: {raw_noise}."

        # Target: Lively / Social / Meeting / Collaborative
        elif requested in ("lively", "social", "active", "meeting", "collaborative"):
            if any(term in noise_lower for term in ("lively", "active", "social", "open floor", "moderate")):
                return 1.0, f"Vibrant collaborative environment ({raw_noise})."
            elif getattr(space, "space_type", "") in ("meeting_room", "conference", "studio"):
                return 0.90, f"Enclosed space suitable for discussion ({raw_noise})."
            elif any(term in noise_lower for term in ("whisper", "silent", "isolated")):
                return 0.60, f"Isolated quiet space ({raw_noise}) - suitable for confidential discussions."
            return 0.80, f"Acoustic profile: {raw_noise}."

        # Target: Moderate / Normal
        elif requested in ("moderate", "normal", "medium"):
            if any(term in noise_lower for term in ("moderate", "open floor", "<55db")):
                return 1.0, f"Balanced moderate acoustics ({raw_noise})."
            return 0.80, f"Acoustic profile: {raw_noise}."

        return 0.70, f"Acoustic profile: {raw_noise}."

    @classmethod
    def get_matched_amenities(cls, space: Any, requested_amenities: list[str] | None) -> list[str]:
        """Return list of matched requested amenities."""
        if not requested_amenities:
            return []
        space_amenities_lower = [a.lower() for a in (getattr(space, "amenities", []) or [])]
        matched = []
        for req in requested_amenities:
            req_lower = req.lower()
            req_syns = AMENITY_SYNONYMS.get(req_lower, [req_lower])
            for syn in req_syns:
                if any(syn in a for a in space_amenities_lower):
                    matched.append(req.title())
                    break
                # Check noise field for quiet
                if req_lower == "quiet" and space.ai_noise_level and any(q in space.ai_noise_level.lower() for q in ("quiet", "silent", "soundproof")):
                    matched.append("Quiet")
                    break
        return matched

    @classmethod
    def calculate_similarity(
        cls,
        query: str,
        space: Any,
        requested_amenities: list[str] | None = None,
    ) -> float:
        """Calculate Jaccard and weighted feature overlap score bounded in [0.0, 1.0]."""
        q_tokens = cls._tokenize(query)
        if not q_tokens:
            return 0.5  # Neutral baseline for empty queries

        s_tokens = cls._extract_space_tokens(space)
        if not s_tokens:
            return 0.0

        # 1. Base Token Jaccard coefficient
        intersection = q_tokens.intersection(s_tokens)
        union = q_tokens.union(s_tokens)
        jaccard = len(intersection) / len(union) if union else 0.0

        # 2. Amenity coverage boost
        amenity_score = 1.0
        if requested_amenities:
            matched_amenities = cls.get_matched_amenities(space, requested_amenities)
            amenity_score = len(matched_amenities) / len(requested_amenities)
            # Weighted combination: 40% Jaccard + 60% amenity coverage
            composite_keyword = (0.4 * min(1.0, jaccard * 2.5)) + (0.6 * amenity_score)
        else:
            # Scaled Jaccard (raw Jaccard is typically between 0.1 and 0.4 due to long descriptions)
            composite_keyword = min(1.0, jaccard * 3.0)

        return round(max(0.0, min(1.0, composite_keyword)), 4)

    @classmethod
    def _tokenize(cls, text: str | None) -> set[str]:
        if not text:
            return set()
        words = re.findall(r"\w+", text.lower())
        # Filter common non-informative English/Hindi/Marathi stop words
        stopwords = {
            "a", "an", "the", "in", "on", "at", "for", "with", "and", "or",
            "me", "mein", "ko", "ke", "ka", "ki", "se", "par", "hai", "chahiye",
            "madhe", "yethe", "javal", "sathi", "ani", "sobat", "pahije", "aahe",
        }
        return {w for w in words if len(w) > 1 and w not in stopwords}

    @classmethod
    def _extract_space_tokens(cls, space: Any) -> set[str]:
        """Aggregate all textual fields of a space into a comprehensive token set."""
        tokens: set[str] = set()

        fields_to_tokenize = [
            space.title,
            space.description,
            space.space_type,
            space.category,
            space.neighborhood,
            space.city,
            space.ai_lighting,
            space.ai_noise_level,
            space.ai_power_access,
        ]

        for field in fields_to_tokenize:
            if field:
                tokens.update(cls._tokenize(str(field)))

        if space.amenities and isinstance(space.amenities, list):
            for amenity in space.amenities:
                tokens.update(cls._tokenize(str(amenity)))

        if space.recommended_uses and isinstance(space.recommended_uses, list):
            for use in space.recommended_uses:
                tokens.update(cls._tokenize(str(use)))

        return tokens
