"""Intent classification, multilingual language detection, and entity extraction for SpaceLoop LoopBot.

Covers the 18 distinct marketplace intent categories:
1. GENERAL: Greetings, what is SpaceLoop, high-level overview.
2. SPACE_SEARCH: Discovery, search query, location/budget/amenity matching.
3. SPACE_DETAILS: Specific details about an identified space.
4. SPACE_AVAILABILITY: Slot checks, prechecks, minimum hours questions.
5. BOOKING_STATUS: Status of existing reservation.
6. BOOKING_CREATE: Intent to book/reserve a space.
7. BOOKING_CANCEL: Intent to cancel a booking.
8. ACCESS_STATUS: PIN, QR, door lock status for a booking.
9. ACCESS_HELP: Access troubleshooting, 50m geofence, 15m temporal guard.
10. ESCROW_STATUS: Deposit status, escrow hold, ledger balance.
11. REFUND_HELP: Refund calculation, 5% fee explanation, return timeline.
12. HOST_HELP: Host onboarding, listing creation, payouts.
13. SEEKER_HELP: Seeker guidebook, verification, student discount.
14. LEGAL_INFORMATION: Section 52 Indian Easements Act 1882, leave & license.
15. DISPUTE_HELP: Filing disputes, 48h photo inspection comparison, escrow freezing.
16. TRUST_SAFETY: Objective Trust Score (0-100), KYC, safety guarantees.
17. ACCOUNT_HELP: Account, profile, MFA, password reset.
18. SUPPORT: Human support escalation, customer assistance.
"""

import logging
import re
import unicodedata
from typing import Any

from backend.modules.i18n.constants import (
    LANG_EN,
    LANG_GSW,
    LANG_HI,
    LANG_HINGLISH,
    LANG_JNS,
    LANG_KFY,
    LANG_MR,
)
from backend.modules.i18n.detector import LanguageDetector
from backend.modules.nlp.parser import QueryParser

logger = logging.getLogger("spaceloop.ai.intent")


