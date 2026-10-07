import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from flask import current_app


def _b64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    """Base64url decode with automatic padding recovery."""
    rem = len(data) % 4
    if rem > 0:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def _get_signing_key() -> bytes:
    """Retrieve secret key from Flask app configuration."""
    try:
        secret = current_app.config.get("JWT_SECRET_KEY") or current_app.config.get("SECRET_KEY", "spaceloop-jwt-secret")
    except RuntimeError:
        secret = "spaceloop-jwt-secret"
    return secret.encode("utf-8") if isinstance(secret, str) else secret


def encode_jwt(payload: dict[str, Any], expires_in_seconds: int = 3600) -> str:
    """Encode payload into an RFC 7519 compliant HS256 JWT."""
    now = int(time.time())
    full_payload = {
        **payload,
        "iat": now,
        "exp": now + expires_in_seconds,
    }

    header = {"alg": "HS256", "typ": "JWT"}
    header_bytes = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_bytes = json.dumps(full_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    header_b64 = _b64url_encode(header_bytes)
    payload_b64 = _b64url_encode(payload_bytes)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(_get_signing_key(), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_jwt(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """Decode and verify an HS256 JWT token."""
    if not token or not isinstance(token, str):
        raise ValueError("Invalid token format.")

    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError("Malformed JWT token.")

    header_b64, payload_b64, sig_b64 = parts

    # Verify signature in constant time
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(_get_signing_key(), signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Token signature verification failed.")

    # Decode payload
    try:
        payload_data = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise ValueError("Failed to decode token payload.") from exc

    # Verify expiration
    exp = payload_data.get("exp")
    if exp is not None and int(time.time()) > int(exp):
        raise ValueError("Token has expired.")

    # Verify token type if specified
    if expected_type and payload_data.get("type") != expected_type:
        raise ValueError(f"Invalid token type. Expected {expected_type}, got {payload_data.get('type')}.")

    return payload_data


def create_access_token(
    user_id: int,
    email: str,
    role: str,
    active_role: str | None = None,
    expires_in_minutes: int = 60,
) -> str:
    """Create a standard SpaceLoop Bearer access token."""
    payload = {
        "sub": user_id,
        "email": email,
        "role": role.lower(),
        "active_role": (active_role or role).lower(),
        "type": "access",
    }
    return encode_jwt(payload, expires_in_seconds=expires_in_minutes * 60)


def create_refresh_token(user_id: int, expires_in_days: int = 30) -> str:
    """Create a long-lived refresh token."""
    payload = {
        "sub": user_id,
        "type": "refresh",
    }
    return encode_jwt(payload, expires_in_seconds=expires_in_days * 86400)


def create_mfa_pending_token(user_id: int, expires_in_minutes: int = 5) -> str:
    """Create a short-lived token representing an active login awaiting 2FA challenge."""
    payload = {
        "sub": user_id,
        "type": "mfa_pending",
    }
    return encode_jwt(payload, expires_in_seconds=expires_in_minutes * 60)


def generate_crypto_token() -> tuple[str, str]:
    """Generate a single-use random token and its SHA-256 database hash.
    
    Returns:
        (raw_token, token_hash)
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, token_hash


def hash_token(raw_token: str) -> str:
    """Return SHA-256 hex digest of a raw token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
