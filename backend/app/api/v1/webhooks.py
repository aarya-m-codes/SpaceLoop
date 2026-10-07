import hmac
import hashlib
import logging
import os
import time
from typing import Any
from flask import Blueprint, current_app, jsonify, request

logger = logging.getLogger("spaceloop.webhooks")
webhooks_bp = Blueprint("webhooks_api", __name__)

# In-memory replay cache: event_id -> timestamp
_PROCESSED_WEBHOOK_EVENTS: dict[str, float] = {}
MAX_REPLAY_WINDOW_SECONDS = 300  # 5 minutes


def is_valid_signature(payload_bytes: bytes, signature: str, secret: str) -> bool:
    """Validate HMAC-SHA256 signature against webhook payload."""
    if not signature or not secret:
        return False
    expected = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@webhooks_bp.route("/payment", methods=["POST"])
def payment_webhook():
    """Handle asynchronous inbound payment and escrow settlement webhooks with replay & forgery defenses."""
    raw_body = request.get_data()
    secret = os.getenv("PAYMENT_WEBHOOK_SECRET", os.getenv("WEBHOOK_SECRET", ""))
    sig = request.headers.get("X-Webhook-Signature") or request.headers.get("X-Razorpay-Signature") or ""
    timestamp_header = request.headers.get("X-Webhook-Timestamp")

    is_testing = False
    try:
        is_testing = bool(current_app and current_app.config.get("TESTING"))
    except Exception:
        pass

    # 1. Signature Verification (enforced in production or whenever secret is configured)
    if secret:
        if not is_valid_signature(raw_body, sig, secret):
            logger.warning("Rejected forged or invalid webhook signature.")
            return jsonify({
                "success": False,
                "error": {"code": "INVALID_SIGNATURE", "message": "Webhook cryptographic signature mismatch."},
            }), 401
    elif not is_testing and (os.getenv("ENV") == "production" or os.getenv("FLASK_ENV") == "production"):
        logger.error("PAYMENT_WEBHOOK_SECRET missing in production environment.")
        return jsonify({
            "success": False,
            "error": {"code": "CONFIG_ERROR", "message": "Webhook secret not configured on server."},
        }), 500

    # 2. Replay Protection: Timestamp check (within 5 minutes)
    if timestamp_header:
        try:
            ts = float(timestamp_header)
            now = time.time()
            if abs(now - ts) > MAX_REPLAY_WINDOW_SECONDS:
                logger.warning(f"Rejected replayed webhook timestamp ({ts} vs {now}).")
                return jsonify({
                    "success": False,
                    "error": {"code": "TIMESTAMP_EXPIRED", "message": "Webhook timestamp outside acceptable window."},
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": {"code": "INVALID_TIMESTAMP", "message": "Invalid X-Webhook-Timestamp header format."},
            }), 400

    payload: dict[str, Any] = request.get_json(silent=True) or {}
    event_id = payload.get("event_id") or payload.get("id") or request.headers.get("X-Webhook-Id")

    # 3. Replay Protection: Event ID deduplication
    if event_id:
        if event_id in _PROCESSED_WEBHOOK_EVENTS:
            logger.info(f"Duplicate webhook event '{event_id}' skipped (idempotent).")
            return jsonify({
                "success": True,
                "received": True,
                "message": "Event already processed (idempotent duplicate).",
            }), 200
        _PROCESSED_WEBHOOK_EVENTS[event_id] = time.time()

    # Clean up old replay cache entries older than 1 hour
    cutoff = time.time() - 3600
    to_delete = [eid for eid, t in _PROCESSED_WEBHOOK_EVENTS.items() if t < cutoff]
    for eid in to_delete:
        _PROCESSED_WEBHOOK_EVENTS.pop(eid, None)

    logger.info(f"Accepted verified payment webhook event: {event_id or 'anonymous'}")
    return jsonify({
        "success": True,
        "received": True,
        "message": "Payment webhook processed successfully.",
    }), 200
