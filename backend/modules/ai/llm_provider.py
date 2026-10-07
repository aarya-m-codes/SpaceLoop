"""LLM provider abstraction with resilient fallback cascade for SpaceLoop LoopBot.

Cascade Order:
1. Primary: Groq LLM (llama-3.3-70b-versatile)
2. Fallback: Google Gemini LLM (gemini-1.5-flash / gemini-2.5-flash)
3. Guaranteed Final Fallback: Multilingual Deterministic Knowledge Engine (100% Uptime)
"""

import logging
import os
from typing import Any

from backend.modules.ai.intent_parser import IntentParser
from backend.modules.ai.rag_service import RAGService

logger = logging.getLogger("spaceloop.ai.llm")


class LLMProvider:
    """Manages AI provider routing with strict zero-failure fallback cascade."""

    @classmethod
    def generate_response(
        cls,
        user_message: str,
        normalized_text: str,
        intent: str,
        entities: dict[str, Any],
        sources: list[dict[str, Any]],
        language: str,
        conversation_history: list[dict[str, Any]],
        tool_data: dict[str, Any] | None = None,
        pending_action: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        """Generate conversational response text and report provider used ('groq', 'gemini', 'deterministic')."""
        # 1. Primary: Groq API
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                res = cls._call_groq(
                    api_key=groq_key,
                    user_message=user_message,
                    intent=intent,
                    entities=entities,
                    sources=sources,
                    language=language,
                    conversation_history=conversation_history,
                    tool_data=tool_data,
                    pending_action=pending_action,
                )
                if res and res.strip():
                    return res.strip(), "groq"
            except Exception as exc:
                logger.warning(f"Primary Groq generation failed: {exc}. Cascading to Gemini fallback.")

        # 2. Fallback: Google Gemini API
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                res = cls._call_gemini(
                    api_key=gemini_key,
                    user_message=user_message,
                    intent=intent,
                    entities=entities,
                    sources=sources,
                    language=language,
                    conversation_history=conversation_history,
                    tool_data=tool_data,
                    pending_action=pending_action,
                )
                if res and res.strip():
                    return res.strip(), "gemini"
            except Exception as exc:
                logger.warning(f"Fallback Gemini generation failed: {exc}. Cascading to deterministic rule engine.")

        # 3. Guaranteed Final Fallback: Multilingual Deterministic Rule Engine
        res = cls._generate_deterministic_response(
            intent=intent,
            entities=entities,
            sources=sources,
            language=language,
            tool_data=tool_data,
            pending_action=pending_action,
        )
        return res, "deterministic"

    # =========================================================================
    # System Prompt Construction
    # =========================================================================
    @classmethod
    def _build_system_prompt(
        cls,
        intent: str,
        sources: list[dict[str, Any]],
        language: str,
        tool_data: dict[str, Any] | None = None,
        pending_action: dict[str, Any] | None = None,
    ) -> str:
        """Construct authoritative grounded prompt enforcing SpaceLoop invariants."""
        context_block = RAGService.build_llm_context(sources)
        tool_context = f"Verified Live Platform Data: {tool_data}" if tool_data else "No live tool state queried."
        pending_context = f"Pending Confirmation Action: {pending_action}" if pending_action else ""

        return (
            "You are LoopBot, the native AI concierge and platform assistant for SpaceLoop "
            "— India's peer-to-peer physical workspace marketplace (desks, studios, offices, meeting rooms).\n\n"
            f"USER LANGUAGE: {language.upper()}.\n\n"
            "CRITICAL INVARIANTS:\n"
            "1. You NEVER execute unauthorized financial or booking mutations. Every consequential action "
            "(booking creation or cancellation) requires explicit confirmation.\n"
            "2. PRICING FORMULA: Space Subtotal = hourly rate × duration hours. Platform fee = 5% of subtotal. "
            "Refundable security deposit = ₹100.00. Total paid = Subtotal + 5% Fee + ₹100.\n"
            "3. CANCELLATION: SpaceLoop retains ONLY the 5% platform fee. Seeker receives 100% rental subtotal "
            "+ 100% of ₹100 deposit refunded. On host rejection, seeker gets full 100% refund of all fees.\n"
            "4. PHYSICAL ACCESS: 15-minute temporal window guard before start time, 50m GPS geofencing (Haversine), "
            "4-digit arrival PIN fallback, dynamic QR code, and AccessLog.\n"
            "5. LEGAL: All bookings are revocable leave-and-license under Section 52 of the Indian Easements Act 1882; "
            "no tenancy or leasehold rights are ever created.\n"
            "6. Ground your answers strictly in the verified platform specifications and tool data below.\n\n"
            f"{context_block}\n\n"
            f"{tool_context}\n"
            f"{pending_context}\n"
        )

    # =========================================================================
    # Tier 1: Groq LLM
    # =========================================================================
    @classmethod
    def _call_groq(
        cls,
        api_key: str,
        user_message: str,
        intent: str,
        entities: dict[str, Any],
        sources: list[dict[str, Any]],
        language: str,
        conversation_history: list[dict[str, Any]],
        tool_data: dict[str, Any] | None,
        pending_action: dict[str, Any] | None,
    ) -> str | None:
        """Execute inference using Groq LLaMA 3.3 70B."""
        import groq
        client = groq.Groq(api_key=api_key, timeout=3.0)

        sys_prompt = cls._build_system_prompt(intent, sources, language, tool_data, pending_action)
        messages = [{"role": "system", "content": sys_prompt}]

        for turn in conversation_history[-4:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )
        if completion and completion.choices:
            return completion.choices[0].message.content
        return None

    # =========================================================================
    # Tier 2: Gemini LLM
    # =========================================================================
    @classmethod
    def _call_gemini(
        cls,
        api_key: str,
        user_message: str,
        intent: str,
        entities: dict[str, Any],
        sources: list[dict[str, Any]],
        language: str,
        conversation_history: list[dict[str, Any]],
        tool_data: dict[str, Any] | None,
        pending_action: dict[str, Any] | None,
    ) -> str | None:
        """Execute inference using Google Gemini 2.5/1.5 Flash."""
        from google import genai
        client = genai.Client(api_key=api_key)

        sys_prompt = cls._build_system_prompt(intent, sources, language, tool_data, pending_action)
        full_prompt = f"{sys_prompt}\n\nUser Question:\n{user_message}\n\nConcierge Response:"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )
        if response and response.text:
            return response.text
        return None

    # =========================================================================
    # Tier 3: Multilingual Deterministic Rule Engine
    # =========================================================================
    @classmethod
    def _generate_deterministic_response(
        cls,
        intent: str,
        entities: dict[str, Any],
        sources: list[dict[str, Any]],
        language: str,
        tool_data: dict[str, Any] | None = None,
        pending_action: dict[str, Any] | None = None,
    ) -> str:
        """Produce authoritative deterministic responses with 100% resilience across all 4 languages."""
        city = entities.get("city") or "your area"
        neighborhood = entities.get("neighborhood")
        loc_str = f"{neighborhood.title()}, {city.title()}" if neighborhood else city.title()
        space_type = entities.get("space_type") or "space"
        budget = entities.get("budget")
        duration = entities.get("duration_hours") or 2.0

        # If there is a pending confirmation action, explain it clearly
        if pending_action:
            act_type = pending_action.get("action")
            summary = pending_action.get("action_summary", "")
            if language == IntentParser.LANG_EN:
                return (
                    f"Action Confirmation Required: {summary}\n\n"
                    f"Please confirm by replying 'Yes' or 'Confirm' to proceed, or 'Cancel' to abort."
                )
            elif language in (IntentParser.LANG_HI, IntentParser.LANG_HINGLISH):
                return (
                    f"Action Confirmation Chahiye: {summary}\n\n"
                    f"Aage badhne ke liye 'Yes' ya 'Confirm' bole, ya cancel karne ke liye 'No' bole."
                )
            elif language == IntentParser.LANG_MR:
                return (
                    f"कृती पुष्टीकरण आवश्यक आहे: {summary}\n\n"
                    f"पुढे जाण्यासाठी 'होय' (Yes) किंवा रद्द करण्यासाठी 'नाही' (Cancel) टाईप करा."
                )

        # Standard Intent Responses
        # ------------------- English -------------------
        if language == IntentParser.LANG_EN:
            if intent in (IntentParser.INTENT_SPACE_SEARCH, "find_spaces"):
                budget_info = f" with hourly budgets under ₹{budget}" if budget else ""
                spaces_count = len(tool_data.get("spaces", [])) if tool_data else 0
                if spaces_count > 0:
                    return (
                        f"I found {spaces_count} verified physical {space_type}s matching your criteria in {loc_str}{budget_info}. "
                        f"All spaces feature high-speed WiFi, verified acoustic profiles, and keyless PIN/QR entry. "
                        f"Select a space below to review pricing breakdown and check live availability."
                    )
                return (
                    f"I can help you find verified physical {space_type}s in {loc_str}{budget_info}. "
                    f"SpaceLoop matches listings within 2km to 25km using acoustic noise levels, high-speed WiFi, "
                    f"and host trust scores. Click below to browse active spaces or refine your filters."
                )

            elif intent in (IntentParser.INTENT_BOOKING_CREATE, IntentParser.INTENT_SPACE_AVAILABILITY, "booking_reservation"):
                return (
                    f"To book a space on SpaceLoop: 1) Run an instant precheck to verify slot availability and minimum "
                    f"hours. 2) Submit your reservation. 3) Once the host accepts, you'll receive a secure 4-digit arrival "
                    f"PIN for physical access. No overlapping bookings are ever allowed for the same slot."
                )

            elif intent in (IntentParser.INTENT_BOOKING_CANCEL, IntentParser.INTENT_REFUND_HELP, "cancellation_refund"):
                return (
                    "Here is SpaceLoop's cancellation policy: When you cancel a booking, SpaceLoop retains only the "
                    "5% platform fee. You receive 100% of your rental subtotal plus 100% of the ₹100 security deposit "
                    "back to your account. If the host rejects your booking, you receive a full 100% refund."
                )

            elif intent in (IntentParser.INTENT_ACCESS_STATUS, IntentParser.INTENT_ACCESS_HELP, "checkin_checkout"):
                return (
                    "For seamless check-in: 1) Enter your 4-digit arrival PIN at the door. 2) Your phone confirms you are "
                    "within the 50-meter GPS geofence. 3) Upload quick check-in inspection photos to document space condition. "
                    "Repeat photo upload at check-out to safely release your ₹100 deposit."
                )

            elif intent in (IntentParser.INTENT_ESCROW_STATUS, "pricing_escrow"):
                return (
                    "SpaceLoop uses a transparent micro-escrow pricing model: Space Subtotal = hourly rate × duration hours. "
                    "Platform fee = 5% of subtotal. Refundable security deposit = ₹100.00. Total paid = Subtotal + 5% Fee + ₹100. "
                    "Upon normal checkout, the host receives the subtotal, SpaceLoop retains the 5% fee, and the ₹100 deposit is returned."
                )

            elif intent in (IntentParser.INTENT_HOST_HELP, "host_listing"):
                return (
                    "To list your space on SpaceLoop: Upload photos (up to 5MB with verified image headers), set your hourly "
                    "rate and capacity, and complete KYC verification. After a seeker's session completes, your payout is "
                    "released directly to your verified UPI VPA with zero listing subscription fees."
                )

            elif intent in (IntentParser.INTENT_LEGAL_INFORMATION, "legal"):
                return (
                    "All SpaceLoop reservations operate as a Leave and License under Section 52 of the Indian Easements Act, 1882. "
                    "This creates a revocable personal license to occupy the workspace for the booked hours. Crucially, "
                    "no tenancy, leasehold, or proprietary rights are created in the property."
                )

            elif intent in (IntentParser.INTENT_DISPUTE_HELP, IntentParser.INTENT_TRUST_SAFETY, "trust_safety"):
                return (
                    "SpaceLoop protects hosts and seekers with an Objective Trust Score (0-100), government KYC identity "
                    "verification, and automated escrow protection. In case of any dispute or access failure, escrow funds "
                    "are immediately frozen while administrators adjudicate."
                )

            else:  # General / Support
                return (
                    "Hello! I am LoopBot, your SpaceLoop concierge. I can help you discover workspaces, studios, "
                    "and meeting rooms, understand our 5% fee & ₹100 escrow deposit, explain check-in PINs, or guide you through listing a space."
                )

        # ------------------- Hinglish -------------------
        elif language == IntentParser.LANG_HINGLISH:
            if intent in (IntentParser.INTENT_SPACE_SEARCH, "find_spaces"):
                return (
                    f"Main aapke liye {loc_str} mein verified physical {space_type}s dhoondh sakta hoon. "
                    f"Sabhi spaces mein high-speed WiFi aur 4-digit arrival PIN access available hai. "
                    f"Neeche diye gaye options se active spaces browse karein."
                )
            elif intent in (IntentParser.INTENT_BOOKING_CANCEL, IntentParser.INTENT_REFUND_HELP, "cancellation_refund"):
                return (
                    "SpaceLoop cancellation policy ke mutabik: Agar aap booking cancel karte hain, toh SpaceLoop sirf "
                    "5% platform fee retain karta hai. Aapko rental subtotal ka 100% plus ₹100 security deposit pura wapas milta hai."
                )
            elif intent in (IntentParser.INTENT_ACCESS_STATUS, IntentParser.INTENT_ACCESS_HELP, "checkin_checkout"):
                return (
                    "Check-in karne ke liye aapko 50m GPS geofence ke andar hona hoga aur apna 4-digit arrival PIN ya "
                    "QR code use karna hoga. Saath hi inspection photos upload karke entry confirm karein."
                )
            elif intent in (IntentParser.INTENT_ESCROW_STATUS, "pricing_escrow"):
                return (
                    "SpaceLoop pricing formula: Total = Space Subtotal (hourly rate × hours) + 5% platform fee + ₹100 refundable escrow deposit. "
                    "Checkout par ₹100 deposit aapko pura refund mil jata hai."
                )
            else:
                return (
                    "Namaste! Main LoopBot hoon, aapka SpaceLoop concierge. Main spaces dhoondhne, booking precheck, "
                    "5% fee rules, aur PIN check-in mein aapki madad kar sakta hoon."
                )

        # ------------------- Hindi -------------------
        elif language == IntentParser.LANG_HI:
            if intent in (IntentParser.INTENT_BOOKING_CANCEL, IntentParser.INTENT_REFUND_HELP, "cancellation_refund"):
                return (
                    "SpaceLoop रद्दीकरण नीति: बुकिंग रद्द करने पर SpaceLoop केवल 5% प्लेटफ़ॉर्म शुल्क रखता है। "
                    "आपको 100% किराया और ₹100 सुरक्षा जमा राशि पूरी वापस मिलती है। मेज़बान द्वारा अस्वीकार किए जाने पर पूरा 100% रिफ़ंड मिलता है।"
                )
            elif intent in (IntentParser.INTENT_ESCROW_STATUS, "pricing_escrow"):
                return (
                    "SpaceLoop मूल्य निर्धारण: कुल राशि = किराया उप-योग + 5% प्लेटफ़ॉर्म शुल्क + ₹100 रिफ़ंडेबल सुरक्षा जमा। "
                    "सत्र समाप्ति पर ₹100 जमा राशि आपके खाते में वापस भेज दी जाती है।"
                )
            else:
                return (
                    "नमस्ते! मैं लूपबॉट (LoopBot) हूँ, स्पेस-लूप का सहायक। मैं कार्यक्षेत्र खोजने, बुकिंग और नियमों में आपकी सहायता कर सकता हूँ।"
                )

        # ------------------- Marathi -------------------
        else:
            if intent in (IntentParser.INTENT_BOOKING_CANCEL, IntentParser.INTENT_REFUND_HELP, "cancellation_refund"):
                return (
                    "स्पेस-लूप रद्द करण्याचे धोरण: बुकिंग रद्द केल्यास केवळ 5% प्लॅटफॉर्म शुल्क कापले जाते. "
                    "आपल्याला 100% भाडे आणि ₹100 सुरक्षा ठेव पूर्ण परत मिळते. यजमानाने नाकारल्यास 100% पूर्ण परतावा मिळतो."
                )
            elif intent in (IntentParser.INTENT_ESCROW_STATUS, "pricing_escrow"):
                return (
                    "स्पेस-लूप शुल्क नियम: एकूण रक्कम = भाडे + 5% प्लॅटफॉर्म शुल्क + ₹100 सुरक्षा ठेव. "
                    "सत्र पूर्ण झाल्यावर ₹100 सुरक्षा ठेव थेट परत केली जाते."
                )
            else:
                return (
                    "नमस्कार! मी लूपबॉट (LoopBot), स्पेस-लूपचा डिजिटल सहाय्यक. मी जागा शोधणे, बुकिंग, "
                    "5% शुल्क नियम आणि चेक-इन पिनमध्ये आपली मदत करू शकतो."
                )
