"""SpaceLoop Email Module.

Provides pluggable email adapters (Resend, Brevo, SMTP, In-Memory)
and transactional email dispatch with EmailLog audit trails.
"""

from backend.modules.email.adapters.base import BaseEmailAdapter, EmailDispatchResult
from backend.modules.email.adapters.brevo_adapter import BrevoEmailAdapter
from backend.modules.email.adapters.memory import InMemoryEmailAdapter
from backend.modules.email.adapters.resend_adapter import ResendEmailAdapter
from backend.modules.email.adapters.smtp_adapter import SMTPEmailAdapter
from backend.modules.email.service import EmailService

__all__ = [
    "BaseEmailAdapter",
    "EmailDispatchResult",
    "EmailService",
    "InMemoryEmailAdapter",
    "ResendEmailAdapter",
    "BrevoEmailAdapter",
    "SMTPEmailAdapter",
]
