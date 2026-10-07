"""Seven-domain in-process RAG knowledge architecture for SpaceLoop LoopBot.

Provides grounded, deterministic knowledge retrieval across core marketplace domains:
1. spaces_search: Discovery, search, location filters, amenities, and vibe.
2. booking_reservation: Booking pipeline, precheck, concurrency control, and arrival PIN.
3. cancellation_refund: Cancellation policy (5% fee retained, 100% rental + deposit refunded), host rejection.
4. checkin_checkout: 4-digit arrival PIN, 50m GPS geofence, and inspection photo verification.
5. host_listing: Space creation, photo uploads, KYC verification, and host payouts.
6. pricing_escrow: Micro-escrow formula (Subtotal + 5% fee + ₹100 deposit) and double-entry ledger.
7. trust_safety: Objective Trust Score (0-100), KYC tiers, dispute freezing, and platform safety.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from backend.modules.nlp.parser import QueryParser
from backend.modules.search.vector_engine import VectorEngine

logger = logging.getLogger("spaceloop.ai.rag")


@dataclass
class RAGDocument:
    """Document unit within the in-process RAG knowledge base."""
    id: str
    domain: str
    title: str
    content: str
    summary: str
    keywords: list[str]
    suggested_action_types: list[str]


class RAGService:
    """In-process retrieval-augmented generation engine for LoopBot."""

    KNOWLEDGE_BASE: list[RAGDocument] = [
        # Domain 1: Discovery & Spaces Search
        RAGDocument(
            id="rag-spaces-search-01",
            domain="spaces_search",
            title="Physical Space Discovery & Multi-Modal Search",
            summary="Explore desks, private offices, meeting rooms, and studios across Indian metro tech hubs.",
            content=(
                "SpaceLoop enables peer-to-peer discovery of physical spaces across Bengaluru, Mumbai, Delhi NCR, "
                "Pune, and Hyderabad. Seekers can search using natural language (English, Hindi, Hinglish, Marathi) "
                "or faceted filters. Filter by hourly budget, capacity (1 to 50+ guests), space types (desk, room, "
                "studio, event space), and verified amenities like gigabit WiFi, AC, soundproofing, and whiteboards. "
                "Hard geographic boundaries match listings within 2km to 25km haversine distance."
            ),
            keywords=[
                "find", "search", "desk", "room", "office", "studio", "meeting", "cabin", "space", "bengaluru",
                "mumbai", "delhi", "pune", "hyderabad", "indiranagar", "koramangala", "wifi", "ac", "quiet",
                "soundproof", "khoj", "dhoondo", "shodha", "sthan", "kamra", "kholi", "mej", "chahiye", "pahije",
            ],
            suggested_action_types=["search_spaces", "filter_amenities"],
        ),

        # Domain 2: Booking Engine & Precheck
        RAGDocument(
            id="rag-booking-reservation-02",
            domain="booking_reservation",
            title="Booking Engine, Precheck & Overlap Prevention",
            summary="Transactional reservation engine with atomic slot locks and 4-digit arrival PIN generation.",
            content=(
                "Booking requires selecting an active space and valid start/end times meeting the space's minimum "
                "booking hours (typically 1 to 2 hours). Seekers run precheck via POST /api/bookings/precheck to "
                "confirm availability and view an exact cost quote before committing. SpaceLoop strictly enforces "
                "concurrency locks—overlapping reservations for the same space are rejected with 409 Conflict. "
                "Upon host acceptance, a secure 4-digit arrival PIN is generated for keyless door access."
            ),
            keywords=[
                "book", "booking", "reserve", "reservation", "precheck", "hours", "slot", "schedule", "pin",
                "arrival pin", "confirm", "overlap", "conflict", "samay", "karna", "karaychi", "arambh", "booking kaise kare",
            ],
            suggested_action_types=["open_precheck", "my_bookings"],
        ),

        # Domain 3: Cancellation & Refund Policy
        RAGDocument(
            id="rag-cancellation-refund-03",
            domain="cancellation_refund",
            title="Cancellation Rules & Deterministic Escrow Refunds",
            summary="Clear cancellation formula: 5% platform fee retained, 100% rental + ₹100 deposit refunded.",
            content=(
                "Under the SpaceLoop specification, when a seeker cancels a booking: SpaceLoop retains ONLY the "
                "5% platform fee. The seeker receives 100% of the space rental subtotal plus 100% of the ₹100 "
                "refundable security deposit back. If a host rejects a reservation, the seeker receives a full 100% "
                "refund of all charges (rental subtotal + 5% platform fee + ₹100 deposit). Every disbursement is "
                "immutably logged in the double-entry escrow ledger to prevent duplicate settlements or refunds."
            ),
            keywords=[
                "cancel", "cancellation", "refund", "money back", "deposit refund", "reject", "rejection", "policy",
                "radd", "vapasi", "paratam", "paise wapas", "refund kab aayega", "cancel policy", "fee refund",
            ],
            suggested_action_types=["view_cancellation_policy", "my_bookings"],
        ),

        # Domain 4: Check-in, Check-out & PIN Access
        RAGDocument(
            id="rag-checkin-checkout-04",
            domain="checkin_checkout",
            title="4-Digit Arrival PIN, GPS Geofencing & Photo Inspection",
            summary="Secure physical access with arrival PINs, 50m GPS verification, and check-in/out photo audits.",
            content=(
                "Physical check-in is safeguarded by three layers: 1) The seeker enters their unique 4-digit arrival "
                "PIN to access the space. 2) The mobile client validates that the user is physically within the "
                "50-meter GPS geofence of the space coordinates. 3) Both parties take inspection photos at check-in "
                "and check-out to record property cleanliness and amenity conditions, safeguarding the ₹100 deposit. "
                "Session states transition: not_started -> checked_in -> checked_out."
            ),
            keywords=[
                "checkin", "check-in", "checkout", "check-out", "pin", "arrival pin", "door", "lock", "gps",
                "geofence", "inspection", "photos", "access", "entry", "pravesh", "chabi", "darwaza", "tala",
            ],
            suggested_action_types=["checkin_guide", "view_pin"],
        ),

        # Domain 5: Host Onboarding & Listing Management
        RAGDocument(
            id="rag-host-listing-05",
            domain="host_listing",
            title="Host Space Listing, Photos & Payout Settlement",
            summary="List unused physical square footage, set hourly pricing, complete KYC, and receive UPI payouts.",
            content=(
                "Property owners, businesses, and creators can monetize idle physical capacity on SpaceLoop. Hosts "
                "upload space photos (up to 5MB, JPEG/PNG/WebP with magic byte integrity verification), define hourly "
                "rates, minimum hours, and list amenities. New hosts undergo KYC identity verification. Payouts are "
                "automatically scheduled after seeker checkout and disbursed directly to the host's UPI VPA through "
                "our payment adapter, with zero host subscription fees."
            ),
            keywords=[
                "host", "listing", "list space", "become host", "monetize", "earn", "payout", "upi", "photos",
                "kyc", "property", "mej", "kamra", "nondani", "soochi", "host kaise bane", "paise kamaye",
            ],
            suggested_action_types=["create_listing", "host_dashboard"],
        ),

        # Domain 6: Micro-Escrow Pricing & Ledger Architecture
        RAGDocument(
            id="rag-pricing-escrow-06",
            domain="pricing_escrow",
            title="Micro-Escrow Economics, 5% Platform Fee & UPI Ledger",
            summary="Deterministic formula: Subtotal (rate × hours) + 5% platform fee + ₹100 refundable escrow.",
            content=(
                "SpaceLoop operates an immutable double-entry micro-escrow ledger. Pricing formula: "
                "Space Subtotal = price_hourly × duration_hours. Platform Fee = round(Space Subtotal × 0.05, 2). "
                "Refundable Escrow Deposit = ₹100.00. Total Paid = Space Subtotal + Platform Fee + ₹100. "
                "Funds are securely held in escrow. Upon normal checkout: the host receives the subtotal, SpaceLoop "
                "retains the 5% platform fee, and the ₹100 deposit is returned to the seeker. Real or mock UPI "
                "adapters validate VPAs and perform ₹1.00 penny-drop account verification before disbursement."
            ),
            keywords=[
                "price", "pricing", "cost", "fee", "platform fee", "5%", "escrow", "deposit", "100", "subtotal",
                "ledger", "upi", "vpa", "penny drop", "shulk", "bhade", "kiti paise", "kitna kharcha", "hisab",
            ],
            suggested_action_types=["view_pricing_breakdown", "verify_vpa"],
        ),

        # Domain 7: Trust, Safety, Verification & Disputes
        RAGDocument(
            id="rag-trust-safety-07",
            domain="trust_safety",
            title="Objective Trust Score, Safety Guardrails & Dispute Freezes",
            summary="Holistic trust scoring (0-100), KYC identity verification, and dispute escrow freezing.",
            content=(
                "Platform safety is grounded in an Objective Trust Score (0-100) based on verified bookings, user "
                "ratings, completed KYC, and zero dispute infractions. If an amenity is misrepresented or access is "
                "denied, seekers can file a dispute via POST /api/booking/<id>/dispute, which immediately freezes "
                "escrow funds (status FROZEN) and alerts admin adjudicators. LoopBot is an advisory assistant and "
                "cannot directly mutate financial, booking, or security states—every action requires backend validation."
            ),
            keywords=[
                "trust", "safety", "trust score", "objective trust", "score", "kyc", "verification", "dispute",
                "freeze", "fraud", "scam", "suraksha", "vishwas", "takrar", "vivad", "surakshit", "safety rules",
            ],
            suggested_action_types=["view_trust_guidelines", "file_dispute"],
        ),
    ]

    @classmethod
    def all_domains(cls) -> list[str]:
        """Return list of all supported RAG knowledge domains."""
        return [
            "spaces_search",
            "booking_reservation",
            "cancellation_refund",
            "checkin_checkout",
            "host_listing",
            "pricing_escrow",
            "trust_safety",
        ]

    @classmethod
    def search_knowledge(
        cls,
        query: str,
        domain: str | None = None,
        top_k: int = 3,
        language: str = "en",
    ) -> list[dict[str, Any]]:
        """Retrieve the top-k most relevant knowledge articles for a user message."""
        if not query or not query.strip():
            return [cls._doc_to_dict(doc, 1.0) for doc in cls.KNOWLEDGE_BASE[:top_k]]

        normalized = QueryParser.normalize_text(query).lower()
        tokens = set(re.findall(r"\w+", normalized))

        # Concept vector for query
        query_vector = VectorEngine.get_deterministic_embedding(normalized)

        scored_docs: list[tuple[float, RAGDocument]] = []

        for doc in cls.KNOWLEDGE_BASE:
            score = 0.0

            # 1. Exact domain match bonus
            if domain and doc.domain == domain:
                score += 3.0

            # 2. Keyword & tag overlap
            doc_keywords = set(doc.keywords)
            overlap = tokens.intersection(doc_keywords)
            score += len(overlap) * 1.5

            # 3. Title token overlap
            title_tokens = set(re.findall(r"\w+", doc.title.lower()))
            score += len(tokens.intersection(title_tokens)) * 2.0

            # 4. Content token frequency
            content_tokens = set(re.findall(r"\w+", doc.content.lower()))
            score += len(tokens.intersection(content_tokens)) * 0.5

            # 5. Semantic vector similarity
            doc_vector = VectorEngine.get_deterministic_embedding(doc.content)
            vec_sim = VectorEngine.cosine_similarity(query_vector, doc_vector)
            score += vec_sim * 2.5

            scored_docs.append((score, doc))

        # Sort descending by composite relevance score
        scored_docs.sort(key=lambda item: item[0], reverse=True)

        results = []
        for score, doc in scored_docs[:top_k]:
            results.append(cls._doc_to_dict(doc, score))

        return results

    @classmethod
    def get_domain_summary(cls, domain: str) -> str:
        """Fetch summary knowledge text for a specific domain."""
        for doc in cls.KNOWLEDGE_BASE:
            if doc.domain == domain:
                return doc.content
        return "SpaceLoop is a peer-to-peer physical space discovery and booking platform."

    @classmethod
    def build_llm_context(cls, docs: list[dict[str, Any]]) -> str:
        """Format retrieved knowledge articles into a concise LLM context block."""
        if not docs:
            return "No specific SpaceLoop reference documents retrieved."

        lines = ["Relevant SpaceLoop Knowledge & Specifications:"]
        for idx, doc in enumerate(docs, 1):
            lines.append(f"[{idx}] Domain: {doc.get('domain')} | Title: {doc.get('title')}")
            lines.append(f"Summary: {doc.get('summary', '')}")
            lines.append(f"Content: {doc.get('snippet', '')}\n")

        return "\n".join(lines)

    @staticmethod
    def _doc_to_dict(doc: RAGDocument, score: float) -> dict[str, Any]:
        return {
            "id": doc.id,
            "domain": doc.domain,
            "title": doc.title,
            "summary": doc.summary,
            "snippet": doc.content,
            "score": round(score, 3),
            "suggested_action_types": doc.suggested_action_types,
        }
