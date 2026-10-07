"""Keyword similarity engine for SpaceLoop.

Calculates Jaccard and token overlap across amenities, noise, vibe, typology, and listing content.
"""

import re
from typing import Any

from backend.modules.nlp.lexicons import AMENITY_SYNONYMS


class KeywordEngine:
    """Calculates lexical and token overlap similarity between search queries and space listings."""

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
            space_amenities_lower = [a.lower() for a in (space.amenities or [])]
            # Check matches across space amenities, description, and acoustics
            matched_amenities = 0
            for req in requested_amenities:
                req_synonyms = AMENITY_SYNONYMS.get(req, [req])
                has_match = False
                for syn in req_synonyms:
                    if any(syn in a for a in space_amenities_lower):
                        has_match = True
                        break
                    # Also check noise/lighting fields for quiet/acoustics/lighting
                    if req == "quiet" and space.ai_noise_level and ("quiet" in space.ai_noise_level.lower() or "sound" in space.ai_noise_level.lower()):
                        has_match = True
                        break
                if has_match:
                    matched_amenities += 1

            amenity_score = matched_amenities / len(requested_amenities)
            # Weighted combination: 50% Jaccard + 50% amenity coverage
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
