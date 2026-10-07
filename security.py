import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timezone
from typing import Any
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    """Securely hash a user password using PBKDF2/scrypt via Werkzeug."""
    if not password:
        raise ValueError("Password cannot be empty.")
    return generate_password_hash(password, method="scrypt")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain-text password against a stored secure password hash."""
    if not password or not password_hash:
        return False
    return check_password_hash(password_hash, password)


def generate_secure_token(length_bytes: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(length_bytes)


def generate_numeric_otp(digits: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    range_start = 10 ** (digits - 1)
    range_end = (10 ** digits) - 1
    return str(secrets.randbelow(range_end - range_start + 1) + range_start)


def hash_token(token: str) -> str:
    """Produce a SHA-256 hex digest of a token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_compare(val1: str, val2: str) -> bool:
    """Constant-time string comparison to prevent timing side-channel attacks."""
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password compliance: at least 8 chars, containing digit, upper, lower, and symbol."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special symbol."
    return True, "Password meets security requirements."


def generate_access_code(length: int = 6) -> str:
    """Generate an alphanumeric access code for space check-in."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # omit ambiguous characters (0, O, 1, I)
    return "".join(secrets.choice(alphabet) for _ in range(length))


# Compatibility alias
from backend.modules.auth.permissions import require_auth as token_required