class IntentParser:
    """Enterprise intent classifier and structured entity extractor for SpaceLoop."""

    # 18 Standard SpaceLoop Intent Constants
    INTENT_GENERAL = "GENERAL"
    INTENT_SPACE_SEARCH = "SPACE_SEARCH"
    INTENT_SPACE_DETAILS = "SPACE_DETAILS"
    INTENT_SPACE_AVAILABILITY = "SPACE_AVAILABILITY"
    INTENT_BOOKING_STATUS = "BOOKING_STATUS"
    INTENT_BOOKING_CREATE = "BOOKING_CREATE"
    INTENT_BOOKING_CANCEL = "BOOKING_CANCEL"
    INTENT_ACCESS_STATUS = "ACCESS_STATUS"
    INTENT_ACCESS_HELP = "ACCESS_HELP"
    INTENT_ESCROW_STATUS = "ESCROW_STATUS"
    INTENT_REFUND_HELP = "REFUND_HELP"
    INTENT_HOST_HELP = "HOST_HELP"
    INTENT_SEEKER_HELP = "SEEKER_HELP"
    INTENT_LEGAL_INFORMATION = "LEGAL_INFORMATION"
    INTENT_DISPUTE_HELP = "DISPUTE_HELP"
    INTENT_TRUST_SAFETY = "TRUST_SAFETY"
    INTENT_ACCOUNT_HELP = "ACCOUNT_HELP"
    INTENT_SUPPORT = "SUPPORT"

    # Legacy mapping for backwards-compatibility with test suites
    LEGACY_INTENT_MAP = {
        INTENT_GENERAL: "platform_help",
        INTENT_SPACE_SEARCH: "find_spaces",
        INTENT_SPACE_DETAILS: "find_spaces",
        INTENT_SPACE_AVAILABILITY: "booking_reservation",
        INTENT_BOOKING_STATUS: "booking_reservation",
        INTENT_BOOKING_CREATE: "booking_reservation",
        INTENT_BOOKING_CANCEL: "cancellation_refund",
        INTENT_ACCESS_STATUS: "checkin_checkout",
        INTENT_ACCESS_HELP: "checkin_checkout",
        INTENT_ESCROW_STATUS: "pricing_escrow",
        INTENT_REFUND_HELP: "cancellation_refund",
        INTENT_HOST_HELP: "host_listing",
        INTENT_SEEKER_HELP: "platform_help",
        INTENT_LEGAL_INFORMATION: "trust_safety",
        INTENT_DISPUTE_HELP: "trust_safety",
        INTENT_TRUST_SAFETY: "trust_safety",
        INTENT_ACCOUNT_HELP: "platform_help",
        INTENT_SUPPORT: "platform_help",
    }

    # Supported 6 canonical language identifiers
    LANG_EN = LANG_EN
    LANG_HI = LANG_HI
    LANG_MR = LANG_MR
    LANG_GSW = LANG_GSW
    LANG_KFY = LANG_KFY
    LANG_JNS = LANG_JNS
    LANG_HINGLISH = LANG_HINGLISH

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect language across all 6 languages (en, hi, mr, gsw, kfy, jns) and Hinglish."""
        return LanguageDetector.detect(text, allow_hinglish=True)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Unicode and clean whitespace."""
        nfkd = unicodedata.normalize("NFKD", text)
        cleaned = re.sub(r"[\s\t\r\n]+", " ", nfkd)
        return cleaned.strip()

    @classmethod
    def detect_confirmation(cls, text: str) -> tuple[bool, str | None]:
        """Detect whether a message represents an affirmative or negative confirmation.
        
        Returns (is_confirmation_attempt, decision: 'yes' | 'no' | None).
        """
        cleaned = re.sub(r"[^\w\s]", " ", text.lower()).strip()
        words = cleaned.split()
        if not words:
            return False, None

        first_word = words[0]

        # Negative checks take precedence (e.g. "no, don't confirm", "no, cancel request")
        negative_starters = {"no", "nope", "nah", "dont", "abort", "nevermind", "nahi", "nakko", "stop"}
        negative_phrases = ["cancel request", "do not", "keep it", "never mind", "dont cancel", "rahne do", "abort"]
        if first_word in negative_starters or any(p in cleaned for p in negative_phrases):
            return True, "no"

        # Affirmative checks
        affirmative_starters = {"yes", "yep", "yeah", "yup", "sure", "ok", "okay", "confirm", "proceed", "ha", "haan", "ho"}
        affirmative_phrases = ["please confirm", "go ahead", "confirm and proceed", "i confirm", "book it", "do it", "yes please"]
        if first_word in affirmative_starters or any(p in cleaned for p in affirmative_phrases):
            return True, "yes"

        return False, None

    @classmethod
    def classify_intent(cls, text: str, session_context: dict[str, Any] | None = None) -> tuple[str, str]:
        """Classify message into standard 18-intent enum and return (standard_intent, legacy_intent)."""
        lower = text.lower()

        # 1. Legal / Section 52 Easements Act
        if any(re.search(pat, lower) for pat in [
            r"section 52", r"easement", r"easements act", r"leave and license",
            r"tenancy", r"tenant rights", r"eviction", r"lease agreement", r"legal status",
        ]):
            return cls.INTENT_LEGAL_INFORMATION, cls.LEGACY_INTENT_MAP[cls.INTENT_LEGAL_INFORMATION]

        # 2. Dispute & Evidence
        if any(re.search(pat, lower) for pat in [
            r"dispute", r"file dispute", r"freeze escrow", r"damage", r"takrar",
            r"vivad", r"complaint", r"48 hour", r"48h", r"inspection dispute",
        ]):
            return cls.INTENT_DISPUTE_HELP, cls.LEGACY_INTENT_MAP[cls.INTENT_DISPUTE_HELP]

        # 3. Access Help & Geofence
        if any(re.search(pat, lower) for pat in [
            r"geofence", r"50m", r"50 meter", r"temporal guard", r"15 minute",
            r"cant check in", r"can't check in", r"gps error", r"distance too far",
            r"door locked", r"how to enter", r"how to check in",
        ]):
            return cls.INTENT_ACCESS_HELP, cls.LEGACY_INTENT_MAP[cls.INTENT_ACCESS_HELP]

        # 4. Access Status / PIN / QR
        if any(re.search(pat, lower) for pat in [
            r"arrival pin", r"\bpin\b", r"qr code", r"qr token", r"door code",
            r"access code", r"my pin", r"where is my pin", r"show pin",
            r"पिन", r"चाबी", r"darwaza",
        ]):
            return cls.INTENT_ACCESS_STATUS, cls.LEGACY_INTENT_MAP[cls.INTENT_ACCESS_STATUS]

        # 5. Booking Cancel & Refund
        if any(re.search(pat, lower) for pat in [
            r"cancel my booking", r"cancel booking", r"i want to cancel", r"cancel reservation",
            r"radd karna", r"booking cancel", r"slot cancel", r"रद्द", r"रद्द करण्याचे", r"cancel",
            r"कैंसिल", r"radd",
        ]):
            return cls.INTENT_BOOKING_CANCEL, cls.LEGACY_INTENT_MAP[cls.INTENT_BOOKING_CANCEL]

        if any(re.search(pat, lower) for pat in [
            r"refund", r"money back", r"cancellation policy", r"fee refund",
            r"deposit refund", r"paise wapas", r"paratam", r"रिफंड", r"परत", r"पैसे परत",
        ]):
            return cls.INTENT_REFUND_HELP, cls.LEGACY_INTENT_MAP[cls.INTENT_REFUND_HELP]

        # 6. Booking Create (requesting to book)
        if any(re.search(pat, lower) for pat in [
            r"book\s+(?:it|this|that|space|desk|room|studio|now|one|the\s+\w+)",
            r"reserve\s+(?:it|this|that|space|now|one|the\s+\w+)",
            r"book\s+for\s+\d+", r"i\s+want\s+to\s+book", r"book\s+kar\s*(?:do|de|lo)",
            r"booking\s+kar\s*(?:do|de|lo|na)", r"booking\s+karo", r"reserve\s+kar\s*(?:do|de)",
            r"confirm\s+booking", r"let's\s+book", r"lets\s+book",
        ]):
            return cls.INTENT_BOOKING_CREATE, cls.LEGACY_INTENT_MAP[cls.INTENT_BOOKING_CREATE]

        # 7. Space Availability & Precheck / Pricing Quote for duration
        if any(re.search(pat, lower) for pat in [
            r"how\s+much\s+(?:for|for\s+the)\s+\d+",
            r"(?:pricing|price|cost|quote)\s+for\s+\d+",
            r"how\s+much\s+(?:will|does)\s+it\s+cost",
            r"kitna\s+(?:paisa|kharcha|lagega)\s+(?:hoga\s+)?(?:\d+\s+ghante)?",
            r"kiti\s+(?:paise|kharch)\s+hotil",
            r"is it available", r"check availability", r"availability", r"available slots",
            r"free slot", r"minimum hours", r"can i book for", r"precheck",
        ]):
            return cls.INTENT_SPACE_AVAILABILITY, cls.LEGACY_INTENT_MAP[cls.INTENT_SPACE_AVAILABILITY]

        # 8. Questions about current listings or specific listing attributes (e.g. parking, wifi)
        if any(re.search(pat, lower) for pat in [
            r"which\s+(?:one|space|desk)\s+(?:has|have|offers)\b",
            r"does\s+(?:that\s+one|the\s+second|the\s+first|it)\s+have\b",
            r"(?:parking|wifi|ac|coffee|valet)\s+(?:hai\s+kya|ahe\s+ka)",
            r"kisme\s+(?:parking|wifi|ac)\s+hai",
            r"compare\s+(?:them|spaces|listings)",
        ]):
            return cls.INTENT_SPACE_DETAILS, cls.LEGACY_INTENT_MAP[cls.INTENT_SPACE_DETAILS]

        # 9. Ordinal reference or specific listing selection ("the second one", "first one", "space 2")
        if any(re.search(pat, lower) for pat in [
            r"^(?:the\s+)?(?:first|1st|second|2nd|third|3rd|fourth|4th|last)\s+(?:one|space|desk|room)?$",
            r"^(?:pehla|pahila|dusra|doosra|teesra|tisra|aakhri)\s*(?:wala|waala)?$",
            r"tell me about space", r"space #\d+", r"space details", r"details of space",
            r"show space", r"amenities of space",
        ]):
            return cls.INTENT_SPACE_DETAILS, cls.LEGACY_INTENT_MAP[cls.INTENT_SPACE_DETAILS]

        # 10. Escrow Status & Pricing Formula & Fees (general policy questions)
        if any(re.search(pat, lower) for pat in [
            r"escrow", r"₹100 deposit", r"100 deposit", r"security deposit",
            r"platform fee", r"5% fee", r"5 percent", r"ledger balance", r"deposit status",
            r"fee structure", r"fee breakdown", r"what is escrow",
            r"शुल्क", r"किराया", r"भाडे",
        ]):
            return cls.INTENT_ESCROW_STATUS, cls.LEGACY_INTENT_MAP[cls.INTENT_ESCROW_STATUS]

        # 11. Host Help & Listing Management (Checked before space details & search)
        if any(re.search(pat, lower) for pat in [
            r"list my space", r"list a space", r"host on spaceloop", r"become a host",
            r"host payout", r"payout setup", r"upi vpa", r"penny drop", r"discom",
            r"utility proof", r"space scan", r"host earnings", r"earn as host",
            r"earn money as host", r"as host", r"list.*office", r"list.*room",
            r"list.*desk", r"list.*studio", r"list my", r"monetize", r"list space",
            r"होस्ट", r"लिस्टिंग", r"जागा जोडा", r"कमाई", r"पैसे कमवा", r"host kaise bane",
        ]):
            return cls.INTENT_HOST_HELP, cls.LEGACY_INTENT_MAP[cls.INTENT_HOST_HELP]

        # 12. Booking Status (specific booking inquiries)
        if any(re.search(pat, lower) for pat in [
            r"my booking", r"booking status", r"booking #\d+", r"view booking",
            r"is my booking confirmed", r"active booking",
        ]):
            return cls.INTENT_BOOKING_STATUS, cls.LEGACY_INTENT_MAP[cls.INTENT_BOOKING_STATUS]

        # 13. Trust, Safety & KYC
        if any(re.search(pat, lower) for pat in [
            r"trust score", r"objective trust", r"is host verified", r"safety",
            r"safe to use", r"kyc", r"identity verification", r"सुरक्षा", r"vishwas",
        ]):
            return cls.INTENT_TRUST_SAFETY, cls.LEGACY_INTENT_MAP[cls.INTENT_TRUST_SAFETY]

        # 13. Account Help
        if any(re.search(pat, lower) for pat in [
            r"my account", r"mfa", r"2fa", r"reset password", r"change profile",
            r"verification status", r"login problem",
        ]):
            return cls.INTENT_ACCOUNT_HELP, cls.LEGACY_INTENT_MAP[cls.INTENT_ACCOUNT_HELP]

        # 14. Support Escalation
        if any(re.search(pat, lower) for pat in [
            r"contact support", r"human agent", r"talk to support", r"admin help",
            r"raise ticket", r"support team",
        ]):
            return cls.INTENT_SUPPORT, cls.LEGACY_INTENT_MAP[cls.INTENT_SUPPORT]

        # 15. General Greetings / Platform Overview
        if any(re.search(pat, lower) for pat in [
            r"^(hi|hello|hey|namaste|namaskar|good morning|good evening)$",
            r"what is spaceloop", r"how does spaceloop work", r"kya hai",
        ]):
            return cls.INTENT_GENERAL, cls.LEGACY_INTENT_MAP[cls.INTENT_GENERAL]

        # 16. Search Spaces / Discovery (Keywords or general space criteria)
        if any(re.search(pat, lower) for pat in [
            r"find", r"search", r"desk", r"studio", r"office", r"cabin", r"room",
            r"meeting", r"coworking", r"space", r"indiranagar", r"koramangala",
            r"bengaluru", r"bangalore", r"mumbai", r"delhi", r"pune", r"hyderabad",
            r"wifi", r"quiet", r"soundproof", r"ac", r"dhoondo", r"chahiye", r"pahije",
        ]):
            return cls.INTENT_SPACE_SEARCH, cls.LEGACY_INTENT_MAP[cls.INTENT_SPACE_SEARCH]

        # Fallback to session's previous intent or general search
        if session_context and session_context.get("last_intent"):
            last = session_context["last_intent"]
            # Map if last is legacy
            for std, leg in cls.LEGACY_INTENT_MAP.items():
                if last in (std, leg):
                    return std, leg
        return cls.INTENT_SPACE_SEARCH, cls.LEGACY_INTENT_MAP[cls.INTENT_SPACE_SEARCH]

    @classmethod
    def extract_entities(cls, text: str, context_entities: dict[str, Any] | None = None) -> dict[str, Any]:
        """Extract structured marketplace entities from text and merge with conversation context."""
        context = dict(context_entities or {})
        parsed = QueryParser.parse_query(text)

        merged = dict(context)

        # Merge standard geographic & dimensional constraints
        for key in [
            "city", "neighborhood", "latitude", "longitude", "date", "time",
            "duration_hours", "budget", "capacity", "space_type", "use_case",
        ]:
            val = parsed.get(key)
            if val is not None and val != "":
                merged[key] = val

        # Explicit regex extraction for IDs
        # Space ID: e.g. "space 2", "space #3", "space id 5"
        space_match = re.search(r"\bspace\s*(?:id|#)?\s*(\d+)\b", text, re.IGNORECASE)
        if space_match:
            merged["selected_space_id"] = int(space_match.group(1))

        # Booking ID: e.g. "booking 12", "booking #4", "reservation 9"
        booking_match = re.search(r"\b(?:booking|reservation)\s*#?\s*(\d+)\b", text, re.IGNORECASE)
        if booking_match:
            merged["selected_booking_id"] = int(booking_match.group(1))

        # Duration hours regex override: e.g. "for 3 hours", "2 hrs", "4h"
        dur_match = re.search(r"\b(?:for\s+)?(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h|ghante|taas)\b", text, re.IGNORECASE)
        if dur_match:
            merged["duration_hours"] = float(dur_match.group(1))

        # Budget regex override: e.g. "under 500", "₹1000", "budget 800"
        budg_match = re.search(r"(?:under|below|budget|within|₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if budg_match:
            merged["budget"] = float(budg_match.group(1))

        # Capacity regex override: e.g. "for 4 people", "6 guests", "team of 10"
        cap_match = re.search(r"(?:for\s+)?(\d+)\s*(?:people|persons|guests|seats|attendees|members|team)", text, re.IGNORECASE)
        if cap_match:
            merged["capacity"] = int(cap_match.group(1))

        # Merge amenities lists without duplicates
        existing_amenities = set(merged.get("amenities", []))
        for am in parsed.get("amenities", []):
            existing_amenities.add(am)

        # Additional regex amenity detection
        amenity_keywords = {
            "wifi": ["wifi", "wi-fi", "internet"],
            "ac": ["ac", "air condition", "air-conditioned"],
            "quiet": ["quiet", "peaceful", "silent"],
            "soundproof": ["soundproof", "acoustic", "studio"],
            "whiteboard": ["whiteboard", "marker"],
            "power": ["power", "outlets", "charging", "plugs"],
            "monitor": ["monitor", "display", "screen"],
            "coffee": ["coffee", "tea", "beverages"],
            "parking": ["parking", "valet", "garage", "vehicle", "car"],
        }
        lower = text.lower()
        for am_name, terms in amenity_keywords.items():
            if any(term in lower for term in terms):
                existing_amenities.add(am_name)

        # Ordinal reference detection: e.g. "the second one", "first one", "3rd"
        ordinal_patterns = [
            (r"\b(?:first|1st|pehla|pahila)\b", 0),
            (r"\b(?:second|2nd|dusra|doosra)\b", 1),
            (r"\b(?:third|3rd|teesra|tisra)\b", 2),
            (r"\b(?:fourth|4th|chautha)\b", 3),
            (r"\b(?:last|aakhri|shevat)\b", -1),
        ]
        for pat, idx in ordinal_patterns:
            if re.search(pat, lower):
                merged["ordinal_index"] = idx
                break

        # 'Cheaper' / 'Sasta' relative adjustment
        if re.search(r"\b(?:make\s+it\s+cheaper|cheaper|sasta|kuch\s+sasta|cheap\s+one|less\s+expensive)\b", lower):
            cur_b = merged.get("budget")
            if cur_b:
                merged["budget"] = max(150.0, round(float(cur_b) * 0.75, 2))
            else:
                merged["budget"] = 400.0

        merged["amenities"] = sorted(list(existing_amenities))
        return merged
