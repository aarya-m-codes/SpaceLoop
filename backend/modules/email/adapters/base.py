"""Base interface for SpaceLoop Email Adapters.

Enables seamless swapping of email delivery providers (Resend, Brevo, SMTP, In-Memory)
without altering platform business logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EmailDispatchResult:
    """Standardized response from email provider adapters."""
    success: bool
    provider: str
    message_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseEmailAdapter(ABC):
    """Abstract email delivery provider adapter interface."""

    @abstractmethod
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
        """Dispatch a single email message to the specified recipient."""
        raise NotImplementedError
