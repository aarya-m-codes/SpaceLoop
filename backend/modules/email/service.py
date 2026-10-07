"""SpaceLoop Transactional Email Service.

Coordinates:
- Dynamic adapter resolution (Resend, Brevo, SMTP, In-Memory)
- Template rendering for 8+ transactional event types
- Complete audit logging to EmailLog table
"""

from datetime import datetime, timezone
import logging
import os
from typing import Any

from backend.core.database import db
from backend.modules.email.adapters.base import BaseEmailAdapter, EmailDispatchResult
from backend.modules.email.adapters.brevo_adapter import BrevoEmailAdapter
from backend.modules.email.adapters.memory import InMemoryEmailAdapter
from backend.modules.email.adapters.resend_adapter import ResendEmailAdapter
from backend.modules.email.adapters.smtp_adapter import SMTPEmailAdapter
from backend.modules.email.templates import render_email_template
from models import EmailLog

logger = logging.getLogger("spaceloop.email.service")


class EmailService:
    """Core transactional email service for SpaceLoop."""

    _adapter: BaseEmailAdapter | None = None
    _in_memory_instance: InMemoryEmailAdapter | None = None

    @classmethod
    def get_adapter(cls) -> BaseEmailAdapter:
        """Resolve current email delivery adapter based on environment configuration."""
        if cls._adapter is not None:
            return cls._adapter

        provider = os.getenv("EMAIL_PROVIDER", "memory").lower().strip()

        if provider == "resend":
            return ResendEmailAdapter()
        elif provider == "brevo":
            return BrevoEmailAdapter()
        elif provider == "smtp":
            return SMTPEmailAdapter()
        else:
            # Default to in-memory adapter
            if cls._in_memory_instance is None:
                cls._in_memory_instance = InMemoryEmailAdapter()
            return cls._in_memory_instance

    @classmethod
    def set_adapter(cls, adapter: BaseEmailAdapter | None) -> None:
        """Manually override active adapter (useful for testing and mocking)."""
        cls._adapter = adapter

    @classmethod
    def send_transactional_email(
        cls,
        template_name: str,
        recipient_email: str,
        template_data: dict[str, Any] | None = None,
        persist_log: bool = True,
    ) -> tuple[bool, EmailLog | None]:
        """Render and transmit a transactional email, recording an immutable EmailLog."""
        data = template_data or {}
        subject, html_content, text_content = render_email_template(template_name, data)

        adapter = cls.get_adapter()
        result: EmailDispatchResult = adapter.send_email(
            to_email=recipient_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            metadata={"template": template_name},
        )

        email_log = None
        if persist_log:
            try:
                now = datetime.now(timezone.utc)
                email_log = EmailLog(
                    recipient_email=recipient_email,
                    template_name=template_name,
                    subject=subject,
                    body=html_content,
                    status="SENT" if result.success else "FAILED",
                    error_message=result.error,
                    sent_at=now if result.success else None,
                )
                db.session.add(email_log)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to record EmailLog: {e}", exc_info=True)

        return result.success, email_log

    # -------------------------------------------------------------------------
    # Convenience Transactional Dispatchers
    # -------------------------------------------------------------------------

    @classmethod
    def send_verification_email(cls, recipient_email: str, token: str, user_name: str | None = None) -> tuple[bool, EmailLog | None]:
        return cls.send_transactional_email(
            template_name="verification",
            recipient_email=recipient_email,
            template_data={"token": token, "user_name": user_name},
        )

    @classmethod
    def send_password_reset_email(cls, recipient_email: str, token: str, user_name: str | None = None) -> tuple[bool, EmailLog | None]:
        return cls.send_transactional_email(
            template_name="password_reset",
            recipient_email=recipient_email,
            template_data={"token": token, "user_name": user_name},
        )

    @classmethod
    def send_booking_confirmation_email(cls, recipient_email: str, booking_data: dict[str, Any]) -> tuple[bool, EmailLog | None]:
        return cls.send_transactional_email(
            template_name="booking",
            recipient_email=recipient_email,
            template_data=booking_data,
        )

    @classmethod
    def send_cancellation_email(cls, recipient_email: str, cancellation_data: dict[str, Any]) -> tuple[bool, EmailLog | None]:
        return cls.send_transactional_email(
            template_name="cancellation",
            recipient_email=recipient_email,
            template_data=cancellation_data,
        )

    @classmethod
    def send_host_approval_email(cls, recipient_email: str, approval_data: dict[str, Any]) -> tuple[bool, EmailLog | None]:
        return cls.send_transactional_email(
            template_name="host_approval",
            recipient_email=recipient_email,
            template_data=approval_data,
        )

    @classmethod
    def send_host_rejection_email(cls, recipient_email: str, rejection_data: dict[str, Any]) -> tuple[bool, EmailLog | None]:
        return cls.send_transactional_email(
            template_name="host_rejection",
            recipient_email=recipient_email,
            template_data=rejection_data,
        )

    @classmethod
    def send_check_in_email(cls, recipient_email: str, checkin_data: dict[str, Any]) -> tuple[bool, EmailLog | None]:
        return cls.send_transactional_email(
            template_name="check_in",
            recipient_email=recipient_email,
            template_data=checkin_data,
        )

    @classmethod
    def send_checkout_email(cls, recipient_email: str, checkout_data: dict[str, Any]) -> tuple[bool, EmailLog | None]:
        return cls.send_transactional_email(
            template_name="checkout",
            recipient_email=recipient_email,
            template_data=checkout_data,
        )

    @classmethod
    def send_dispute_email(cls, recipient_email: str, dispute_data: dict[str, Any]) -> tuple[bool, EmailLog | None]:
        return cls.send_transactional_email(
            template_name="dispute",
            recipient_email=recipient_email,
            template_data=dispute_data,
        )

    @classmethod
    def get_email_logs(
        cls,
        recipient_email: str | None = None,
        template_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query EmailLog audit entries."""
        query = EmailLog.query
        if recipient_email:
            query = query.filter_by(recipient_email=recipient_email)
        if template_name:
            query = query.filter_by(template_name=template_name)
        logs = query.order_by(EmailLog.created_at.desc()).offset(offset).limit(limit).all()
        return [log.to_dict() for log in logs]
