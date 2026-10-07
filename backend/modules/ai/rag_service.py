"""Seven-domain in-process RAG knowledge architecture for SpaceLoop LoopBot.

Authoritative knowledge base covering SpaceLoop's 7 core domains:
1. spaces_search: Physical space discovery & 60-second AI space scan (lighting in lux, ambient noise dB, power plugs, desk ergonomics).
2. booking_reservation: Booking engine, precheck, atomic slot locking, minimum hours, and arrival PIN generation.
3. cancellation_refund: Cancellation policy (SpaceLoop retains ONLY 5% platform fee, 100% rental + ₹100 deposit refunded).
4. checkin_checkout: 50m GPS geofence (Haversine formula), 15-minute temporal window guard, keyless 4-digit PIN & dynamic QR, AccessLog.
5. host_listing: Host onboarding, DISCOM CA utility proofs (MSEDCL, BESCOM, TPDDL, Adani, PSPCL, SHA-256 tokens), and automated UPI VPA penny-drop payouts.
6. pricing_escrow: Micro-escrow formula (Subtotal + 5% platform fee + ₹100 deposit) and immutable double-entry ledger.
7. trust_safety: Section 52 Indian Easements Act 1882 (Leave & License, no tenancy), Objective Trust Score (0-100), and 48-hour photo dispute escrow freezing (status FROZEN).

Relevance cutoff threshold: 0.45.
"""

import logging
import math
import re
from dataclasses import dataclass
from typing import Any

from backend.modules.nlp.parser import QueryParser
from backend.modules.search.vector_engine import VectorEngine

logger = logging.getLogger("spaceloop.ai.rag")

