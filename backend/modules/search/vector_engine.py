"""Vector semantic similarity engine for SpaceLoop.

Supports:
1. Google Gemini text embeddings (when GEMINI_API_KEY is available)
2. Deterministic 256-dimensional concept-cluster hash vectorizer (guaranteed fallback)
"""

import hashlib
import logging
import math
import os
import re
from typing import Any

from backend.modules.nlp.parser import QueryParser

logger = logging.getLogger("spaceloop.search.vector")

# Vector dimension for deterministic concept space
VECTOR_DIM = 256

# Core semantic concept clusters mapped to dedicated dimensions
SEMANTIC_CLUSTERS: list[tuple[str, list[str]]] = [
    # Workspaces
    ("desk_workspace", ["desk", "hotdesk", "workstation", "mej", "table", "chair", "seat", "coworking"]),
    ("private_room", ["room", "cabin", "kamra", "kholi", "office", "enclosed", "private"]),
    ("meeting_room", ["meeting", "conference", "boardroom", "baithak", "discussion", "presentation", "pitch"]),
    ("studio_creative", ["studio", "podcast", "recording", "audio", "voiceover", "video", "photoshoot", "filming"]),
    ("commercial_retail", ["commercial", "retail", "shop", "dukaan", "showroom", "hall", "event"]),

    # Amenities & Physical Attributes
    ("high_speed_internet", ["wifi", "internet", "broadband", "fiber", "speed", "net", "connection"]),
    ("air_conditioning", ["ac", "aircon", "air", "conditioning", "cool", "hawa"]),
    ("parking_facility", ["parking", "valet", "car", "bike", "vehicle"]),
    ("power_backup", ["power", "backup", "generator", "inverter", "ups", "electricity", "socket", "plug"]),
    ("quiet_acoustics", ["quiet", "silent", "soundproof", "peaceful", "shant", "whisper", "calm", "silence", "isolated"]),
    ("projector_display", ["projector", "screen", "display", "tv", "monitor", "4k"]),
    ("whiteboard", ["whiteboard", "board", "marker", "fala"]),
    ("coffee_beverages", ["coffee", "tea", "chai", "espresso", "pantry", "cafe", "beverages"]),
    ("restroom", ["washroom", "restroom", "toilet", "bathroom"]),
    ("ergonomics", ["ergonomic", "herman", "miller", "lumbar", "comfortable"]),

    # Activities & Use Cases
    ("software_engineering", ["coding", "programming", "software", "developer", "hackathon", "tech", "code"]),
    ("academic_study", ["study", "exam", "reading", "padhai", "abhyas", "learning", "student", "book"]),
    ("audio_production", ["podcast", "recording", "voiceover", "mic", "microphone", "sound"]),
    ("visual_production", ["photoshoot", "photography", "camera", "lighting", "model", "shoot"]),
    ("business_meeting", ["client", "interview", "sync", "team", "sprint", "planning", "strategy"]),
    ("workshop_training", ["workshop", "training", "seminar", "class", "meetup"]),

    # Geospatial Metro Hubs
    ("bengaluru_hub", ["bengaluru", "bangalore", "blr", "indiranagar", "koramangala", "whitefield", "hsr"]),
    ("mumbai_hub", ["mumbai", "bombay", "bom", "bkc", "bandra", "andheri", "parel", "powai"]),
    ("delhi_hub", ["delhi", "new delhi", "del", "ncr", "connaught", "cp", "hauz", "khas", "gurgaon", "cyber"]),
    ("pune_hub", ["pune", "poona", "kothrud", "hinjewadi", "viman", "baner"]),
    ("hyderabad_hub", ["hyderabad", "hyd", "gachibowli", "hitec"]),

    # Vibes
    ("deep_focus", ["focus", "deep", "uninterrupted", "productive", "work"]),
    ("collaborative_vibe", ["collaborative", "lively", "vibrant", "energetic", "networking"]),
    ("premium_luxury", ["premium", "luxury", "executive", "modern", "aesthetic", "upscale"]),
]


