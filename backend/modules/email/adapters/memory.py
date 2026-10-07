"""In-Memory / Development Mock Email Adapter for SpaceLoop.

Stores outbound emails in an in-memory audit log for zero-dependency local testing.
"""

from datetime import datetime, timezone
import uuid
from typing import Any

from backend.modules.email.adapters.base import BaseEmailAdapter, EmailDispatchResult


class InMemoryEmailAdapter(BaseEmailAdapter):
    """In-memory email delivery adapter for development and automated test suites."""

    def __init__(self):
        self._outbox: list[dict[str, Any]] = []

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EmailDispatchResult:
        """Record dispatched email into memory outbox."""
        message_id = f"mem-{uuid.uuid4().hex[:12]}"
        email_record = {
            "id": message_id,
            "to": to_email,
            "subject": subject,
            "html": html_content,
            "text": text_content or "",
            "from_email": from_email or "no-reply@spaceloop.in",
            "from_name": from_name or "SpaceLoop",
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._outbox.append(email_record)

        return EmailDispatchResult(
            success=True,
            provider="in_memory",
            message_id=message_id,
            metadata={"outbox_size": len(self._outbox)},
        )

    def get_outbox(self) -> list[dict[str, Any]]:
        """Retrieve full in-memory outbound email history."""
        return list(self._outbox)

    def get_last_email(self) -> dict[str, Any] | None:
        """Retrieve most recently dispatched email."""
        return self._outbox[-1] if self._outbox else None

    def clear(self) -> None:
        """Reset the in-memory outbox."""
        self._outbox.clear()
