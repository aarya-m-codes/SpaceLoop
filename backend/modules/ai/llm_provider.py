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

        return (
            "You are LoopBot, SpaceLoop's native AI concierge.\n"
            "SpaceLoop is India's premier marketplace for flexible peer-to-peer workspace reservations (desks, soundproof studios, cabins, meeting rooms).\n\n"
            f"USER LANGUAGE PREFERENCE: {language.upper()}.\n\n"
            "COMMUNICATION & CONVERSATIONAL RULES:\n"
            "- Speak naturally, intelligently, and conversationally like an experienced local workspace concierge.\n"
            "- NEVER use repetitive robotic formulas like 'Based on your query, here are the spaces' or 'I can help you find verified physical spaces in your area'. Adapt your tone to each message.\n"
            "- Understand typos, broken grammar, abbreviations ('3h', '2 hrs', 'pune me room', 'sasta', 'kharadi side', 'under 700') seamlessly without calling them out.\n"
            "- Natural Multilingual Adaptation:\n"
            "  * If user speaks in English: reply in clear, friendly English.\n"
            "  * If user speaks in Hinglish (e.g. 'bhai pune me quiet place chahiye', 'sasta kuch hai?', 'kal available hai?'): reply in natural, conversational Hinglish.\n"
            "  * If user speaks in Hindi or Marathi: reply warmly and respectfully in Hindi or Marathi.\n"
            "- Multi-turn Context:\n"
            "  * Follow-up constraints ('under 700', 'tomorrow afternoon', 'around kharadi') are additions to previous requirements.\n"
            "  * Ordinal references ('the second one', '1st one') refer to the listed spaces.\n"
            "  * Questions ('which one has parking?', 'how much for 4 hours?', 'book it') apply to the current active listings.\n"
            "- Grounding: Ground all spaces, rates, hours, and amenities STRICTLY in the verified platform data below. NEVER invent spaces, fake IDs, or arbitrary prices.\n"
            "- Core Marketplace Rules:\n"
            "  1. Pricing: Subtotal = hourly rate × hours. Platform fee = exactly 5%. Refundable deposit = exactly ₹100. Total = Subtotal + 5% Fee + ₹100.\n"
            "  2. Cancellation: SpaceLoop retains ONLY 5% platform fee. Seeker receives 100% of rental subtotal + 100% of ₹100 deposit refunded.\n"
            "  3. Access: 15-minute start window, 50m GPS geofence, 4-digit arrival PIN.\n"
            "  4. Legal: Section 52 Indian Easements Act 1882 (Leave and License); no tenancy rights.\n\n"
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

        # Dynamic Tool-Grounded Responses for Deterministic Fallback
        if tool_data and "inspected_spaces" in tool_data:
            attr = tool_data.get("query_attribute", "amenity")
            matched = tool_data.get("inspected_spaces", [])
            if matched:
                names = [f"'{s.get('title')}' (₹{s.get('price_per_hour')}/hr)" for s in matched]
                if language == IntentParser.LANG_EN:
                    return f"From our active listings in {loc_str}, the following options include {attr}:\n" + "\n".join(f"• {n}" for n in names)
                elif language in (IntentParser.LANG_HI, IntentParser.LANG_HINGLISH):
                    return f"{loc_str} ke active listings mein se in spaces mein {attr} available hai:\n" + "\n".join(f"• {n}" for n in names)
                else:
                    return f"{loc_str} मधील खालील जागांवर {attr} उपलब्ध आहे:\n" + "\n".join(f"• {n}" for n in names)
            else:
                return f"Currently, none of the active listings in {loc_str} explicitly list {attr}. Would you like to check nearby areas?"

        if tool_data and "pricing" in tool_data:
            p = tool_data["pricing"]
            sp_title = tool_data.get("space", {}).get("title") or "the selected space"
            dur_h = tool_data.get("duration_hours") or duration
            if language == IntentParser.LANG_EN:
                return (
                    f"For {dur_h} hours at '{sp_title}':\n"
                    f"• Rental Subtotal: ₹{p.get('subtotal', 0):.2f}\n"
                    f"• SpaceLoop Fee (5%): ₹{p.get('platform_fee', 0):.2f}\n"
                    f"• Refundable Security Deposit: ₹{p.get('escrow_deposit', 100):.2f}\n"
                    f"• Total Payable: ₹{p.get('final_amount', 0):.2f}\n\n"
                    f"The ₹100 escrow deposit is refunded to your account upon checkout."
                )
            elif language in (IntentParser.LANG_HI, IntentParser.LANG_HINGLISH):
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
            if language == IntentParser.LANG_EN:
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

        # Standard Intent Responses
        # ------------------- English -------------------
        if language == IntentParser.LANG_EN:
            if intent in (IntentParser.INTENT_SPACE_SEARCH, "find_spaces"):
                budget_info = f" with hourly budgets under ₹{budget}" if budget else ""
                spaces = tool_data.get("spaces", []) if tool_data else []
                spaces_count = len(spaces)
                if spaces_count > 0:
                    summary_lines = [
                        f"{i}. '{s.get('title')}' (₹{s.get('price_per_hour')}/hr, {s.get('neighborhood') or s.get('city')})"
                        for i, s in enumerate(spaces[:3], 1)
                    ]
                    return (
                        f"I found {spaces_count} verified physical {space_type}s matching your criteria in {loc_str}{budget_info}:\n"
                        + "\n".join(summary_lines)
                        + "\n\nAll spaces feature high-speed WiFi, verified acoustic profiles, and keyless PIN/QR entry. Let me know if you would like to book or inspect one."
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
