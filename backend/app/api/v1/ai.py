"""REST API endpoints for SpaceLoop LoopBot Conversational Concierge & AI Services."""

from typing import Any
from flask import Blueprint, g, jsonify, request

from backend.modules.ai.loopbot_orchestrator import LoopBotOrchestrator

ai_bp = Blueprint("ai", __name__)


def _handle_chat_request():
    """Common handler for conversational LoopBot queries."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}

    # Extract message from various common field names
    message = (
        payload.get("message")
        or payload.get("query")
        or payload.get("prompt")
        or payload.get("text")
        or ""
    )

    conversation_id = payload.get("conversation_id")
    context = payload.get("context") or {}
    language = payload.get("language")

    current_user = getattr(g, "current_user", None)

    result = LoopBotOrchestrator.process_message(
        message=message,
        conversation_id=conversation_id,
        context=context,
        language=language,
        user=current_user,
    )

    # Standard format fulfilling both top-level and data-wrapped contracts
    response_payload = {
        "success": True,
        "data": result.get("data", {}),
        "response": result["response"],
        "message": result["message"],
        "type": result.get("type", "message"),
        "intent": result["intent"],
        "standard_intent": result.get("standard_intent"),
        "sources": result["sources"],
        "suggested_actions": result["suggested_actions"],
        "conversation_id": result["conversation_id"],
        "language": result["language"],
        "provider": result.get("provider", "deterministic"),
        "context": result.get("context", {}),
    }

    return jsonify(response_payload), 200


@ai_bp.route("/chat", methods=["POST"])
def ai_chat():
    """Primary conversational chat endpoint for LoopBot."""
    return _handle_chat_request()


@ai_bp.route("/assistant", methods=["POST"])
def ai_assistant():
    """Assistant query endpoint."""
    return _handle_chat_request()


@ai_bp.route("/concierge/chat", methods=["POST"])
def concierge_chat():
    """Concierge chat endpoint."""
    return _handle_chat_request()


@ai_bp.route("/nlp/dispatch", methods=["POST"])
def nlp_dispatch():
    """NLP message dispatcher for intent classification and entity-assisted routing."""
    return _handle_chat_request()
