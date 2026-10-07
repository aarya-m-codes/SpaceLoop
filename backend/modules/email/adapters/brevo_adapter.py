"""Brevo (formerly Sendinblue) REST API Email Adapter for SpaceLoop.

Uses Brevo's v3 SMTP endpoint (https://api.brevo.com/v3/smtp/email).
"""

import logging
import os
from typing import Any
import requests

from backend.modules.email.adapters.base import BaseEmailAdapter, EmailDispatchResult

logger = logging.getLogger("spaceloop.email.brevo")


class BrevoEmailAdapter(BaseEmailAdapter):
    """Email delivery adapter for the Brevo transactional email API."""

    def __init__(self, api_key: str | None = None, api_url: str = "https://api.brevo.com/v3/smtp/email"):
        self.api_key = api_key or os.getenv("BREVO_API_KEY", "")
        self.api_url = api_url

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
        if not self.api_key:
            return EmailDispatchResult(
                success=False,
                provider="brevo",
                error="BREVO_API_KEY is not configured.",
            )

        sender_email = from_email or os.getenv("EMAIL_FROM_ADDRESS", "no-reply@spaceloop.in")
        sender_name = from_name or os.getenv("EMAIL_FROM_NAME", "SpaceLoop Marketplace")

        payload: dict[str, Any] = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content,
        }
        if text_content:
            payload["textContent"] = text_content
        if metadata:
            payload["params"] = metadata

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=5.0)
            if response.status_code in (200, 201):
                res_data = response.json()
                message_id = res_data.get("messageId")
                return EmailDispatchResult(
                    success=True,
                    provider="brevo",
                    message_id=message_id,
                )
            else:
                err_msg = f"Brevo API error {response.status_code}: {response.text}"
                logger.error(err_msg)
                return EmailDispatchResult(
                    success=False,
                    provider="brevo",
                    error=err_msg,
                )
        except Exception as exc:
            err_msg = f"Brevo request failed: {exc}"
            logger.error(err_msg)
            return EmailDispatchResult(
                success=False,
                provider="brevo",
                error=err_msg,
            )
