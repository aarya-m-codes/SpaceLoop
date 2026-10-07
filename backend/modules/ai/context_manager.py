"""Conversation and multi-turn context management for SpaceLoop LoopBot.

Provides persistent session memory, TTL expiration, structured entity accumulation,
and the consequential action confirmation state machine.
"""

import copy
import logging
import secrets
import threading
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("spaceloop.ai.context")

# Session inactivity TTL: 30 minutes
SESSION_TTL_SECONDS = 1800


class ConversationManager:
    """Thread-safe multi-turn session state and entity accumulation manager."""

    _lock = threading.Lock()
    _sessions: dict[str, dict[str, Any]] = {}

    @classmethod
    def _clean_expired_sessions(cls) -> None:
        """Purge sessions inactive beyond SESSION_TTL_SECONDS."""
        now = time.time()
        expired_keys = [
            cid for cid, s in cls._sessions.items()
            if now - s.get("_last_active_epoch", now) > SESSION_TTL_SECONDS
        ]
        for cid in expired_keys:
            cls._sessions.pop(cid, None)

    @classmethod
    def get_or_create_session(cls, conversation_id: str | None = None) -> tuple[str, dict[str, Any]]:
        """Retrieve existing conversation session or initialize a fresh structured session."""
        with cls._lock:
            cls._clean_expired_sessions()
            now_epoch = time.time()
            now_iso = datetime.now(timezone.utc).isoformat()

            if not conversation_id or conversation_id not in cls._sessions:
                cid = conversation_id or f"conv-{secrets.token_hex(6)}"
                fresh_session: dict[str, Any] = {
                    "conversation_id": cid,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "_last_active_epoch": now_epoch,
                    "messages": [],
                    "accumulated_entities": {
                        "city": None,
                        "neighborhood": None,
                        "location": None,
                        "date": None,
                        "start_time": None,
                        "end_time": None,
                        "duration_hours": None,
                        "budget": None,
                        "capacity": None,
                        "space_type": None,
                        "amenities": [],
                        "noise_preference": None,
                        "selected_space_id": None,
                        "selected_booking_id": None,
                    },
                    "pending_action": None,
                    "last_intent": None,
                    "language": "en",
                }
                cls._sessions[cid] = fresh_session
                return cid, copy.deepcopy(cls._sessions[cid])

            session = cls._sessions[conversation_id]
            session["updated_at"] = now_iso
            session["_last_active_epoch"] = now_epoch
            return conversation_id, copy.deepcopy(session)

    @classmethod
    def append_message(
        cls,
        conversation_id: str,
        role: str,
        content: str,
        entities: dict[str, Any] | None = None,
        intent: str | None = None,
    ) -> None:
        """Record a conversational turn and atomically merge extracted entities into session memory."""
        with cls._lock:
            if conversation_id not in cls._sessions:
                return

            session = cls._sessions[conversation_id]
            now_iso = datetime.now(timezone.utc).isoformat()
            now_epoch = time.time()

            session["messages"].append({
                "role": role,
                "content": content,
                "timestamp": now_iso,
            })

            # Retain last 20 turns
            if len(session["messages"]) > 20:
                session["messages"] = session["messages"][-20:]

            session["updated_at"] = now_iso
            session["_last_active_epoch"] = now_epoch

            if intent:
                session["last_intent"] = intent

            if entities:
                acc = session["accumulated_entities"]
                for k, v in entities.items():
                    if v is not None and v != "" and v != []:
                        if k == "amenities" and isinstance(v, list):
                            existing = set(acc.get("amenities", []))
                            existing.update(v)
                            acc["amenities"] = sorted(list(existing))
                        else:
                            acc[k] = v

    @classmethod
    def update_entities(cls, conversation_id: str, new_entities: dict[str, Any]) -> None:
        """Directly update structured accumulated entities for a conversation."""
        with cls._lock:
            if conversation_id in cls._sessions:
                acc = cls._sessions[conversation_id]["accumulated_entities"]
                for k, v in new_entities.items():
                    if v is not None and v != "" and v != []:
                        if k == "amenities" and isinstance(v, list):
                            existing = set(acc.get("amenities", []))
                            existing.update(v)
                            acc["amenities"] = sorted(list(existing))
                        else:
                            acc[k] = v

    @classmethod
    def set_pending_action(cls, conversation_id: str, action_data: dict[str, Any]) -> None:
        """Set a pending consequential action requiring explicit confirmation before execution."""
        with cls._lock:
            if conversation_id in cls._sessions:
                cls._sessions[conversation_id]["pending_action"] = {
                    **action_data,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

    @classmethod
    def get_pending_action(cls, conversation_id: str) -> dict[str, Any] | None:
        """Retrieve current pending consequential action."""
        with cls._lock:
            if conversation_id in cls._sessions:
                action = cls._sessions[conversation_id].get("pending_action")
                return copy.deepcopy(action) if action else None
            return None

    @classmethod
    def clear_pending_action(cls, conversation_id: str) -> None:
        """Clear the pending consequential action."""
        with cls._lock:
            if conversation_id in cls._sessions:
                cls._sessions[conversation_id]["pending_action"] = None

    @classmethod
    def reset_session(cls, conversation_id: str) -> None:
        """Reset conversation session to clean state."""
        with cls._lock:
            cls._sessions.pop(conversation_id, None)
