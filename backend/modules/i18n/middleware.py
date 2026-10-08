"""Flask middleware and request context language resolution for SpaceLoop."""

from typing import Any
from flask import g, has_request_context, jsonify, request

from backend.modules.i18n.constants import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    normalize_language_code,
)
from backend.modules.i18n.lexicon import localize_error


def get_request_language(default: str = DEFAULT_LANGUAGE) -> str:
    """Extract and normalize target language for current Flask request context.
    
    Priority cascade:
    1. Query param: `?lang=...` or `?language=...`
    2. Explicit custom header: `X-Language: ...`
    3. JSON request payload: `{"language": "..."}`
    4. Authenticated user preference: `current_user.preferred_language`
    5. HTTP standard header: `Accept-Language: ...`
    6. Default platform language: 'en'
    """
    if not has_request_context():
        return normalize_language_code(default)

    # 1. Query parameters
    lang_param = request.args.get("lang") or request.args.get("language")
    if lang_param:
        return normalize_language_code(lang_param)

    # 2. Custom header
    x_lang = request.headers.get("X-Language")
    if x_lang:
        return normalize_language_code(x_lang)

    # 3. JSON body
    if request.is_json:
        try:
            body = request.get_json(silent=True) or {}
            if isinstance(body, dict) and body.get("language"):
                return normalize_language_code(body["language"])
        except Exception:
            pass

    # 4. Authenticated user context
    current_user = getattr(g, "current_user", None) or getattr(request, "current_user", None)
    if current_user and getattr(current_user, "preferred_language", None):
        return normalize_language_code(current_user.preferred_language)

    # 5. Standard Accept-Language header (e.g., 'mr-IN,mr;q=0.9,en;q=0.8')
    accept_lang = request.headers.get("Accept-Language")
    if accept_lang:
        parts = [p.strip().split(";")[0] for p in accept_lang.split(",")]
        for p in parts:
            normalized = normalize_language_code(p)
            if normalized in SUPPORTED_LANGUAGES:
                return normalized

    return normalize_language_code(default)


def localized_json_error(code: str, status_code: int = 400, details: Any = None) -> tuple[Any, int]:
    """Return standard localized API error JSON response."""
    lang = get_request_language()
    message = localize_error(code, lang)
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "language": lang,
        },
    }
    if details is not None:
        payload["error"]["details"] = details
    return jsonify(payload), status_code
