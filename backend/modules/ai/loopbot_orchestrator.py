"""SpaceLoop LoopBot Orchestrator & Conversational Concierge Subsystem.

Coordinates the complete 8-stage LoopBot processing pipeline:
1. Receive user message & load multi-turn session context.
2. Detect language (English, Hindi, Hinglish, Marathi).
3. Normalize text & evaluate confirmation state machine.
4. Classify intent across the 18 marketplace categories.
5. Extract structured entities and accumulate context across turns.
6. Execute controlled SpaceLoop domain tools with authorization gates.
7. Retrieve authoritative knowledge via the 7-domain in-process RAG.
8. Generate grounded commentary via primary Groq -> fallback Gemini -> deterministic engine.
9. Return structured response contract with actionable payload cards.

CRITICAL INVARIANTS:
- SpaceLoop backend is always the single source of truth.
- LoopBot NEVER invents prices, policies, or booking numbers.
- Consequential mutations (booking creation, cancellation) MUST require explicit user confirmation.
- An isolated "yes" without a pending confirmation action NEVER mutates state.
"""

import logging
import os
import secrets
from typing import Any

from backend.modules.ai.context_manager import ConversationManager
from backend.modules.ai.intent_parser import IntentParser
from backend.modules.ai.llm_provider import LLMProvider
from backend.modules.ai.rag_service import RAGService
from backend.modules.ai.tools import LoopBotTools
from models import User

logger = logging.getLogger("spaceloop.ai.loopbot")


