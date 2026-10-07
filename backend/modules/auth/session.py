import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from flask import Flask, Response, g, request

from backend.core.database import db
from backend.modules.auth.tokens import decode_jwt
from models import DeviceSession, User, utc_now

logger = logging.getLogger("spaceloop.auth.session")

COOKIE_NAME = "spaceloop_session"
COOKIE_MAX_AGE = 30 * 86400  # 30 days


def extract_token_from_request() -> str | None:
    """Extract authentication token from Authorization header or HTTP-only cookie."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token

    # Check HTTP-only cookie fallback
    cookie_token = request.cookies.get(COOKIE_NAME) or request.cookies.get("access_token")
    if cookie_token:
        return cookie_token.strip()

    return None


def resolve_authenticated_user() -> User | None:
    """Resolve current user from Bearer token, session cookie, or X-User-Id fallback."""
    token = extract_token_from_request()
    if token:
        try:
            payload = decode_jwt(token, expected_type="access")
            user_id = payload.get("sub")
            if user_id:
                user = db.session.get(User, int(user_id))
                if user and user.is_active:
                    return user
        except Exception as exc:
            logger.debug(f"Token decoding failed during user resolution: {exc}")

    # Fallback: X-User-Id for cross-origin / internal proxy environments
    x_user_id = request.headers.get("X-User-Id")
    if x_user_id and x_user_id.isdigit():
        try:
            user = db.session.get(User, int(x_user_id))
            if user and user.is_active:
                return user
        except Exception as exc:
            logger.debug(f"Failed to resolve user from X-User-Id header: {exc}")

    return None


def create_device_session(user_id: int, device_name: str | None = None) -> tuple[DeviceSession, str]:
    """Create a new tracked device session in the database.
    
    Returns:
        (device_session_record, raw_session_token)
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    user_agent = request.headers.get("User-Agent", "Unknown Device")[:500]
    dev_name = device_name or (user_agent[:40] if user_agent != "Unknown Device" else "Web Browser")

    session_record = DeviceSession(
        user_id=user_id,
        session_token_hash=token_hash,
        device_name=dev_name,
        ip_address=client_ip[:45],
        user_agent=user_agent,
        is_active=True,
        last_seen=utc_now(),
        expires_at=utc_now() + timedelta(days=30),
    )
    db.session.add(session_record)
    db.session.commit()

    return session_record, raw_token


def invalidate_user_session(user_id: int) -> None:
    """Invalidate active device sessions for the given user."""
    try:
        DeviceSession.query.filter_by(user_id=user_id, is_active=True).update({"is_active": False})
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning(f"Error invalidating sessions for user {user_id}: {exc}")


def set_auth_cookies(response: Response, access_token: str, is_secure: bool = False) -> None:
    """Attach HTTP-only secure session cookie to the HTTP response."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=is_secure,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear session cookies upon logout."""
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="Lax",
    )
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="Lax",
    )


def init_session_context(app: Flask) -> None:
    """Register before_request hook that binds current_user to Flask context (g)."""

    @app.before_request
    def attach_current_user() -> None:
        g.current_user = resolve_authenticated_user()
