"""Resend REST API Email Adapter for SpaceLoop.

Uses Resend's REST endpoint (https://api.resend.com/emails) to deliver transactional emails.
"""

import logging
import os
from typing import Any
import requests

from backend.modules.email.adapters.base import BaseEmailAdapter, EmailDispatchResult

logger = logging.getLogger("spaceloop.email.resend")


class ResendEmailAdapter(BaseEmailAdapter):
    """Email delivery adapter for the Resend transactional service."""

    def __init__(self, api_key: str | None = None, api_url: str = "https://api.resend.com/emails"):
        self.api_key = api_key or os.getenv("RESEND_API_KEY", "")
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
                provider="resend",
                error="RESEND_API_KEY is not configured.",
            )

        sender_email = from_email or os.getenv("EMAIL_FROM_ADDRESS", "no-reply@spaceloop.in")
        sender_name = from_name or os.getenv("EMAIL_FROM_NAME", "SpaceLoop Marketplace")
        from_formatted = f"{sender_name} <{sender_email}>"

        payload = {
            "from": from_formatted,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        if text_content:
            payload["text"] = text_content
        if metadata:
            payload["tags"] = [{"name": k, "value": str(v)} for k, v in metadata.items()]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=5.0)
            if response.status_code in (200, 201):
                res_data = response.json()
                message_id = res_data.get("id")
                return EmailDispatchResult(
                    success=True,
                    provider="resend",
                    message_id=message_id,
                )
            else:
                err_msg = f"Resend API error {response.status_code}: {response.text}"
                logger.error(err_msg)
                return EmailDispatchResult(
                    success=False,
                    provider="resend",
                    error=err_msg,
                )
        except Exception as exc:
            err_msg = f"Resend request failed: {exc}"
            logger.error(err_msg)
            return EmailDispatchResult(
                success=False,
                provider="resend",
                error=err_msg,
            )