# Strict relevance cutoff mandated by SpaceLoop specification
RAG_RELEVANCE_THRESHOLD = 0.45


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
        # Domain 1: Discovery & 60-Second AI Space Scan Requirements
        RAGDocument(
            id="rag-spaces-search-01",
            domain="spaces_search",
            title="Physical Space Discovery & 60-Second AI Space Scan",
            summary="Explore verified desks, studios, and offices with 60-second AI space scan evaluating lux, dB, power, and ergonomics.",
            content=(
                "SpaceLoop enables peer-to-peer discovery of physical workspaces across Bengaluru, Mumbai, Delhi NCR, "
                "Pune, and Hyderabad. Seekers can search using natural language (English, Hindi, Hinglish, Marathi) "
                "or faceted filters. Filter by hourly budget, capacity (1 to 50+ guests), space types (desk, room, "
                "studio, event space), and verified amenities like gigabit WiFi, AC, soundproofing, and whiteboards. "
                "To prevent deceptive listings, every host space must complete a 60-second AI Space Scan prior to activation: "
                "1. Lighting Quality: Minimum 300 lux target for standard reading/desk work; natural daylight glare detection. "
                "2. Acoustic Environment: Ambient noise measured in decibels (dB)—classified as Quiet (<45 dB), Moderate (45-60 dB), or Active (>60 dB). "
                "3. Power Availability: Verification of accessible AC power plug density and surge protection within 1.5m of workstation. "
                "4. Desk Typology & Ergonomics: Categorization into ergonomic task chair, sit-stand desk, private booth, conference table, or studio setup. "
                "Images must be genuine photos (JPEG/PNG/WebP <= 5MB) verifying room cleanliness."
            ),
            keywords=[
                "find", "search", "desk", "room", "office", "studio", "meeting", "cabin", "space", "bengaluru",
                "mumbai", "delhi", "pune", "hyderabad", "indiranagar", "koramangala", "wifi", "ac", "quiet",
                "soundproof", "space scan", "photo scan", "60-second", "60 seconds", "ai scan", "lighting", "lux",
                "noise", "decibel", "db", "power plug", "ergonomics", "khoj", "dhoondo", "shodha", "sthan", "kamra",
            ],
            suggested_action_types=["search_spaces", "filter_amenities", "start_space_scan"],
        ),

        # Domain 2: Booking Engine & Precheck
        RAGDocument(
            id="rag-booking-reservation-02",
            domain="booking_reservation",
            title="Booking Engine, Precheck & Overlap Prevention",
            summary="Transactional reservation engine with atomic slot locks, minimum hours, and 4-digit arrival PIN generation.",
            content=(
                "Booking requires selecting an active space and valid start/end times meeting the space's minimum "
                "booking hours (typically 1 to 2 hours). Seekers run precheck via POST /api/bookings/precheck to "
                "confirm availability and view an exact cost quote before committing. SpaceLoop strictly enforces "
                "concurrency locks—overlapping reservations for the same space are rejected with 409 Conflict. "
                "Upon host acceptance, a secure 4-digit arrival PIN and dynamic QR token are generated for keyless door access."
            ),
            keywords=[
                "book", "booking", "reserve", "reservation", "precheck", "hours", "slot", "schedule", "pin",
                "arrival pin", "confirm", "overlap", "conflict", "minimum hours", "samay", "karna", "karaychi",
                "arambh", "booking kaise kare", "slot book",
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
                "refundable security deposit back to their account. If a host rejects a reservation, the seeker receives "
                "an unconditional 100% full refund of all charges (rental subtotal + 5% platform fee + ₹100 deposit). "
                "Every disbursement is immutably logged in the double-entry escrow ledger to prevent duplicate settlements or refunds."
            ),
            keywords=[
                "cancel", "cancellation", "refund", "money back", "deposit refund", "reject", "rejection", "policy",
                "5% fee", "platform fee", "radd", "vapasi", "paratam", "paise wapas", "refund kab aayega", "cancel policy",
            ],
            suggested_action_types=["view_cancellation_policy", "my_bookings"],
        ),

        # Domain 4: Check-in, 50m Geofence, Temporal Guard & PIN Access
        RAGDocument(
            id="rag-checkin-checkout-04",
            domain="checkin_checkout",
            title="4-Digit Arrival PIN, 50m GPS Geofence & 15-Minute Temporal Guard",
            summary="Secure physical access with 50m Haversine geofence, 15-min start guard, 4-digit PIN fallback, QR token, and AccessLog.",
            content=(
                "Physical check-in operates on a zero-trust multi-factor architecture: "
                "1. Temporal Guard: Physical check-in is locked until exactly 15 minutes prior to the scheduled booking start time. "
                "2. 50-Meter Geofence: When checking in via GPS, seeker coordinates are validated against space coordinates using "
                "the Haversine great-circle distance formula (d <= 50 meters). "
                "3. Keyless Credentials: Seekers can scan the dynamic encrypted room QR token or enter their unique 4-digit arrival "
                "PIN on physical keypad door locks. "
                "4. Photo Audits: Both parties take inspection photos at check-in and check-out to document cleanliness and condition, "
                "safeguarding the ₹100 deposit. "
                "5. AccessLog: Every attempt is immutably recorded in the AccessLog table with timestamp, coordinates, distance, and validation method."
            ),
            keywords=[
                "checkin", "check-in", "checkout", "check-out", "pin", "arrival pin", "door", "lock", "gps",
                "geofence", "50m", "50 meter", "50 meters", "haversine", "temporal guard", "15 minute", "15 minutes",
                "inspection", "photos", "access", "entry", "qr", "qr code", "accesslog", "pravesh", "chabi", "darwaza", "tala",
            ],
            suggested_action_types=["checkin_guide", "view_pin"],
        ),

        # Domain 5: Host Onboarding, DISCOM CA Utility Proofs & Payout Settlement
        RAGDocument(
            id="rag-host-listing-05",
            domain="host_listing",
            title="Host Space Listing, DISCOM CA Utility Proofs & UPI Payouts",
            summary="List space, verify via DISCOM electricity bills (MSEDCL, BESCOM, TPDDL, Adani, PSPCL) with SHA-256 tokens, receive UPI payouts.",
            content=(
                "Property owners, businesses, and creators can monetize idle physical capacity on SpaceLoop: "
                "1. Listing Creation: Hosts upload space photos (up to 5MB, JPEG/PNG/WebP with magic byte verification), set hourly rates, and list amenities. "
                "2. DISCOM CA Utility Proofs: To eliminate phantom listings, hosts verify property possession using electricity Consumer Account (CA) "
                "numbers from Indian DISCOMs (MSEDCL Maharashtra, BESCOM Bengaluru, TPDDL/BSES Delhi NCR, Adani Electricity Mumbai, PSPCL Punjab). "
                "SpaceLoop generates an immutable SHA-256 hash of the utility statement. "
                "3. Zero Listing Fee: Zero host subscription or listing fees. Hosts receive 100% of the rental subtotal. "
                "4. Payout Settlement: Automatically scheduled post-checkout and disbursed directly to host's UPI VPA verified through ₹1 penny-drop."
            ),
            keywords=[
                "host", "listing", "list space", "become host", "monetize", "earn", "payout", "upi", "vpa", "penny drop",
                "photos", "kyc", "property", "discom", "ca number", "consumer account", "electricity bill", "utility",
                "msedcl", "bescom", "tpddl", "adani", "pspcl", "sha-256", "mej", "kamra", "nondani", "soochi", "host kaise bane",
            ],
            suggested_action_types=["create_listing", "host_dashboard", "verify_vpa"],
        ),

        # Domain 6: Micro-Escrow Pricing & Double-Entry Ledger
        RAGDocument(
            id="rag-pricing-escrow-06",
            domain="pricing_escrow",
            title="Micro-Escrow Economics, 5% Platform Fee & Double-Entry Ledger",
            summary="Deterministic formula: Subtotal (rate × hours) + 5% platform fee + ₹100 refundable escrow deposit.",
            content=(
                "SpaceLoop operates an immutable double-entry micro-escrow ledger. "
                "Pricing formula: "
                "Space Subtotal = price_hourly × duration_hours. "
                "Platform Fee = round(Space Subtotal × 0.05, 2) (5% service fee). "
                "Refundable Escrow Deposit = ₹100.00. "
                "Total Paid = Space Subtotal + Platform Fee + ₹100.00. "
                "Funds are securely held in escrow during the booking. Upon normal checkout: the host receives 100% of the subtotal, "
                "SpaceLoop retains the 5% platform fee, and the ₹100 deposit is promptly returned to the seeker. "
                "Every financial transaction is recorded with double-entry debit/credit ledger records."
            ),
            keywords=[
                "price", "pricing", "cost", "fee", "platform fee", "5%", "5 percent", "escrow", "deposit", "100", "₹100",
                "subtotal", "total", "ledger", "double-entry", "upi", "vpa", "shulk", "bhade", "kiraya", "kiti paise", "kitna kharcha", "hisab",
            ],
            suggested_action_types=["view_pricing_breakdown", "verify_vpa"],
        ),

        # Domain 7: Section 52 Easements, Objective Trust & Dispute Freezing
        RAGDocument(
            id="rag-trust-safety-07",
            domain="trust_safety",
            title="Section 52 Easements Act, Objective Trust Score & Dispute Freezes",
            summary="Section 52 Leave & License (no tenancy rights), Objective Trust Score (0-100), and 48-hour photo dispute escrow freezes.",
            content=(
                "Platform safety, legal integrity, and dispute management: "
                "1. Section 52 Indian Easements Act 1882: All SpaceLoop reservations are legally structured as revocable Leave and License agreements. "
                "A license grants a personal right to occupy the space for the agreed hours; it does NOT create any tenancy, leasehold estate, or "
                "exclusive proprietary rights in the property. "
                "2. Objective Trust Score: Holistic score (0-100) based on verified bookings, user reviews, DISCOM CA verification, and zero dispute infractions. "
                "3. 48-Hour Dispute Window: If physical access is denied or property is misrepresented/damaged, parties can file a dispute within 48 hours. "
                "Filing immediately updates escrow status to FROZEN in the double-entry ledger, preventing disbursement until platform administrators adjudicate comparative check-in vs check-out inspection photos."
            ),
            keywords=[
                "trust", "safety", "trust score", "objective trust", "score", "kyc", "verification", "dispute",
                "freeze", "frozen", "48 hour", "48 hours", "48h", "section 52", "easements act", "easement", "leave and license",
                "tenancy", "lease", "eviction", "revocable", "suraksha", "vishwas", "takrar", "vivad", "surakshit",
            ],
            suggested_action_types=["view_trust_guidelines", "file_dispute", "view_legal_terms"],
        ),
    ]

    # Domain aliases mapping both legacy names and detailed names
    DOMAIN_ALIASES = {
        "spaces_search": "spaces_search",
        "photo_scan": "spaces_search",
        "booking_reservation": "booking_reservation",
        "cancellation_refund": "cancellation_refund",
        "checkin_checkout": "checkin_checkout",
        "geofence_access": "checkin_checkout",
        "host_listing": "host_listing",
        "utility_proofs": "host_listing",
        "host_payouts": "host_listing",
        "pricing_escrow": "pricing_escrow",
        "micro_escrow": "pricing_escrow",
        "trust_safety": "trust_safety",
        "section_52_easements": "trust_safety",
        "dispute_resolution": "trust_safety",
    }

    @classmethod
    def all_domains(cls) -> list[str]:
        """Return list of all supported canonical RAG knowledge domains."""
        return [
            "booking_reservation",
            "cancellation_refund",
            "checkin_checkout",
            "host_listing",
            "pricing_escrow",
            "spaces_search",
            "trust_safety",
        ]

    @classmethod
    def resolve_domain(cls, domain: str | None) -> str | None:
        """Resolve domain or alias to canonical domain string."""
        if not domain:
            return None
        norm = domain.lower().strip()
        return cls.DOMAIN_ALIASES.get(norm, norm)

    @classmethod
    def search_knowledge(
        cls,
        query: str,
        domain: str | None = None,
        top_k: int = 3,
        language: str = "en",
        threshold: float = RAG_RELEVANCE_THRESHOLD,
    ) -> list[dict[str, Any]]:
        """Retrieve top-k knowledge documents matching query with relevance >= threshold."""
        if not query or not query.strip():
            return [cls._doc_to_dict(doc, 1.0) for doc in cls.KNOWLEDGE_BASE[:top_k]]

        normalized = QueryParser.normalize_text(query).lower()
        tokens = set(re.findall(r"\w+", normalized))
        query_vector = VectorEngine.get_deterministic_embedding(normalized)

        target_domain = cls.resolve_domain(domain)
        scored_docs: list[tuple[float, RAGDocument]] = []

        for doc in cls.KNOWLEDGE_BASE:
            score = 0.0

            # 1. Exact canonical domain match
            if target_domain and doc.domain == target_domain:
                score += 3.0

            # 2. Keyword exact overlap
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

        # Sort descending by composite score
        scored_docs.sort(key=lambda item: item[0], reverse=True)

        results = []
        for score, doc in scored_docs[:top_k]:
            if score >= threshold:
                results.append(cls._doc_to_dict(doc, score))

        return results

    @classmethod
    def get_domain_summary(cls, domain: str) -> str:
        """Fetch summary knowledge text for a specific domain."""
        canonical = cls.resolve_domain(domain)
        for doc in cls.KNOWLEDGE_BASE:
            if doc.domain == canonical:
                return doc.content
        return "SpaceLoop is India's peer-to-peer physical workspace marketplace with micro-escrow protection."

    @classmethod
    def build_llm_context(cls, docs: list[dict[str, Any]]) -> str:
        """Format retrieved knowledge articles into a concise LLM context block."""
        if not docs:
            return "No specific SpaceLoop reference documents retrieved."

        lines = ["Authoritative SpaceLoop Reference Specifications:"]
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
