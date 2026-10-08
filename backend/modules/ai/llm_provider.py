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
from backend.modules.i18n.constants import normalize_language_code
from backend.modules.i18n.lexicon import get_deterministic_response

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
        """Construct authoritative grounded prompt enforcing SpaceLoop invariants and tool grounding."""
        context_block = RAGService.build_llm_context(sources)

        # Build clean, high-fidelity tool grounding context
        tool_lines = []
        if tool_data:
            if "spaces" in tool_data and tool_data["spaces"]:
                tool_lines.append("CURRENT ACTIVE SPACELOOP LISTINGS IN DATABASE:")
                for i, sp in enumerate(tool_data["spaces"], 1):
                    loc = f"{sp.get('neighborhood')}, {sp.get('city')}" if sp.get('neighborhood') else sp.get('city', '')
                    amenities_str = ", ".join(sp.get("amenities", []) or [])
                    tool_lines.append(
                        f"  Listing #{i} (ID: {sp.get('id')}): '{sp.get('title')}' in {loc} | "
                        f"Price: ₹{sp.get('price_per_hour')}/hr | Capacity: {sp.get('capacity', 1)} | "
                        f"Amenities: [{amenities_str}] | Acoustic Level: {sp.get('ai_noise_level', 'quiet')}"
                    )
            elif "inspected_spaces" in tool_data:
                attr = tool_data.get("query_attribute", "amenities")
                matches = tool_data.get("inspected_spaces", [])
                if matches:
                    tool_lines.append(f"CURRENT LISTINGS OFFERING '{attr.upper()}':")
                    for sp in matches:
                        tool_lines.append(f"  - '{sp.get('title')}' (ID: {sp.get('id')}) offers {', '.join(sp.get('amenities', []))} (₹{sp.get('price_per_hour')}/hr)")
                else:
                    tool_lines.append(f"No current listings offer '{attr}'.")
            elif "pricing" in tool_data and tool_data["pricing"]:
                p = tool_data["pricing"]
                sp_info = tool_data.get("space", {})
                sp_title = sp_info.get("title") or f"Space #{sp_info.get('id')}"
                tool_lines.append(
                    f"AUTHORITATIVE PRICING QUOTE FOR '{sp_title}':\n"
                    f"  - Duration: {tool_data.get('duration_hours', 2)} hours\n"
                    f"  - Rental Subtotal: ₹{p.get('subtotal', 0):.2f}\n"
                    f"  - Platform Fee (5%): ₹{p.get('platform_fee', 0):.2f}\n"
                    f"  - Refundable Security Deposit: ₹{p.get('escrow_deposit', 100):.2f}\n"
                    f"  - Total Payable: ₹{p.get('final_amount', 0):.2f}\n"
                    f"  - Slot Available: {tool_data.get('available', True)}"
                )
            elif "booking" in tool_data:
                b = tool_data["booking"]
                tool_lines.append(
                    f"CONFIRMED BOOKING RECORD:\n"
                    f"  - Booking ID: #{b.get('id')}\n"
                    f"  - Status: {b.get('status')}\n"
                    f"  - Arrival 4-Digit PIN: {b.get('arrival_pin')}\n"
                    f"  - Check-in Guard: 50m GPS geofence + 15m window"
                )
            elif "confirmation_required" == tool_data.get("type"):
                tool_lines.append(f"PENDING USER CONFIRMATION:\n  {tool_data.get('action_summary')}")
            else:
                tool_lines.append(f"Platform Data: {tool_data}")

        tool_context = "\n".join(tool_lines) if tool_lines else "No specific tool data queried."
        pending_context = f"Pending Confirmation Action: {pending_action.get('action_summary')}" if pending_action else ""

        lang_code = normalize_language_code(language)
        lang_instruction = {
            "en": "You MUST respond in professional, helpful English.",
            "hi": "You MUST respond in standard Hindi (हिन्दी) using Devanagari script.",
            "mr": "You MUST respond in authentic Marathi (मराठी) using Devanagari script.",
            "gsw": "You MUST respond in authentic Garhwali (गढ़वळि) using Devanagari script with natural regional Pahari idioms (e.g. ठौर, सुभीता, बगत, पैलाग/प्रणाम).",
            "kfy": "You MUST respond in authentic Kumaoni (कुमाउँनी) using Devanagari script with natural regional Pahari idioms (e.g. ठौर, सुभीत, बखत, पैलाग).",
            "jns": "You MUST respond in authentic Jaunsari (जौनसारी) using Devanagari script with natural regional Pahari idioms (e.g. ठौर, सुआणो, ओखत, नमस्ते/प्रणाम).",
        }.get(lang_code, "You MUST respond in professional English.")

        return (
            "You are LoopBot, SpaceLoop's native AI concierge.\n"
            "SpaceLoop is India's premier marketplace for flexible peer-to-peer workspace reservations (desks, soundproof studios, cabins, meeting rooms).\n\n"
            f"TARGET LANGUAGE: {lang_code.upper()}.\n"
            f"{lang_instruction}\n\n"
            "COMMUNICATION & CONVERSATIONAL RULES:\n"
            "- Speak naturally, intelligently, and conversationally like an experienced local workspace concierge.\n"
            "- NEVER use repetitive robotic formulas like 'Based on your query, here are the spaces' or 'I can help you find verified physical spaces in your area'. Adapt your tone to each message.\n"
            "- Understand typos, broken grammar, abbreviations ('3h', '2 hrs', 'pune me room', 'sasta', 'kharadi side', 'under 700') seamlessly without calling them out.\n"
            "- Natural Multilingual Adaptation:\n"
            "  * If user speaks in English: reply in clear, friendly English.\n"
            "  * If user speaks in Hinglish: reply in natural, conversational Hinglish.\n"
            "  * If user speaks in Hindi, Marathi, Garhwali, Kumaoni, or Jaunsari: reply warmly and respectfully in that language.\n"
            "- Multi-turn Context:\n"
            "  * Follow-up constraints ('under 700', 'tomorrow afternoon', 'around kharadi') are additions to previous requirements.\n"
            "  * Ordinal references ('the second one', '1st one') refer to the listed spaces.\n"
            "  * Questions ('which one has parking?', 'how much for 4 hours?', 'book it') apply to the current active listings.\n"
            "- Grounding: Ground all spaces, rates, hours, and amenities STRICTLY in the verified platform data below. NEVER invent spaces, fake IDs, or arbitrary prices.\n"
            "- Core Marketplace Rules & Invariants:\n"
            "  1. Pricing: Subtotal = hourly rate × hours. Platform fee = exactly 5%. Refundable deposit = exactly ₹100. Total = Subtotal + 5% Fee + ₹100.\n"
            "  2. Cancellation: SpaceLoop retains ONLY 5% platform fee. Seeker receives 100% of rental subtotal + 100% of ₹100 deposit refunded. On host rejection, seeker gets full 100% refund of all fees.\n"
            "  3. Access: 15-minute start window, 50m GPS geofence (Haversine), 4-digit arrival PIN fallback, dynamic QR code, and AccessLog.\n"
            "  4. Legal: Section 52 Indian Easements Act 1882 (Leave and License); no tenancy or leasehold rights are created.\n"
            "  5. Invariants: You NEVER execute unauthorized financial or booking mutations. Every consequential action requires explicit confirmation.\n\n"
            f"{context_block}\n\n"
            f"{tool_context}\n\n"
            f"{pending_context}"
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
        """Execute inference using Groq with candidate model fallback."""
        import groq
        client = groq.Groq(api_key=api_key, timeout=12.0)

        sys_prompt = cls._build_system_prompt(intent, sources, language, tool_data, pending_action)
        messages = [{"role": "system", "content": sys_prompt}]

        for turn in conversation_history[-8:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        candidate_models = [
            os.getenv("GROQ_MODEL"),
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ]
        seen = set()
        models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

        for model_name in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=600,
                )
                if completion and completion.choices and completion.choices[0].message.content:
                    return completion.choices[0].message.content.strip()
            except Exception as exc:
                logger.debug(f"Groq model {model_name} invocation failed: {exc}. Trying next candidate.")
                continue

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
        history_str = ""
        for turn in conversation_history[-6:]:
            history_str += f"{turn.get('role', 'user').title()}: {turn.get('content', '')}\n"

        full_prompt = (
            f"{sys_prompt}\n\n"
            f"CONVERSATION HISTORY:\n{history_str}\n"
            f"User Message: {user_message}\n\n"
            "LoopBot Concierge Response:"
        )

        candidate_models = [
            os.getenv("GEMINI_MODEL"),
            "gemini-2.5-flash",
            "gemini-1.5-flash",
        ]
        seen = set()
        models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as exc:
                logger.debug(f"Gemini model {model_name} failed: {exc}. Trying next candidate.")
                continue

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
        """Produce authoritative deterministic responses with 100% resilience across all 6 supported languages."""
        clean_lang = str(language or "").strip().lower()
        if clean_lang == "hinglish":
            lang_code = "hinglish"
        else:
            lang_code = normalize_language_code(language)
        city = entities.get("city") or "your area"
        neighborhood = entities.get("neighborhood")
        loc_str = f"{neighborhood.title()}, {city.title()}" if neighborhood else city.title()
        space_type = entities.get("space_type") or "space"
        budget = entities.get("budget")
        budget_info = f" under ₹{budget:g}/hr" if budget else ""

        # If there is a pending confirmation action, explain it clearly in the target language
        if pending_action:
            act_type = pending_action.get("action")
            summary = pending_action.get("action_summary", "")
            if lang_code == "en":
                return (
                    f"Action Confirmation Required: {summary}\n\n"
                    f"Please confirm by replying 'Yes' or 'Confirm' to proceed, or 'Cancel' to abort."
                )
            elif lang_code == "hinglish":
                return (
                    f"Action Confirmation Required: {summary}\n\n"
                    f"Aage badhne ke liye 'Yes' ya cancel karne ke liye 'Cancel' type karein."
                )
            elif lang_code == "mr":
                return (
                    f"कृती पुष्टीकरण आवश्यक आहे: {summary}\n\n"
                    f"पुढे जाण्यासाठी 'होय' (Yes) किंवा रद्द करण्यासाठी 'नाही' (Cancel) टाईप करा."
                )
            elif lang_code == "gsw":
                return (
                    f"पुष्टीकरण जरूरी छ: {summary}\n\n"
                    f"आगे बढण खातिर 'ह्वै' (Yes) या रद्द कर्न खातिर 'ना' (Cancel) लिखा।"
                )
            elif lang_code == "kfy":
                return (
                    f"पुष्टीकरण जरूरी छु: {summary}\n\n"
                    f"आगै बढ़ण खातिर 'हो' (Yes) या रद्द कर्न खातिर 'ना' (Cancel) लिखा।"
                )
            elif lang_code == "jns":
                return (
                    f"पुष्टीकरण जरूरी आ: {summary}\n\n"
                    f"आगे बढ़ण खातिर 'हाँ' (Yes) या रद्द कर्न खातिर 'नाइ' (Cancel) लिखा।"
                )
            else:  # Hindi
                return (
                    f"कार्रवाई की पुष्टि आवश्यक है: {summary}\n\n"
                    f"आगे बढ़ने के लिए 'हाँ' (Yes) या रद्द करने के लिए 'नहीं' (Cancel) लिखें।"
                )

        # Dynamic Tool-Grounded Responses for Deterministic Fallback
        if tool_data and "inspected_spaces" in tool_data:
            attr = tool_data.get("query_attribute", "amenity")
            matched = tool_data.get("inspected_spaces", [])
            if matched:
                names = [f"'{s.get('title')}' (₹{s.get('price_per_hour')}/hr)" for s in matched]
                if lang_code == "en":
                    return f"From our active listings in {loc_str}, the following options include {attr}:\n" + "\n".join(f"• {n}" for n in names)
                elif lang_code in ("hi", "hinglish"):
                    return f"{loc_str} ke active listings mein se in spaces mein {attr} available hai:\n" + "\n".join(f"• {n}" for n in names)
                else:
                    return f"{loc_str} मधील खालील जागांवर {attr} उपलब्ध आहे:\n" + "\n".join(f"• {n}" for n in names)
            else:
                return f"Currently, none of the active listings in {loc_str} explicitly list {attr}. Would you like to check nearby areas?"

        if tool_data and "pricing" in tool_data:
            p = tool_data["pricing"]
            sp_title = tool_data.get("space", {}).get("title") or "the selected space"
            dur_h = tool_data.get("duration_hours") or duration
            if lang_code == "en":
                return (
                    f"For {dur_h} hours at '{sp_title}':\n"
                    f"• Rental Subtotal: ₹{p.get('subtotal', 0):.2f}\n"
                    f"• SpaceLoop Fee (5%): ₹{p.get('platform_fee', 0):.2f}\n"
                    f"• Refundable Security Deposit: ₹{p.get('escrow_deposit', 100):.2f}\n"
                    f"• Total Payable: ₹{p.get('final_amount', 0):.2f}\n\n"
                    f"The ₹100 escrow deposit is refunded to your account upon checkout."
                )
            elif lang_code in ("hi", "hinglish"):
                return (
                    f"'{sp_title}' ke {dur_h} ghante ke liye:\n"
                    f"• Rental Subtotal: ₹{p.get('subtotal', 0):.2f}\n"
                    f"• Platform Fee (5%): ₹{p.get('platform_fee', 0):.2f}\n"
                    f"• Refundable Deposit: ₹{p.get('escrow_deposit', 100):.2f}\n"
                    f"• Total Amount: ₹{p.get('final_amount', 0):.2f}\n\n"
                    f"Checkout ke baad ₹100 deposit aapko pura refund mil jata hai."
                )
            else:
                return (
                    f"'{sp_title}' साठी {dur_h} तासांचे भाडे:\n"
                    f"• एकूण भाडे: ₹{p.get('subtotal', 0):.2f}\n"
                    f"• प्लॅटफॉर्म शुल्क (5%): ₹{p.get('platform_fee', 0):.2f}\n"
                    f"• सुरक्षा ठेव: ₹{p.get('escrow_deposit', 100):.2f}\n"
                    f"• देय रक्कम: ₹{p.get('final_amount', 0):.2f}"
                )

        if tool_data and intent in (IntentParser.INTENT_SPACE_DETAILS, "find_spaces") and "space" in tool_data:
            sp = tool_data["space"]
            amenities_str = ", ".join(sp.get("amenities", []) or [])
            if lang_code == "en":
                return (
                    f"Here are the verified details for '{sp.get('title')}':\n"
                    f"• Location: {sp.get('neighborhood') or sp.get('city')}, {sp.get('city')}\n"
                    f"• Hourly Rate: ₹{sp.get('price_per_hour')}/hr (Day rate: ₹{sp.get('price_per_day', 0)}/day)\n"
                    f"• Capacity: {sp.get('capacity', 1)} people\n"
                    f"• Amenities: {amenities_str}\n"
                    f"• Access: Keyless 4-digit PIN + 50m GPS geofence\n"
                    f"Would you like me to check slot availability or book this space?"
                )
            else:
                return (
                    f"'{sp.get('title')}' ki verified details:\n"
                    f"• Location: {sp.get('neighborhood') or sp.get('city')}, {sp.get('city')}\n"
                    f"• Rate: ₹{sp.get('price_per_hour')}/hr\n"
                    f"• Capacity: {sp.get('capacity', 1)} log\n"
                    f"• Amenities: {amenities_str}\n"
                    f"Kya aap is space ko book karna chahte hain?"
                )

        # Map intent code to standard lexicon key
        if intent in (IntentParser.INTENT_SPACE_SEARCH, "find_spaces"):
            intent_key = "search"
        elif intent in (IntentParser.INTENT_BOOKING_CREATE, IntentParser.INTENT_SPACE_AVAILABILITY, "booking_reservation"):
            intent_key = "booking"
        elif intent in (IntentParser.INTENT_BOOKING_CANCEL, IntentParser.INTENT_REFUND_HELP, "cancellation_refund"):
            intent_key = "cancellation"
        elif intent in (IntentParser.INTENT_ACCESS_STATUS, IntentParser.INTENT_ACCESS_HELP, "checkin_checkout"):
            intent_key = "access"
        elif intent in (IntentParser.INTENT_ESCROW_STATUS, "pricing_escrow"):
            intent_key = "escrow"
        elif intent in (IntentParser.INTENT_HOST_HELP, "host_listing"):
            intent_key = "host"
        elif intent in (IntentParser.INTENT_LEGAL_INFORMATION, "legal"):
            intent_key = "legal"
        elif intent in (IntentParser.INTENT_DISPUTE_HELP, IntentParser.INTENT_TRUST_SAFETY, "trust_safety"):
            intent_key = "trust"
        else:
            intent_key = "welcome"

        return get_deterministic_response(
            intent=intent_key,
            language=lang_code,
            context_vars={
                "loc_str": loc_str,
                "budget_info": budget_info,
                "space_type": space_type,
            },
        )
