"""REST API endpoints for SpaceLoop LoopBot Native AI Concierge."""

from typing import Any
from flask import Blueprint, g, jsonify, request

from backend.modules.ai.loopbot_orchestrator import LoopBotOrchestrator

loopbot_bp = Blueprint("loopbot", __name__)


def handle_loopbot_chat_request():
    """Handle conversational chat requests for LoopBot with full structured payload."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}

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


@loopbot_bp.route("/chat", methods=["POST"])
def loopbot_chat():
    """Primary chat endpoint for LoopBot."""
    return handle_loopbot_chat_request()


@loopbot_bp.route("/conversation/reset", methods=["POST"])
def loopbot_reset():
    """Reset a conversation session."""
    payload = request.get_json(silent=True) or {}
    cid = payload.get("conversation_id")
    if cid:
        from backend.modules.ai.context_manager import ConversationManager
        ConversationManager.reset_session(cid)
    return jsonify({"success": True, "message": "Conversation session reset."}), 200