class LoopBotOrchestrator:
    """Enterprise-grade conversational concierge orchestrator for SpaceLoop."""

    # Language constants
    LANG_EN = IntentParser.LANG_EN
    LANG_HI = IntentParser.LANG_HI
    LANG_HINGLISH = IntentParser.LANG_HINGLISH
    LANG_MR = IntentParser.LANG_MR

    # Legacy intent constants for backwards compatibility
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
        raw_msg = (message or "").strip()

        # 1. Retrieve or create multi-turn conversation session
        conv_id, session = ConversationManager.get_or_create_session(conversation_id)

        if not raw_msg:
            return cls._empty_message_response(conv_id, language or session.get("language", "en"))

        # 2. Detect language
        detected_lang = language or cls.detect_language(raw_msg)
        session["language"] = detected_lang

        # 3. Normalize text
        normalized_text = cls.normalize_text(raw_msg)

        # 4. Check for Pending Consequential Confirmation
        pending_action = ConversationManager.get_pending_action(conv_id)
        is_confirmation, decision = IntentParser.detect_confirmation(raw_msg)

        if pending_action and is_confirmation:
            return cls._handle_pending_confirmation(
                conv_id=conv_id,
                session=session,
                decision=decision,
                pending_action=pending_action,
                detected_lang=detected_lang,
                current_user=user,
            )

        # 5. Extract structured entities & merge with accumulated context
        accumulated = session.get("accumulated_entities", {})
        extracted_entities = cls.extract_entities(normalized_text, accumulated)
        ConversationManager.update_entities(conv_id, extracted_entities)

        # 6. Intent Classification (18 Standard Categories & Legacy Map)
        standard_intent, legacy_intent = IntentParser.classify_intent(normalized_text, session)
        session["last_intent"] = legacy_intent

        # 7. Execute Controlled Tools Based on Intent
        tool_data, response_type = cls._execute_tool_pipeline(
            standard_intent=standard_intent,
            legacy_intent=legacy_intent,
            entities=extracted_entities,
            conv_id=conv_id,
            current_user=user,
            raw_msg=raw_msg,
        )

        # 8. Retrieve Relevant Authoritative Knowledge via RAG (threshold >= 0.45)
        rag_domain = cls.INTENT_DOMAIN_MAP.get(legacy_intent, "spaces_search")
        sources = RAGService.search_knowledge(
            query=normalized_text,
            domain=rag_domain,
            top_k=3,
            language=detected_lang,
            threshold=0.45,
        )

        # If RAG found no sources above threshold for a non-tool general query, provide fallback
        if not sources and not tool_data:
            sources = RAGService.search_knowledge(query="", top_k=1)

        # 9. Generate Commentary via Provider Cascade (Groq -> Gemini -> Deterministic)
        pending_now = ConversationManager.get_pending_action(conv_id)
        response_text, provider_used = cls.generate_response(
            message=raw_msg,
            normalized=normalized_text,
            intent=legacy_intent,
            entities=extracted_entities,
            sources=sources,
            language=detected_lang,
            session=session,
            tool_data=tool_data,
            pending_action=pending_now,
        )

        # 10. Generate Suggested Action Chips
        suggested_actions = cls.generate_suggested_actions(
            intent=legacy_intent,
            standard_intent=standard_intent,
            entities=extracted_entities,
            language=detected_lang,
            tool_data=tool_data,
            response_type=response_type,
        )

        # Update multi-turn session history
        ConversationManager.append_message(
            conversation_id=conv_id,
            role="user",
            content=raw_msg,
            entities=extracted_entities,
            intent=legacy_intent,
        )
        ConversationManager.append_message(
            conversation_id=conv_id,
            role="assistant",
            content=response_text,
        )

        # SpaceLoop Comprehensive Response Contract
        return {
            "response": response_text,
            "message": response_text,
            "reply": response_text,
            "type": response_type,
            "intent": legacy_intent,
            "standard_intent": standard_intent,
            "data": tool_data or {},
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
            "language": detected_lang,
            "provider": provider_used,
            "context": extracted_entities,
        }

    # =========================================================================
    # Consequential Action State Machine
    # =========================================================================
    @classmethod
    def _handle_pending_confirmation(
        cls,
        conv_id: str,
        session: dict[str, Any],
        decision: str | None,
        pending_action: dict[str, Any],
        detected_lang: str,
        current_user: Any,
    ) -> dict[str, Any]:
        """Execute or discard pending consequential mutation based on affirmative/negative response."""
        act_type = pending_action.get("action")
        payload = pending_action.get("payload", {})

        if decision == "yes":
            # Explicit confirmation granted!
            ConversationManager.clear_pending_action(conv_id)

            if act_type == "create_booking":
                res = LoopBotTools.create_booking(
                    space_id=payload.get("space_id"),
                    current_user=current_user,
                    start_time_iso=payload.get("start_time"),
                    end_time_iso=payload.get("end_time"),
                    guest_count=payload.get("guest_count", 1),
                    confirmed=True,
                )
                msg = res.get("message") or (
                    f"Booking #{res.get('booking', {}).get('id')} confirmed! "
                    f"Your arrival PIN is {res.get('booking', {}).get('arrival_pin')}."
                    if res.get("success") else res.get("error", "Failed to complete booking.")
                )
                return {
                    "response": msg,
                    "message": msg,
                    "reply": msg,
                    "type": "booking_status",
                    "intent": cls.INTENT_BOOKING,
                    "standard_intent": IntentParser.INTENT_BOOKING_CREATE,
                    "data": res,
                    "sources": [],
                    "suggested_actions": [
                        {"type": "my_bookings", "label": "View My Bookings", "payload": {}},
                        {"type": "checkin_guide", "label": "Arrival PIN Guide", "payload": {}},
                    ],
                    "conversation_id": conv_id,
                    "language": detected_lang,
                    "provider": "deterministic",
                    "context": session.get("accumulated_entities", {}),
                }

            elif act_type == "cancel_booking":
                res = LoopBotTools.cancel_booking(
                    booking_id=payload.get("booking_id"),
                    current_user=current_user,
                    reason=payload.get("reason"),
                    confirmed=True,
                )
                msg = res.get("message") or (
                    f"Booking #{payload.get('booking_id')} cancelled. Refund processed with 5% platform fee retained."
                    if res.get("success") else res.get("error", "Failed to cancel booking.")
                )
                return {
                    "response": msg,
                    "message": msg,
                    "reply": msg,
                    "type": "booking_status",
                    "intent": cls.INTENT_CANCELLATION,
                    "standard_intent": IntentParser.INTENT_BOOKING_CANCEL,
                    "data": res,
                    "sources": [],
                    "suggested_actions": [
                        {"type": "my_bookings", "label": "View Bookings", "payload": {}},
                        {"type": "search_spaces", "label": "Explore Other Spaces", "payload": {}},
                    ],
                    "conversation_id": conv_id,
                    "language": detected_lang,
                    "provider": "deterministic",
                    "context": session.get("accumulated_entities", {}),
                }

        # User said "no", "cancel", "stop", or "nevermind"
        ConversationManager.clear_pending_action(conv_id)
        cancel_msg = (
            "Understood! The pending action has been cancelled. No changes were made to your account or reservations."
            if detected_lang == cls.LANG_EN else
            "Theek hai! Action cancel kar diya gaya hai. Aapke account ya booking mein koi badlaav nahi hua."
        )
        return {
            "response": cancel_msg,
            "message": cancel_msg,
            "reply": cancel_msg,
            "type": "message",
            "intent": cls.INTENT_PLATFORM_HELP,
            "standard_intent": IntentParser.INTENT_GENERAL,
            "data": {"cancelled_action": act_type},
            "sources": [],
            "suggested_actions": [
                {"type": "search_spaces", "label": "Explore Spaces", "payload": {}},
                {"type": "my_bookings", "label": "My Bookings", "payload": {}},
            ],
            "conversation_id": conv_id,
            "language": detected_lang,
            "provider": "deterministic",
            "context": session.get("accumulated_entities", {}),
        }

    # =========================================================================
    # Controlled Tool Execution Pipeline
    # =========================================================================
    @classmethod
    def _execute_tool_pipeline(
        cls,
        standard_intent: str,
        legacy_intent: str,
        entities: dict[str, Any],
        conv_id: str,
        current_user: Any,
        raw_msg: str,
    ) -> tuple[dict[str, Any] | None, str]:
        """Execute corresponding SpaceLoop domain tool and determine response type."""
        # 1. Search Spaces
        if standard_intent == IntentParser.INTENT_SPACE_SEARCH:
            loc_part = entities.get("neighborhood") or entities.get("city") or ""
            typ_part = entities.get("space_type") or "workspace"
            # If the user query is a short constraint refinement, construct rich query
            if loc_part and len(raw_msg.split()) <= 4:
                search_q = f"quiet {typ_part} in {loc_part}"
            else:
                search_q = raw_msg

            tool_res = LoopBotTools.search_spaces(
                query=search_q,
                city=entities.get("city"),
                neighborhood=entities.get("neighborhood"),
                budget=entities.get("budget"),
                space_type=entities.get("space_type"),
                duration_hours=entities.get("duration_hours"),
                capacity=entities.get("capacity"),
                limit=4,
            )
            if tool_res and tool_res.get("spaces"):
                ConversationManager.set_search_results(conv_id, tool_res["spaces"])
            return tool_res, "space_results"

        # 2. Specific Space Details & Listing Inspection (e.g. "which one has parking?", "the second one")
        elif standard_intent == IntentParser.INTENT_SPACE_DETAILS:
            lower_msg = raw_msg.lower()
            recent_spaces = ConversationManager.get_search_results(conv_id)

            # Check if user is asking about an amenity on current search results (e.g. parking, wifi, ac)
            amenity_keywords = ["parking", "valet", "wifi", "soundproof", "quiet", "ac", "coffee", "display"]
            matched_amenity = next((am for am in amenity_keywords if am in lower_msg), None)
            if recent_spaces and matched_amenity:
                matching_spaces = [
                    s for s in recent_spaces
                    if any(matched_amenity in str(a).lower() for a in s.get("amenities", []))
                    or (matched_amenity == "soundproof" and s.get("ai_noise_level") == "soundproof")
                    or (matched_amenity == "quiet" and s.get("ai_noise_level") in ("quiet", "soundproof"))
                ]
                tool_res = {
                    "success": True,
                    "inspected_spaces": matching_spaces,
                    "query_attribute": matched_amenity,
                    "spaces": matching_spaces if matching_spaces else recent_spaces,
                    "count": len(matching_spaces),
                }
                return tool_res, "space_results"

            # Check if user is referencing an ordinal space ("the second one", "first one", "last one")
            resolved = ConversationManager.resolve_space_reference(conv_id, raw_msg)
            if resolved:
                ConversationManager.set_selected_space(conv_id, resolved)
                entities["selected_space_id"] = resolved.get("id")
                tool_res = {
                    "success": True,
                    "space": resolved,
                    "spaces": [resolved],
                    "count": 1,
                }
                return tool_res, "space_details"

            space_id = entities.get("selected_space_id")
            if not space_id:
                sel = ConversationManager.get_selected_space(conv_id)
                if sel:
                    space_id = sel.get("id")

            if space_id:
                tool_res = LoopBotTools.get_space(space_id)
                return tool_res, "space_details"

        # 3. Space Availability / Precheck / Pricing Quote (e.g. "how much for 4 hours?")
        elif standard_intent == IntentParser.INTENT_SPACE_AVAILABILITY:
            target_space = ConversationManager.resolve_space_reference(conv_id, raw_msg) or ConversationManager.get_selected_space(conv_id)
            if not target_space:
                recent_spaces = ConversationManager.get_search_results(conv_id)
                if recent_spaces:
                    target_space = recent_spaces[0]

            space_id = (target_space or {}).get("id") or entities.get("selected_space_id")
            if space_id:
                dur = entities.get("duration_hours") or 2.0
                tool_res = LoopBotTools.check_availability(
                    space_id=space_id,
                    duration_hours=dur,
                    guest_count=entities.get("capacity") or 1,
                )
                return tool_res, "booking_preview"

        # 4. Booking Creation (Consequential - Sets Confirmation Gate)
        elif standard_intent == IntentParser.INTENT_BOOKING_CREATE:
            target_space = ConversationManager.resolve_space_reference(conv_id, raw_msg) or ConversationManager.get_selected_space(conv_id)
            if not target_space:
                recent_spaces = ConversationManager.get_search_results(conv_id)
                if recent_spaces:
                    target_space = recent_spaces[0]

            space_id = (target_space or {}).get("id") or entities.get("selected_space_id")
            if space_id:
                dur = entities.get("duration_hours") or 2.0
                # If guest user is not logged in, provide booking preview card
                if not current_user:
                    tool_res = LoopBotTools.check_availability(
                        space_id=space_id,
                        duration_hours=dur,
                        guest_count=entities.get("capacity") or 1,
                    )
                    return tool_res, "booking_preview"

                tool_res = LoopBotTools.create_booking(
                    space_id=space_id,
                    current_user=current_user,
                    duration_hours=dur,
                    guest_count=entities.get("capacity") or 1,
                    confirmed=False,
                )
                if tool_res.get("type") == "confirmation_required":
                    ConversationManager.set_pending_action(conv_id, tool_res)
                    return tool_res, "confirmation_required"
                return tool_res, "booking_preview"

        # 5. Booking Cancellation (Consequential - Sets Confirmation Gate)
        elif standard_intent == IntentParser.INTENT_BOOKING_CANCEL:
            booking_id = entities.get("selected_booking_id")
            if booking_id and current_user:
                tool_res = LoopBotTools.cancel_booking(
                    booking_id=booking_id,
                    current_user=current_user,
                    confirmed=False,
                )
                if tool_res.get("type") == "confirmation_required":
                    ConversationManager.set_pending_action(conv_id, tool_res)
                    return tool_res, "confirmation_required"
                return tool_res, "booking_preview"

        # 6. Booking Status
        elif standard_intent == IntentParser.INTENT_BOOKING_STATUS:
            booking_id = entities.get("selected_booking_id")
            if booking_id and current_user:
                tool_res = LoopBotTools.get_booking(booking_id, current_user)
                return tool_res, "booking_status"

        # 7. Access Status
        elif standard_intent in (IntentParser.INTENT_ACCESS_STATUS, IntentParser.INTENT_ACCESS_HELP):
            booking_id = entities.get("selected_booking_id")
            if booking_id and current_user:
                tool_res = LoopBotTools.get_access_status(
                    booking_id=booking_id,
                    current_user=current_user,
                    lat=entities.get("latitude"),
                    lng=entities.get("longitude"),
                )
                return tool_res, "access_status"

        # 8. Escrow Status
        elif standard_intent in (IntentParser.INTENT_ESCROW_STATUS, IntentParser.INTENT_REFUND_HELP):
            booking_id = entities.get("selected_booking_id")
            if booking_id and current_user:
                tool_res = LoopBotTools.get_escrow_status(booking_id, current_user)
                return tool_res, "escrow_status"

        # 9. Trust & Safety Status
        elif standard_intent == IntentParser.INTENT_TRUST_SAFETY:
            if entities.get("selected_space_id"):
                tool_res = LoopBotTools.get_trust_status("SPACE", entities["selected_space_id"], current_user)
                return tool_res, "message"
            elif current_user:
                tool_res = LoopBotTools.get_trust_status("USER", current_user.id, current_user)
                return tool_res, "message"

        # 10. Support Request
        elif standard_intent == IntentParser.INTENT_SUPPORT:
            tool_res = LoopBotTools.create_support_request(
                subject=raw_msg[:60],
                message=raw_msg,
                current_user=current_user,
                booking_id=entities.get("selected_booking_id"),
            )
            return tool_res, "support"

        return None, "message"

    # =========================================================================
    # Delegates for Language, Text, and Entity Processing
    # =========================================================================
    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect language across English, Hindi, Hinglish, and Marathi."""
        return IntentParser.detect_language(text)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Unicode and clean whitespace."""
        return IntentParser.normalize_text(text)

    @classmethod
    def detect_intent(cls, text: str, language: str, session: dict[str, Any]) -> str:
        """Classify message intent into one of the 7 core domains or platform help."""
        _, legacy = IntentParser.classify_intent(text, session)
        return legacy

    @classmethod
    def extract_entities(cls, text: str, context_entities: dict[str, Any]) -> dict[str, Any]:
        """Extract structured marketplace entities, merging with conversation context."""
        return IntentParser.extract_entities(text, context_entities)

    # =========================================================================
    # Suggested Actions Generator
    # =========================================================================
    @classmethod
    def generate_suggested_actions(
        cls,
        intent: str,
        standard_intent: str,
        entities: dict[str, Any],
        language: str,
        tool_data: dict[str, Any] | None = None,
        response_type: str = "message",
    ) -> list[dict[str, Any]]:
        """Return contextually appropriate actionable quick-buttons for the frontend UI."""
        city = entities.get("city")
        neighborhood = entities.get("neighborhood")
        actions: list[dict[str, Any]] = []

        # If confirmation is required, provide explicit Yes / Cancel actions
        if response_type == "confirmation_required":
            actions.append({
                "type": "confirm_action",
                "label": "Yes, Confirm Action",
                "payload": {"confirm": True},
            })
            actions.append({
                "type": "cancel_action",
                "label": "No, Cancel",
                "payload": {"confirm": False},
            })
            return actions

        if intent in (cls.INTENT_FIND_SPACES, IntentParser.INTENT_SPACE_SEARCH):
            loc_label = neighborhood.title() if neighborhood else (city.title() if city else "Area")
            actions.append({
                "type": "search_spaces",
                "label": f"Browse Spaces in {loc_label}",
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

        elif intent in (cls.INTENT_BOOKING, IntentParser.INTENT_BOOKING_CREATE, IntentParser.INTENT_SPACE_AVAILABILITY):
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

        elif intent in (cls.INTENT_CANCELLATION, IntentParser.INTENT_BOOKING_CANCEL, IntentParser.INTENT_REFUND_HELP):
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

        elif intent in (cls.INTENT_CHECKIN_CHECKOUT, IntentParser.INTENT_ACCESS_STATUS, IntentParser.INTENT_ACCESS_HELP):
            actions.append({
                "type": "checkin_guide",
                "label": "Arrival PIN & GPS Check-in Guide",
                "payload": {"geofence_meters": 50},
            })
            if entities.get("selected_booking_id"):
                actions.append({
                    "type": "view_pin",
                    "label": f"View PIN for Booking #{entities['selected_booking_id']}",
                    "payload": {"booking_id": entities["selected_booking_id"]},
                })

        elif intent in (cls.INTENT_HOST_LISTING, IntentParser.INTENT_HOST_HELP):
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

        elif intent in (cls.INTENT_PRICING_ESCROW, IntentParser.INTENT_ESCROW_STATUS):
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

        elif intent in (cls.INTENT_TRUST_SAFETY, IntentParser.INTENT_TRUST_SAFETY, IntentParser.INTENT_DISPUTE_HELP):
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

        else:
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

    # Provider delegation & routing chain (Groq -> Gemini -> Deterministic)
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
        tool_data: dict[str, Any] | None = None,
        pending_action: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        """Generate response via Groq -> Gemini -> Deterministic fallback cascade."""
        # Tier 1: Groq LLM
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                res = cls._call_groq(
                    api_key=groq_key,
                    message=message,
                    intent=intent,
                    entities=entities,
                    sources=sources,
                    language=language,
                    session=session,
                    tool_data=tool_data,
                    pending_action=pending_action,
                )
                if res and res.strip():
                    return res.strip(), "groq"
            except Exception as exc:
                logger.warning(f"Groq API call failed: {exc}. Cascading to Gemini fallback.")

        # Tier 2: Google Gemini LLM
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                res = cls._call_gemini(
                    api_key=gemini_key,
                    message=message,
                    intent=intent,
                    entities=entities,
                    sources=sources,
                    language=language,
                    session=session,
                    tool_data=tool_data,
                    pending_action=pending_action,
                )
                if res and res.strip():
                    return res.strip(), "gemini"
            except Exception as exc:
                logger.warning(f"Gemini API call failed: {exc}. Cascading to deterministic fallback.")

        # Tier 3: Guaranteed Deterministic Knowledge Rule Engine
        res = LLMProvider._generate_deterministic_response(
            intent=intent,
            entities=entities,
            sources=sources,
            language=language,
            tool_data=tool_data,
            pending_action=pending_action,
        )
        return res, "deterministic"

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
        tool_data: dict[str, Any] | None = None,
        pending_action: dict[str, Any] | None = None,
    ) -> str | None:
        """Call Groq API with candidate model cascade and verified tool data."""
        return LLMProvider._call_groq(
            api_key=api_key,
            user_message=message,
            intent=intent,
            entities=entities,
            sources=sources,
            language=language,
            conversation_history=session.get("messages", []),
            tool_data=tool_data,
            pending_action=pending_action,
        )

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
        tool_data: dict[str, Any] | None = None,
        pending_action: dict[str, Any] | None = None,
    ) -> str | None:
        """Call Google Gemini Flash API with verified tool data."""
        return LLMProvider._call_gemini(
            api_key=api_key,
            user_message=message,
            intent=intent,
            entities=entities,
            sources=sources,
            language=language,
            conversation_history=session.get("messages", []),
            tool_data=tool_data,
            pending_action=pending_action,
        )

    @classmethod
    def _empty_message_response(cls, conversation_id: str, language: str) -> dict[str, Any]:
        """Helpful response for empty initial message requests."""
        if language in [cls.LANG_HI, cls.LANG_HINGLISH]:
            resp = "Namaste! Main SpaceLoop LoopBot hoon. Main spaces dhoondhne, booking precheck ya fees samajhne mein aapki kaise madad kar sakta hoon?"
        elif language == cls.LANG_MR:
            resp = "नमस्कार! मी स्पेस-लूप लूपबॉट आहे. जागा शोधण्यासाठी किंवा बुकिंगसाठी मी आपली कशी मदत करू?"
        else:
            resp = "Hello! I am LoopBot, your SpaceLoop concierge. How can I assist you with space discovery, booking prechecks, or platform policies today?"

        return {
            "response": resp,
            "message": resp,
            "reply": resp,
            "type": "message",
            "intent": cls.INTENT_PLATFORM_HELP,
            "standard_intent": IntentParser.INTENT_GENERAL,
            "data": {},
            "sources": [],
            "suggested_actions": [
                {"type": "search_spaces", "label": "Explore Spaces", "payload": {}},
                {"type": "create_listing", "label": "List a Space", "payload": {}},
            ],
            "conversation_id": conversation_id,
            "language": language,
            "provider": "deterministic",
            "context": {},
        }
