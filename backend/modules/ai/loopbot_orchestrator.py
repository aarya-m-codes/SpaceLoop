"""SpaceLoop LoopBot Orchestrator & Conversational Concierge Engine.

Implements the complete 8-stage LoopBot processing pipeline:
1. Receive message
2. Detect language (English, Hindi, Hinglish, Marathi)
3. Normalize text
4. Detect intent (7 core marketplace domains + platform help)
5. Extract entities (locations, dates, durations, budgets, capacities, amenities)
6. Retrieve relevant knowledge via 7-domain in-process RAG
7. Generate response via primary Groq -> fallback Gemini -> deterministic rule engine
8. Return suggested action payloads

CRITICAL INVARIANT:
AI must not control critical financial, booking, security or access decisions.
LoopBot acts strictly as an advisory concierge and recommends validated backend actions.
"""

import json
import logging
import os
import re
import secrets
import unicodedata
from datetime import datetime, timezone
from typing import Any

from backend.modules.ai.rag_service import RAGService
from backend.modules.nlp.parser import QueryParser

logger = logging.getLogger("spaceloop.ai.loopbot")


class ConversationManager:
    """In-memory multi-turn conversation session state manager."""

    _sessions: dict[str, dict[str, Any]] = {}

    @classmethod
    def get_or_create_session(cls, conversation_id: str | None = None) -> tuple[str, dict[str, Any]]:
        """Retrieve existing conversation session or initialize a fresh one."""
        if not conversation_id or conversation_id not in cls._sessions:
            new_id = conversation_id or f"conv-{secrets.token_hex(6)}"
            cls._sessions[new_id] = {
                "conversation_id": new_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "messages": [],
                "accumulated_entities": {},
                "last_intent": None,
                "language": "en",
            }
            return new_id, cls._sessions[new_id]

        session = cls._sessions[conversation_id]
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        return conversation_id, session

    @classmethod
    def append_message(
        cls,
        conversation_id: str,
        role: str,
        content: str,
        entities: dict[str, Any] | None = None,
        intent: str | None = None,
    ) -> None:
        """Store message turn and merge newly identified entities into session memory."""
        if conversation_id in cls._sessions:
            session = cls._sessions[conversation_id]
            session["messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            # Keep last 16 turns to avoid memory leak
            if len(session["messages"]) > 16:
                session["messages"] = session["messages"][-16:]

            if entities:
                for k, v in entities.items():
                    if v is not None and v != [] and v != "":
                        session["accumulated_entities"][k] = v

            if intent:
                session["last_intent"] = intent


class LoopBotOrchestrator:
    """Enterprise-grade conversational concierge orchestrator for SpaceLoop."""

    # Supported language identifiers
    LANG_EN = "en"
    LANG_HI = "hi"
    LANG_HINGLISH = "hinglish"
    LANG_MR = "mr"

    # Supported intents mapped to corresponding RAG domains
    INTENT_FIND_SPACES = "find_spaces"
    INTENT_BOOKING = "booking_reservation"
    INTENT_CANCELLATION = "cancellation_refund"
    INTENT_CHECKIN_CHECKOUT = "checkin_checkout"
    INTENT_HOST_LISTING = "host_listing"
    INTENT_PRICING_ESCROW = "pricing_escrow"
    INTENT_TRUST_SAFETY = "trust_safety"
    INTENT_PLATFORM_HELP = "platform_help"

    INTENT_DOMAIN_MAP = {
        INTENT_FIND_SPACES: "spaces_search",
        INTENT_BOOKING: "booking_reservation",
        INTENT_CANCELLATION: "cancellation_refund",
        INTENT_CHECKIN_CHECKOUT: "checkin_checkout",
        INTENT_HOST_LISTING: "host_listing",
        INTENT_PRICING_ESCROW: "pricing_escrow",
        INTENT_TRUST_SAFETY: "trust_safety",
        INTENT_PLATFORM_HELP: "spaces_search",
    }

    # =========================================================================
    # Pipeline Entry Point
    # =========================================================================

    @classmethod
    def process_message(
        cls,
        message: str | None,
        conversation_id: str | None = None,
        context: dict[str, Any] | None = None,
        language: str | None = None,
        user: Any = None,
    ) -> dict[str, Any]:
        """Execute the full 8-stage LoopBot pipeline."""
        context = context or {}

        # 1. Receive message & manage conversation context
        raw_msg = (message or "").strip()
        conv_id, session = ConversationManager.get_or_create_session(conversation_id)

        if not raw_msg:
            return cls._empty_message_response(conv_id, language or session.get("language", "en"))

        # 2. Detect language
        detected_lang = language or cls.detect_language(raw_msg)
        session["language"] = detected_lang

        # 3. Normalize text
        normalized_text = cls.normalize_text(raw_msg)

        # 4. Extract entities & merge with multi-turn context
        extracted_entities = cls.extract_entities(normalized_text, session.get("accumulated_entities", {}))

        # 5. Detect intent
        intent = cls.detect_intent(normalized_text, detected_lang, session)

        # 6. Retrieve relevant knowledge via 7-domain in-process RAG
        rag_domain = cls.INTENT_DOMAIN_MAP.get(intent, "spaces_search")
        sources = RAGService.search_knowledge(
            query=normalized_text,
            domain=rag_domain,
            top_k=3,
            language=detected_lang,
        )

        # 7. Generate response (Groq -> Gemini -> Deterministic)
        response_text, provider_used = cls.generate_response(
            message=raw_msg,
            normalized=normalized_text,
            intent=intent,
            entities=extracted_entities,
            sources=sources,
            language=detected_lang,
            session=session,
        )

        # 8. Return suggested actions
        suggested_actions = cls.generate_suggested_actions(intent, extracted_entities, detected_lang)

        # Update session memory
        ConversationManager.append_message(
            conversation_id=conv_id,
            role="user",
            content=raw_msg,
            entities=extracted_entities,
            intent=intent,
        )
        ConversationManager.append_message(
            conversation_id=conv_id,
            role="assistant",
            content=response_text,
        )

        # Standard SpaceLoop payload contract
        return {
            "response": response_text,
            "intent": intent,
            "language": detected_lang,
            "sources": [
                {
                    "domain": s.get("domain"),
                    "title": s.get("title"),
                    "snippet": s.get("snippet"),
                }
                for s in sources
            ],
            "suggested_actions": suggested_actions,
            "conversation_id": conv_id,
            "provider": provider_used,
        }

    # =========================================================================
    # Stage 2: Language Detection
    # =========================================================================

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect language across English, Hindi, Hinglish, and Marathi."""
        if not text:
            return cls.LANG_EN

        # Check for Devanagari script (\u0900 - \u097F)
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", text))

        if has_devanagari:
            # Check distinctive Marathi Devanagari vocabulary
            marathi_markers = [
                "आहे", "नाही", "पाहिजे", "कसे", "मला", "शोधत", "शोधतो", "भाडे", "कार्यालय",
                "स्थान", "माहिती", "कसा", "करा", "नका", "होय", "किती", "झाले", "मिळेल",
                "पुणे", "मुंबई", "जागा", "कशी", "करावे", "नमस्कार", "थेट",
            ]
            for m in marathi_markers:
                if m in text:
                    return cls.LANG_MR
            return cls.LANG_HI

        # Romanized text: Check Romanized Marathi markers
        marathi_roman_patterns = [
            r"\bahe\b", r"\bnahi\b", r"\bpahije\b", r"\bkashi\b", r"\bkiti\b", r"\bkuthe\b",
            r"\bmadhe\b", r"\bmala\b", r"\bsangava\b", r"\bmahiti\b", r"\bkaraychi\b",
            r"\bbhaden\b", r"\bkarave\b", r"\bshodh\b",
        ]
        for pat in marathi_roman_patterns:
            if re.search(pat, text, re.IGNORECASE):
                return cls.LANG_MR

        # Romanized text: Check Hinglish markers
        hinglish_patterns = [
            r"\bmujhe\b", r"\bchahiye\b", r"\bmein\b", r"\bkaise\b", r"\bhoga\b", r"\bkarna\b",
            r"\bhai\b", r"\bkya\b", r"\bsath\b", r"\bpaise\b", r"\bbatao\b", r"\bkarein\b",
            r"\bkitna\b", r"\bmilega\b", r"\bdekhna\b", r"\bbataiye\b", r"\bkaru\b", r"\braha\b",
            r"\brahi\b", r"\bhain\b", r"\bki\b", r"\bse\b", r"\bko\b", r"\baap\b", r"\bhum\b",
            r"\bkare\b", r"\bkaha\b", r"\bkab\b", r"\bkisko\b", r"\brupaye\b", r"\bkamra\b",
        ]
        for pat in hinglish_patterns:
            if re.search(pat, text, re.IGNORECASE):
                return cls.LANG_HINGLISH

        return cls.LANG_EN

    # =========================================================================
    # Stage 3: Normalization
    # =========================================================================

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Unicode, strip redundant whitespace and punctuation while keeping script integrity."""
        nfkd = unicodedata.normalize("NFKD", text)
        cleaned = re.sub(r"[\s\t\r\n]+", " ", nfkd)
        return cleaned.strip()

    # =========================================================================
    # Stage 4: Intent Detection
    # =========================================================================

    @classmethod
    def detect_intent(cls, text: str, language: str, session: dict[str, Any]) -> str:
        """Classify message intent into one of the 7 core domains or platform help."""
        lower = text.lower()

        # 1. Cancellation & Refund intent
        cancel_patterns = [
            r"cancel", r"refund", r"money back", r"vapasi", r"paratam", r"radd",
            r"रिफंड", r"कैंसिल", r"रद्द", r"परत", r"पैसे परत", r"paise wapas",
            r"booking cancel", r"slot cancel",
        ]
        if any(re.search(pat, lower) for pat in cancel_patterns):
            return cls.INTENT_CANCELLATION

        # 2. Check-in, Check-out & PIN Access intent
        checkin_patterns = [
            r"check-?in", r"check-?out", r"arrival pin", r"\bpin\b", r"door code",
            r"key", r"unlock", r"lock", r"geofence", r"gps", r"inspection photo",
            r"पिन", r"चेक इन", r"चेक आउट", r"प्रवेश", r"दार", r"चाबी", r"darwaza",
            r"entry code", r"access code",
        ]
        if any(re.search(pat, lower) for pat in checkin_patterns):
            return cls.INTENT_CHECKIN_CHECKOUT

        # 3. Trust, Safety, KYC & Disputes (checked BEFORE host listing to handle 'is host verified?')
        trust_patterns = [
            r"trust score", r"objective trust", r"verified", r"verification", r"safety", r"safe",
            r"secure", r"kyc", r"dispute", r"freeze", r"fraud", r"scam", r"सुरक्षा",
            r"विश्वास", r"तक्रार", r"विवाद", r"suraksha", r"report", r"complain",
        ]
        if any(re.search(pat, lower) for pat in trust_patterns):
            return cls.INTENT_TRUST_SAFETY

        # 4. Host listing & space management
        host_patterns = [
            r"list my space", r"list a space", r"add listing", r"monetize",
            r"become a host", r"earn", r"payout", r"होस्ट", r"लिस्टिंग", r"जागा जोडा",
            r"कमाई", r"पैसे कमवा", r"space register", r"create space", r"host listing",
            r"list space", r"host as",
        ]
        if any(re.search(pat, lower) for pat in host_patterns):
            return cls.INTENT_HOST_LISTING

        # 5. Pricing & Micro-escrow formula
        pricing_patterns = [
            r"platform fee", r"5%", r"5 percent", r"escrow deposit", r"₹100", r"100 deposit",
            r"pricing", r"how much does it cost", r"fee structure", r"ledger", r"upi vpa",
            r"शुल्क", r"किराया", r"भाडे", r"किती पैसे", r"kitna paisa", r"kitna kharcha",
            r"security deposit", r"breakdown",
        ]
        if any(re.search(pat, lower) for pat in pricing_patterns):
            return cls.INTENT_PRICING_ESCROW

        # 6. Booking & Precheck
        booking_patterns = [
            r"book", r"booking", r"reserve", r"reservation", r"precheck", r"schedule",
            r"minimum hours", r"slot", r"availability", r"बुकिंग", r"आरक्षण", r"उपलब्ध",
            r"kaise book kare", r"book karaychi", r"slot book",
        ]
        if any(re.search(pat, lower) for pat in booking_patterns):
            return cls.INTENT_BOOKING

        # 7. Greetings & General Platform Help
        greeting_patterns = [
            r"\bhi\b", r"\bhello\b", r"\bhey\b", r"\bnamaste\b", r"\bnamaskar\b",
            r"\bhelp\b", r"what is spaceloop", r"kya hai", r"kaise kaam karta hai",
            r"नमस्ते", r"नमस्कार", r"मदत",
        ]
        if any(re.search(pat, lower) for pat in greeting_patterns):
            return cls.INTENT_PLATFORM_HELP

        # 8. Finding Spaces & Discovery
        search_patterns = [
            r"find", r"search", r"desk", r"studio", r"office", r"\broom\b", r"cabin",
            r"meeting", r"coworking", r"\bspaces?\b", r"indiranagar", r"koramangala",
            r"bengaluru", r"mumbai", r"delhi", r"pune", r"hyderabad", r"wifi", r"quiet",
            r"soundproof", r"ac", r"खोज", r"स्थान", r"शोध", r"पाहिजे", r"चाहिए",
            r"dhoond", r"looking for",
        ]
        if any(re.search(pat, lower) for pat in search_patterns):
            return cls.INTENT_FIND_SPACES

        # Default fallback to finding spaces or previous session intent
        return session.get("last_intent") or cls.INTENT_FIND_SPACES

    # =========================================================================
    # Stage 5: Entity Extraction
    # =========================================================================

    @classmethod
    def extract_entities(cls, text: str, context_entities: dict[str, Any]) -> dict[str, Any]:
        """Extract structured marketplace entities, merging with conversation context."""
        parsed = QueryParser.parse_query(text)

        # Merge with context: current message takes precedence over previous context
        merged = dict(context_entities)
        for key in [
            "city", "neighborhood", "latitude", "longitude", "date", "time",
            "duration_hours", "budget", "capacity", "space_type", "use_case",
        ]:
            val = parsed.get(key)
            if val is not None:
                merged[key] = val

        # Merge amenities lists without duplicates
        existing_amenities = set(merged.get("amenities", []))
        for am in parsed.get("amenities", []):
            existing_amenities.add(am)
        merged["amenities"] = sorted(list(existing_amenities))

        # Check for booking ID references: e.g. "booking #12" or "booking 45"
        booking_match = re.search(r"\bbooking\s*#?(\d+)\b", text, re.IGNORECASE)
        if booking_match:
            merged["booking_id"] = int(booking_match.group(1))

        return merged

    # =========================================================================
    # Stage 7: Response Generation (Groq -> Gemini -> Deterministic)
    # =========================================================================

    @classmethod
    def generate_response(
        cls,
        message: str,
        normalized: str,
        intent: str,
        entities: dict[str, Any],
        sources: list[dict[str, Any]],
        language: str,
        session: dict[str, Any],
    ) -> tuple[str, str]:
        """Generate response via Groq -> Gemini -> Deterministic fallback."""
        # Tier 1: Groq LLM
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                res = cls._call_groq(groq_key, message, intent, entities, sources, language, session)
                if res:
                    return res, "groq"
            except Exception as exc:
                logger.warning(f"Groq API call failed: {exc}. Cascading to Gemini fallback.")

        # Tier 2: Google Gemini LLM
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                res = cls._call_gemini(gemini_key, message, intent, entities, sources, language, session)
                if res:
                    return res, "gemini"
            except Exception as exc:
                logger.warning(f"Gemini API call failed: {exc}. Cascading to deterministic fallback.")

        # Tier 3: Guaranteed Deterministic Knowledge Rule Engine
        res = cls._generate_deterministic_response(intent, entities, sources, language)
        return res, "deterministic"

    # -------------------------------------------------------------------------
    # LLM Integrations
    # -------------------------------------------------------------------------

    @classmethod
    def _build_system_prompt(cls, intent: str, sources: list[dict[str, Any]], language: str) -> str:
        """Construct strict grounded prompt preventing unauthorized mutations."""
        context_block = RAGService.build_llm_context(sources)

        return (
            "You are LoopBot, the official intelligent concierge for SpaceLoop—India's peer-to-peer physical "
            "space marketplace for desks, private offices, soundproof studios, and meeting rooms.\n\n"
            f"DETECTED USER LANGUAGE: {language.upper()}.\n"
            "CRITICAL SAFETY RULE: You are an advisory concierge. You MUST NOT execute financial, booking, or "
            "security mutations directly. You can recommend actions, but remind users to confirm them through the UI.\n\n"
            "CORE SPACELOOP PLATFORM RULES:\n"
            "- Pricing: Space Subtotal = hourly rate × duration hours. 5% platform fee. ₹100 refundable deposit.\n"
            "- Total Paid = Subtotal + 5% platform fee + ₹100.\n"
            "- Cancellation Rule: SpaceLoop retains ONLY the 5% platform fee. The seeker receives 100% of rental "
            "amount + 100% of ₹100 security deposit.\n"
            "- Host Rejection: Seeker receives 100% full refund.\n"
            "- Check-in requires 4-digit arrival PIN, 50-meter GPS geofencing, and inspection photos.\n"
            "- Objective Trust Score is 0 to 100.\n\n"
            f"{context_block}\n\n"
            "Instructions:\n"
            "1. Answer concisely, helpfully, and politely in the user's language.\n"
            "2. Ground your answer in the provided SpaceLoop specification rules above.\n"
            "3. Mention specific details (fees, ₹100 deposit, 4-digit PIN, locations) accurately."
        )

    @classmethod
    def _call_groq(
        cls,
        api_key: str,
        message: str,
        intent: str,
        entities: dict[str, Any],
        sources: list[dict[str, Any]],
        language: str,
        session: dict[str, Any],
    ) -> str | None:
        """Call Groq API using LLaMA 3.3 70B."""
        import groq
        client = groq.Groq(api_key=api_key, timeout=2.0)

        system_prompt = cls._build_system_prompt(intent, sources, language)

        messages = [{"role": "system", "content": system_prompt}]
        for turn in session.get("messages", [])[-4:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": message})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )

        if completion and completion.choices:
            return completion.choices[0].message.content.strip()
        return None

    @classmethod
    def _call_gemini(
        cls,
        api_key: str,
        message: str,
        intent: str,
        entities: dict[str, Any],
        sources: list[dict[str, Any]],
        language: str,
        session: dict[str, Any],
    ) -> str | None:
        """Call Google Gemini 2.5 Flash API."""
        from google import genai
        client = genai.Client(api_key=api_key)

        system_prompt = cls._build_system_prompt(intent, sources, language)
        full_prompt = f"{system_prompt}\n\nUser Question:\n{message}\n\nHelpful SpaceLoop Response:"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )

        if response and response.text:
            return response.text.strip()
        return None

    # -------------------------------------------------------------------------
    # Deterministic Rule Engine (100% Resilience Guarantee)
    # -------------------------------------------------------------------------

    @classmethod
    def _generate_deterministic_response(
        cls,
        intent: str,
        entities: dict[str, Any],
        sources: list[dict[str, Any]],
        language: str,
    ) -> str:
        """Produce fully grounded, natural, multilingual response with zero external dependencies."""
        city = entities.get("city") or "your area"
        neighborhood = entities.get("neighborhood")
        loc_str = f"{neighborhood.title()}, {city.title()}" if neighborhood else city.title()
        space_type = entities.get("space_type") or "space"
        budget = entities.get("budget")
        duration = entities.get("duration_hours") or 2.0

        # ==================== English Responses ====================
        if language == cls.LANG_EN:
            if intent == cls.INTENT_FIND_SPACES:
                budget_info = f" with hourly budgets under ₹{budget}" if budget else ""
                return (
                    f"I can help you find verified physical {space_type}s in {loc_str}{budget_info}. "
                    f"SpaceLoop matches listings within 2km to 25km using acoustic noise levels, high-speed WiFi, "
                    f"and host trust scores. Click below to browse active spaces or refine your filters."
                )

            elif intent == cls.INTENT_BOOKING:
                return (
                    f"To book a space on SpaceLoop: 1) Run an instant precheck to verify slot availability and minimum "
                    f"hours. 2) Submit your reservation. 3) Once the host accepts, you'll receive a secure 4-digit arrival "
                    f"PIN for physical access. No overlapping bookings are ever allowed for the same slot."
                )

            elif intent == cls.INTENT_CANCELLATION:
                return (
                    "Here is SpaceLoop's cancellation policy: When you cancel a booking, SpaceLoop retains only the "
                    "5% platform fee. You receive 100% of your rental subtotal plus 100% of the ₹100 security deposit "
                    "back to your account. If the host rejects your booking, you receive a full 100% refund."
                )

            elif intent == cls.INTENT_CHECKIN_CHECKOUT:
                return (
                    "For seamless check-in: 1) Enter your 4-digit arrival PIN at the door. 2) Your phone confirms you are "
                    "within the 50-meter GPS geofence. 3) Upload quick check-in inspection photos to document space condition. "
                    "Repeat photo upload at check-out to safely release your ₹100 deposit."
                )

            elif intent == cls.INTENT_HOST_LISTING:
                return (
                    "To list your space on SpaceLoop: Upload photos (up to 5MB with verified image headers), set your hourly "
                    "rate and capacity, and complete KYC verification. After a seeker's session completes, your payout is "
                    "released directly to your verified UPI VPA with zero listing subscription fees."
                )

            elif intent == cls.INTENT_PRICING_ESCROW:
                return (
                    "SpaceLoop uses a transparent micro-escrow pricing model: Space Subtotal = hourly rate × duration hours. "
                    "Platform fee = 5% of subtotal. Refundable security deposit = ₹100.00. Total paid = Subtotal + 5% Fee + ₹100. "
                    "Upon normal checkout, the host receives the subtotal, SpaceLoop retains the 5% fee, and the ₹100 deposit is returned."
                )

            elif intent == cls.INTENT_TRUST_SAFETY:
                return (
                    "SpaceLoop protects hosts and seekers with an Objective Trust Score (0-100), government KYC identity "
                    "verification, and automated escrow protection. In case of any dispute or access failure, escrow funds "
                    "are immediately frozen while administrators adjudicate."
                )

            else:  # Platform help / greeting
                return (
                    "Hello! I am LoopBot, your SpaceLoop concierge. I can help you discover workspaces, studios, "
                    "and meeting rooms, understand our 5% fee & ₹100 escrow deposit, explain check-in PINs, or guide you through listing a space."
                )

        # ==================== Hinglish Responses ====================
        elif language == cls.LANG_HINGLISH:
            if intent == cls.INTENT_FIND_SPACES:
                return (
                    f"Main aapke liye {loc_str} mein best physical {space_type}s search kar sakta hoon. "
                    f"Aap hourly budget, soundproofing, high-speed WiFi aur AC ke sath filter kar sakte hain. "
                    f"Active spaces dekhne ke liye neeche diye gaye action par click karein."
                )

            elif intent == cls.INTENT_BOOKING:
                return (
                    "SpaceLoop par booking karna bahut aasan hai: Pehle availability precheck karein, phir reservation "
                    "submit karein. Host accept karte hi aapko ek secure 4-digit arrival PIN mil jayega jisse aap space enter kar sakte hain."
                )

            elif intent == cls.INTENT_CANCELLATION:
                return (
                    "SpaceLoop cancellation policy bilkul transparent hai: Cancellation par sirf 5% platform fee retain "
                    "hoti hai. Aapko rental subtotal ka 100% aur ₹100 security deposit ka 100% wapas mil jata hai. "
                    "Agar host reject kare, toh poora 100% refund milta hai."
                )

            elif intent == cls.INTENT_CHECKIN_CHECKOUT:
                return (
                    "Check-in ke liye: 1) Booking confirmation ka 4-digit arrival PIN enter karein. 2) App GPS se verify karega "
                    "ki aap space ke 50m ke andar hain. 3) Condition photos upload karein taaki ₹100 deposit safe rahe."
                )

            elif intent == cls.INTENT_HOST_LISTING:
                return (
                    "Apna physical space list karne ke liye: Photos upload karein (up to 5MB), apna hourly price set karein, "
                    "aur KYC verify karein. Seeker ke checkout ke baad aapka payout seedhe aapke UPI VPA par release ho jata hai."
                )

            elif intent == cls.INTENT_PRICING_ESCROW:
                return (
                    "SpaceLoop pricing formula: Subtotal = hourly rate × duration hours. Platform fee = 5%. "
                    "Refundable deposit = ₹100. Total payment = Subtotal + 5% fee + ₹100 deposit. Checkout par host ko subtotal "
                    "milta hai aur ₹100 deposit seeker ko wapas ho jata hai."
                )

            elif intent == cls.INTENT_TRUST_SAFETY:
                return (
                    "SpaceLoop par safety sabse pehle hai: Har host ka Objective Trust Score (0-100) hota hai, KYC verified "
                    "users hote hain, aur kisi bhi samasya par dispute file karke escrow funds freeze kiye ja sakte hain."
                )

            else:
                return (
                    "Namaste! Main hoon LoopBot, aapka SpaceLoop AI concierge. Main spaces dhoondhne, booking precheck, "
                    "cancellation rules (5% fee + ₹100 deposit return), aur check-in PIN mein aapki madad kar sakta hoon."
                )

        # ==================== Hindi Responses (हिंदी) ====================
        elif language == cls.LANG_HI:
            if intent == cls.INTENT_FIND_SPACES:
                return (
                    f"मैं {loc_str} में आपके लिए सत्यापित {space_type} खोजने में सहायता कर सकता हूँ। "
                    f"आप प्रति घंटे के बजट, शांत वातावरण (ध्वनिरोधी), वाई-फाई और एसी के अनुसार फ़िल्टर कर सकते हैं।"
                )

            elif intent == cls.INTENT_CANCELLATION:
                return (
                    "SpaceLoop की रद्दीकरण नीति: रद्दीकरण पर केवल 5% प्लेटफ़ॉर्म शुल्क काटा जाता है। "
                    "आपको किराए का 100% और ₹100 सुरक्षा जमा राशि पूरी तरह वापस मिल जाती है। "
                    "यदि होस्ट अस्वीकार करता है, तो 100% पूरा रिफंड मिलता है।"
                )

            elif intent == cls.INTENT_PRICING_ESCROW:
                return (
                    "SpaceLoop मूल्य निर्धारण: उप-योग = प्रति घंटा दर × कुल घंटे। 5% प्लेटफ़ॉर्म शुल्क। "
                    "वापसी योग्य एस्क्रो जमा = ₹100। कुल भुगतान = उप-योग + 5% शुल्क + ₹100 जमा। "
                    "सफल चेकआउट पर होस्ट को किराया मिलता है और ₹100 जमा राशि वापस आ जाती है।"
                )

            elif intent == cls.INTENT_CHECKIN_CHECKOUT:
                return (
                    "चेक-इन के लिए: 1) अपना 4-अंकीय आगमन पिन दर्ज करें। 2) जीपीएस पुष्टि करता है कि आप 50 मीटर के दायरे में हैं। "
                    "3) अपनी सुरक्षा के लिए चेक-इन और चेक-आउट की तस्वीरें अपलोड करें।"
                )

            elif intent == cls.INTENT_BOOKING:
                return (
                    "बुकिंग के लिए: पहले उपलब्धता और न्यूनतम घंटों की प्री-चेक जाँच करें। "
                    "होस्ट की स्वीकृति पर आपको भौतिक प्रवेश के लिए एक सुरक्षित 4-अंकीय आगमन पिन प्रदान किया जाएगा।"
                )

            elif intent == cls.INTENT_HOST_LISTING:
                return (
                    "होस्ट बनने के लिए: अपने स्थान की तस्वीरें अपलोड करें, प्रति घंटा दर निर्धारित करें और केवाईसी पूर्ण करें। "
                    "चेकआउट के बाद आपकी कमाई सीधे आपके यूपीआई खाते में जमा कर दी जाती है।"
                )

            elif intent == cls.INTENT_TRUST_SAFETY:
                return (
                    "सुरक्षा और विश्वास: सभी सदस्यों का ऑब्जेक्टिव ट्रस्ट स्कोर (0-100) और केवाईसी सत्यापन होता है। "
                    "किसी भी असुविधा की स्थिति में विवाद दर्ज करने पर एस्क्रो राशि तुरंत फ़्रीज़ कर दी जाती है।"
                )

            else:
                return (
                    "नमस्ते! मैं लूपबॉट (LoopBot) हूँ, आपका स्पेस-लूप सहायक। मैं स्थान खोजने, बुकिंग, 5% शुल्क नियम, "
                    "और चेक-इन पिन में आपकी पूरी सहायता कर सकता हूँ।"
                )

        # ==================== Marathi Responses (मराठी) ====================
        else:
            if intent == cls.INTENT_FIND_SPACES:
                return (
                    f"मी तुम्हाला {loc_str} मध्ये पडताळणी केलेली {space_type} शोधण्यात मदत करू शकतो. "
                    f"तुम्ही तासाचे भाडे, शांत जागा, वाय-फाय आणि वातानुकूलन यानुसार शोध घेऊ शकता."
                )

            elif intent == cls.INTENT_CANCELLATION:
                return (
                    "SpaceLoop रद्द करण्याचे धोरण: बुकिंग रद्द केल्यास फक्त 5% प्लॅटफॉर्म शुल्क कापले जाते. "
                    "तुम्हाला जागेच्या भाड्याचे 100% आणि ₹100 सुरक्षा ठेव पूर्णपणे परत मिळते. "
                    "होस्टने नकार दिल्यास 100% संपूर्ण परतावा मिळतो."
                )

            elif intent == cls.INTENT_PRICING_ESCROW:
                return (
                    "SpaceLoop किंमत रचना: एकूण भाडे = ताशी दर × तास. प्लॅटफॉर्म शुल्क = 5%. "
                    "परत मिळणारी ठेव = ₹100. एकूण रक्कम = भाडे + 5% शुल्क + ₹100 ठेव. "
                    "सत्र पूर्ण झाल्यावर होस्टला भाडे मिळते आणि ₹100 ठेव तुम्हाला परत केली जाते."
                )

            elif intent == cls.INTENT_CHECKIN_CHECKOUT:
                return (
                    "चेक-इन पद्धत: 1) आपला 4-अंकी आगमन पिन वापरा. 2) जीपीएसद्वारे 50 मीटर अंतराची खात्री केली जाते. "
                    "3) जागेच्या स्थितीचे फोटो अपलोड करा, जेणेकरून तुमची ठेव सुरक्षित राहील."
                )

            elif intent == cls.INTENT_BOOKING:
                return (
                    "बुकिंग करण्यासाठी: प्रथम उपलब्धता आणि किमान तास तपासा. "
                    "होस्टने मान्यता दिल्यानंतर प्रत्यक्ष प्रवेशासाठी सुरक्षित 4-अंकी पिन दिला जातो."
                )

            elif intent == cls.INTENT_HOST_LISTING:
                return (
                    "जागा भाड्याने देण्यासाठी: जागेचे फोटो अपलोड करा, ताशी दर ठरवा आणि केवायसी पूर्ण करा. "
                    "चेकआउटनंतर तुमचे पैसे थेट तुमच्या युपीआय (UPI) खात्यात जमा केले जातात."
                )

            elif intent == cls.INTENT_TRUST_SAFETY:
                return (
                    "सुरक्षा आणि विश्वास: प्रत्येक सदस्याचा ऑब्जेक्टिव्ह ट्रस्ट स्कोर (0-100) आणि केवायसी पडताळणी असते. "
                    "काही अडचण आल्यास वाद नोंदवून रक्कम तात्काळ गोठवली (Freeze) जाते."
                )

            else:
                return (
                    "नमस्कार! मी लूपबॉट (LoopBot), स्पेस-लूपचा डिजिटल सहाय्यक. मी जागा शोधणे, बुकिंग, "
                    "5% शुल्क नियम आणि चेक-इन पिनमध्ये आपली मदत करू शकतो."
                )

    # =========================================================================
    # Stage 8: Suggested Actions
    # =========================================================================

    @classmethod
    def generate_suggested_actions(
        cls,
        intent: str,
        entities: dict[str, Any],
        language: str,
    ) -> list[dict[str, Any]]:
        """Return contextually appropriate actionable quick-buttons for the frontend UI."""
        city = entities.get("city")
        neighborhood = entities.get("neighborhood")

        actions: list[dict[str, Any]] = []

        if intent == cls.INTENT_FIND_SPACES:
            label = f"Browse Spaces in {neighborhood.title() if neighborhood else (city.title() if city else 'Area')}"
            actions.append({
                "type": "search_spaces",
                "label": label,
                "payload": {
                    "city": city,
                    "neighborhood": neighborhood,
                    "space_type": entities.get("space_type"),
                    "budget": entities.get("budget"),
                },
            })
            actions.append({
                "type": "filter_amenities",
                "label": "Filter by High-Speed WiFi & AC",
                "payload": {"amenities": ["wifi", "ac", "quiet"]},
            })

        elif intent == cls.INTENT_BOOKING:
            actions.append({
                "type": "open_precheck",
                "label": "Check Slot Availability & Pricing",
                "payload": {
                    "duration_hours": entities.get("duration_hours") or 2.0,
                    "city": city,
                },
            })
            actions.append({
                "type": "my_bookings",
                "label": "View My Bookings",
                "payload": {},
            })

        elif intent == cls.INTENT_CANCELLATION:
            actions.append({
                "type": "view_cancellation_policy",
                "label": "View Cancellation Policy (5% Fee)",
                "payload": {"retained_fee_pct": 5.0, "refundable_deposit": 100.0},
            })
            actions.append({
                "type": "my_bookings",
                "label": "Go to My Bookings",
                "payload": {},
            })

        elif intent == cls.INTENT_CHECKIN_CHECKOUT:
            actions.append({
                "type": "checkin_guide",
                "label": "Arrival PIN & GPS Check-in Guide",
                "payload": {"geofence_meters": 50},
            })
            if entities.get("booking_id"):
                actions.append({
                    "type": "view_pin",
                    "label": f"View PIN for Booking #{entities['booking_id']}",
                    "payload": {"booking_id": entities["booking_id"]},
                })

        elif intent == cls.INTENT_HOST_LISTING:
            actions.append({
                "type": "create_listing",
                "label": "List Your Physical Space",
                "payload": {},
            })
            actions.append({
                "type": "host_payout_guide",
                "label": "Host UPI Payout Setup",
                "payload": {},
            })

        elif intent == cls.INTENT_PRICING_ESCROW:
            actions.append({
                "type": "view_pricing_breakdown",
                "label": "Fee Breakdown (5% Fee + ₹100 Deposit)",
                "payload": {"fee_rate": 0.05, "deposit": 100.0},
            })
            actions.append({
                "type": "verify_vpa",
                "label": "Verify UPI VPA via Penny Drop",
                "payload": {},
            })

        elif intent == cls.INTENT_TRUST_SAFETY:
            actions.append({
                "type": "view_trust_guidelines",
                "label": "Objective Trust Score Guidelines",
                "payload": {},
            })
            actions.append({
                "type": "file_dispute",
                "label": "How to Freeze Escrow via Dispute",
                "payload": {},
            })

        else:  # Platform help / greeting
            actions.append({
                "type": "search_spaces",
                "label": "Explore Physical Spaces",
                "payload": {},
            })
            actions.append({
                "type": "create_listing",
                "label": "List a Space as Host",
                "payload": {},
            })

        return actions

    @classmethod
    def _empty_message_response(cls, conversation_id: str, language: str) -> dict[str, Any]:
        """Helpful prompt for empty initial message requests."""
        if language in [cls.LANG_HI, cls.LANG_HINGLISH]:
            resp = "Namaste! Main SpaceLoop LoopBot hoon. Main spaces dhoondhne, booking precheck ya fees samajhne mein aapki kaise madad kar sakta hoon?"
        elif language == cls.LANG_MR:
            resp = "नमस्कार! मी स्पेस-लूप लूपबॉट आहे. जागा शोधण्यासाठी किंवा बुकिंगसाठी मी आपली कशी मदत करू?"
        else:
            resp = "Hello! I am LoopBot, your SpaceLoop concierge. How can I assist you with space discovery, booking prechecks, or platform policies today?"

        return {
            "response": resp,
            "intent": cls.INTENT_PLATFORM_HELP,
            "language": language,
            "sources": [],
            "suggested_actions": [
                {"type": "search_spaces", "label": "Explore Spaces", "payload": {}},
                {"type": "create_listing", "label": "List a Space", "payload": {}},
            ],
            "conversation_id": conversation_id,
            "provider": "deterministic",
        }
