"""Standard SMTP Protocol Email Adapter for SpaceLoop.

Uses Python's built-in smtplib to transmit MIME multipart emails.
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import os
import smtplib
import uuid
from typing import Any

from backend.modules.email.adapters.base import BaseEmailAdapter, EmailDispatchResult

logger = logging.getLogger("spaceloop.email.smtp")


class SMTPEmailAdapter(BaseEmailAdapter):
    """Email delivery adapter connecting to standard SMTP relays (AWS SES, SendGrid, Postmark, etc.)."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
    ):
        self.host = host or os.getenv("SMTP_HOST", "localhost")
        self.port = port or int(os.getenv("SMTP_PORT", "587"))
        self.user = user or os.getenv("SMTP_USER", "")
        self.password = password or os.getenv("SMTP_PASSWORD", "")
        self.use_tls = use_tls

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
        sender_email = from_email or os.getenv("EMAIL_FROM_ADDRESS", "no-reply@spaceloop.in")
        sender_name = from_name or os.getenv("EMAIL_FROM_NAME", "SpaceLoop Marketplace")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email

        message_id = f"<spaceloop-{uuid.uuid4().hex[:16]}@{self.host}>"
        msg["Message-ID"] = message_id

        # Attach text and HTML versions
        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            if self.port == 465:
                # SSL connection
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=5.0)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=5.0)
                if self.use_tls:
                    server.starttls()

            if self.user and self.password:
                server.login(self.user, self.password)

            server.send_message(msg)
            server.quit()

            return EmailDispatchResult(
                success=True,
                provider="smtp",
                message_id=message_id,
            )
        except Exception as exc:
            err_msg = f"SMTP dispatch failed: {exc}"
            logger.error(err_msg)
            return EmailDispatchResult(
                success=False,
                provider="smtp",
                error=err_msg,
            )