class VectorEngine:
    """Vector similarity calculator supporting Gemini Embeddings with deterministic fallback."""

    @classmethod
    def get_embedding(cls, text: str) -> list[float]:
        """Compute normalized vector embedding for given text."""
        cleaned = QueryParser.normalize_text(text)
        if not cleaned:
            return [0.0] * VECTOR_DIM

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=cleaned,
                )
                if response and hasattr(response, "embedding") and response.embedding:
                    emb = list(response.embedding.values)
                    return cls._normalize_vector(emb)
            except Exception as exc:
                logger.debug(f"Gemini embedding API unavailable ({exc}), using deterministic vectorizer.")

        return cls.get_deterministic_embedding(cleaned)

    @classmethod
    def get_deterministic_embedding(cls, text: str) -> list[float]:
        """Generate deterministic 256-dimensional concept-cluster hash vector.
        
        Guarantees reproducible, ultra-fast vector representations across space documents and queries.
        """
        vec = [0.0] * VECTOR_DIM
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return vec

        # 1. Project domain concept clusters into dedicated primary dimensions [0, len(SEMANTIC_CLUSTERS)-1]
        for c_idx, (cluster_name, terms) in enumerate(SEMANTIC_CLUSTERS):
            for term in terms:
                # Substring match in cleaned text
                if term in text:
                    vec[c_idx] += 3.0
                # Exact token match
                for token in tokens:
                    if token == term:
                        vec[c_idx] += 4.0

        # 2. Hashing trick for all tokens and bi-grams into dims [len(SEMANTIC_CLUSTERS), 255]
        hash_start = len(SEMANTIC_CLUSTERS)
        hash_len = VECTOR_DIM - hash_start

        for i, token in enumerate(tokens):
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16)
            dim = hash_start + (h % hash_len)
            vec[dim] += 1.0

            if i < len(tokens) - 1:
                bigram = f"{token}_{tokens[i+1]}"
                h_bi = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest()[:8], 16)
                dim_bi = hash_start + (h_bi % hash_len)
                vec[dim_bi] += 1.5

        return cls._normalize_vector(vec)

    @classmethod
    def cosine_similarity(cls, vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two vectors, bounded in [0.0, 1.0]."""
        if not vec_a or not vec_b:
            return 0.0

        # If dimensions differ (e.g. Gemini high-dim vs 256-dim), handle gracefully
        min_dim = min(len(vec_a), len(vec_b))
        dot_product = sum(vec_a[i] * vec_b[i] for i in range(min_dim))

        norm_a = math.sqrt(sum(x * x for x in vec_a[:min_dim]))
        norm_b = math.sqrt(sum(y * y for y in vec_b[:min_dim]))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        sim = dot_product / (norm_a * norm_b)
        return max(0.0, min(1.0, float(sim)))

    @staticmethod
    def _normalize_vector(vec: list[float]) -> list[float]:
        """L2-normalize vector to unit length."""
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0.0:
            return vec
        return [round(x / norm, 6) for x in vec]

    @classmethod
    def build_space_document(cls, space: Any) -> str:
        """Serialize space entity attributes into rich semantic representation for embedding."""
        amenities_str = ", ".join(space.amenities) if space.amenities else ""
        recommended_uses_str = ", ".join(space.recommended_uses) if space.recommended_uses else ""
        doc_parts = [
            space.title or "",
            space.description or "",
            space.space_type or "",
            space.category or "",
            space.neighborhood or "",
            space.city or "",
            space.address_line1 or "",
            f"Amenities: {amenities_str}",
            f"Lighting: {space.ai_lighting or ''}",
            f"Noise level: {space.ai_noise_level or ''}",
            f"Power access: {space.ai_power_access or ''}",
            f"Recommended uses: {recommended_uses_str}",
            space.rules or "",
        ]
        return " ".join(filter(None, doc_parts))
