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
        emb, _ = cls.get_embedding_with_metadata(text)
        return emb

    @classmethod
    def get_embedding_with_metadata(cls, text: str) -> tuple[list[float], str]:
        """Compute normalized vector embedding and return with model identifier."""
        cleaned = QueryParser.normalize_text(text)
        if not cleaned:
            return [0.0] * VECTOR_DIM, "deterministic-concept-256"

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
                    return cls._normalize_vector(emb), "text-embedding-004"
            except Exception as exc:
                logger.debug(f"Gemini embedding API unavailable ({exc}), using deterministic vectorizer.")

        return cls.get_deterministic_embedding(cleaned), "deterministic-concept-256"

    @classmethod
    def get_or_create_space_embedding(
        cls,
        space: Any,
        force_rebuild: bool = False,
    ) -> list[float]:
        """Retrieve persisted embedding for space, or generate, persist, and return it.

        Avoids regenerating unchanged embeddings by checking SHA-256 content_hash.
        """
        doc = cls.build_space_document(space)
        content_hash = hashlib.sha256(doc.encode("utf-8")).hexdigest()

        # Check existing embedding in database
        try:
            from backend.core.database import db
            from models import SpaceEmbedding

            existing = SpaceEmbedding.query.filter_by(space_id=space.id).first()
            if existing and not force_rebuild:
                if existing.content_hash == content_hash and existing.embedding:
                    return list(existing.embedding)
        except Exception as exc:
            logger.debug(f"Could not load persisted embedding ({exc}), calculating in-memory.")
            existing = None

        # Compute new embedding with model tracking
        emb, model_name = cls.get_embedding_with_metadata(doc)

        # Persist to database if db session available
        try:
            from backend.core.database import db
            from models import SpaceEmbedding

            if existing:
                existing.embedding = emb
                existing.embedding_model = model_name
                existing.embedding_version = "v1"
                existing.content_hash = content_hash
            else:
                new_record = SpaceEmbedding(
                    space_id=space.id,
                    embedding=emb,
                    embedding_model=model_name,
                    embedding_version="v1",
                    content_hash=content_hash,
                )
                db.session.add(new_record)
            db.session.commit()
        except Exception as exc:
            logger.debug(f"Failed to persist space embedding to database ({exc}).")

        return emb

    @classmethod
    def rebuild_embeddings(
        cls,
        space_id: int | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Safely rebuild or update persisted embeddings for spaces.

        If space_id is given, rebuilds that space only.
        If force is True, regenerates even if content_hash matches.
        """
        from models import Space, SpaceEmbedding

        if space_id:
            spaces = Space.query.filter_by(id=space_id).all()
        else:
            spaces = Space.query.filter_by(is_active=True).all()

        total = len(spaces)
        updated = 0
        skipped = 0

        for sp in spaces:
            doc = cls.build_space_document(sp)
            content_hash = hashlib.sha256(doc.encode("utf-8")).hexdigest()
            existing = SpaceEmbedding.query.filter_by(space_id=sp.id).first()
            if existing and not force and existing.content_hash == content_hash and existing.embedding:
                skipped += 1
                continue
            cls.get_or_create_space_embedding(sp, force_rebuild=True)
            updated += 1

        return {
            "total_evaluated": total,
            "updated": updated,
            "skipped": skipped,
            "force": force,
        }

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
        """Serialize space entity attributes into rich semantic representation for embedding.

        Conforms to SpaceLoop dossier:
        "Quiet private workspace suitable for focused study and laptop work.
         Capacity: 4 people. Amenities: Wi-Fi, desk, power outlet. Noise: low. Privacy: private."
        """
        amenities_str = ", ".join(space.amenities) if space.amenities else "none specified"
        recommended_uses_str = ", ".join(space.recommended_uses) if space.recommended_uses else ""

        # Privacy categorization
        st = (space.space_type or "").lower()
        title_lower = (space.title or "").lower()
        desc_lower = (space.description or "").lower()
        if st in ("room", "cabin") or "private" in title_lower or "private" in desc_lower:
            privacy_desc = "private enclosed space"
        elif st in ("desk", "hotdesk", "coworking"):
            privacy_desc = "shared workspace"
        elif st in ("meeting_room", "boardroom"):
            privacy_desc = "private meeting space"
        elif st in ("studio", "creative"):
            privacy_desc = "private studio space"
        else:
            privacy_desc = f"{st} space"

        # Acoustic characteristics
        noise = space.ai_noise_level or "standard acoustic environment"

        # Optional review comments
        review_snippets = []
        if hasattr(space, "reviews") and space.reviews:
            for rev in space.reviews[:3]:
                if rev.comment:
                    review_snippets.append(rev.comment[:100])
        reviews_str = "; ".join(review_snippets)

        doc_parts = [
            space.title or "",
            space.description or "",
            f"Space type: {space.space_type or 'workspace'}.",
            f"Capacity: {space.capacity or 1} people.",
            f"Privacy: {privacy_desc}.",
            f"Noise characteristics: {noise}.",
            f"Price: ₹{space.price_per_hour or 0}/hour.",
            f"Amenities: {amenities_str}.",
            f"Location: {space.neighborhood or ''}, {space.city or ''}, {space.address_line1 or ''}.",
            f"Lighting: {space.ai_lighting or 'standard'}.",
            f"Power access: {space.ai_power_access or 'standard outlets'}.",
            f"Recommended uses: {recommended_uses_str}." if recommended_uses_str else "",
            f"Rules: {space.rules}." if space.rules else "",
            f"Reviews: {reviews_str}." if reviews_str else "",
        ]
        return " ".join(filter(None, doc_parts))
