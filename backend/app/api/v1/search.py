"""SpaceLoop Semantic AI Search Blueprint.

Exposes:
- POST /api/v1/search (and GET /api/v1/search)
- POST /api/v1/search/embeddings/rebuild
- Reusable internal semantic search service
"""

from typing import Any
from flask import Blueprint, jsonify, request

from backend.modules.search.pipeline import DiscoveryPipeline, semantic_search
from backend.modules.search.vector_engine import VectorEngine

search_bp = Blueprint("search_v1", __name__)


@search_bp.route("", methods=["POST", "GET"])
@search_bp.route("/", methods=["POST", "GET"])
@search_bp.route("/search", methods=["POST", "GET"])
def execute_search():
    """Primary SpaceLoop Semantic AI Search endpoint.

    Supports:
    - Natural-language queries (e.g. "quiet workspace for 3 people tomorrow from 2 to 6 PM under ₹150/hour")
    - Structured filters (budget, capacity, space_type, amenities, noise_preference)
    - Geographic proximity & GPS location
    - Authenticated user context
    """
    user_context = None
    if hasattr(request, "current_user") and request.current_user:
        user_context = {
            "user_id": request.current_user.id,
            "role": getattr(request.current_user, "role", None),
        }

    from backend.modules.i18n.middleware import get_request_language
    from backend.modules.i18n.constants import normalize_language_code

    if request.method == "POST":
        payload: dict[str, Any] = request.get_json(silent=True) or {}
        query = payload.get("query") or payload.get("q")
        date = payload.get("date")
        hours = payload.get("hours") or payload.get("duration")
        budget = payload.get("budget")
        location = payload.get("location")
        page = max(1, int(payload.get("page", 1)))
        limit = min(100, max(1, int(payload.get("limit", 20))))
        require_available = bool(payload.get("require_available", False))
        filters = payload.get("filters")
        language = normalize_language_code(payload.get("language") or request.args.get("language") or request.args.get("lang") or get_request_language())
        payload_context = payload.get("user_context")
        if payload_context and isinstance(payload_context, dict):
            if user_context:
                user_context.update(payload_context)
            else:
                user_context = payload_context
    else:
        query = request.args.get("query") or request.args.get("q")
        date = request.args.get("date")
        hours = request.args.get("hours") or request.args.get("duration")
        budget = request.args.get("budget")
        location = request.args.get("location")
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 20))))
        require_available = request.args.get("require_available", "").lower() in ("true", "1")
        language = normalize_language_code(request.args.get("language") or request.args.get("lang") or get_request_language())
        filters = {
            "capacity": request.args.get("capacity"),
            "space_type": request.args.get("space_type"),
            "city": request.args.get("city"),
            "noise_preference": request.args.get("noise_preference") or request.args.get("noise"),
        }

    results = semantic_search(
        query=query,
        user_context=user_context,
        filters=filters,
        location=location,
        date=date,
        hours=hours,
        budget=budget,
        page=page,
        limit=limit,
        require_available=require_available,
        language=language,
    )

    return jsonify({
        "success": True,
        "data": results,
        "language": language,
        "results": results.get("results", []),
        "items": results.get("items", []),
        "total": results.get("total", 0),
        "page": results.get("page", 1),
        "limit": results.get("limit", 20),
        "total_pages": results.get("total_pages", 1),
        "parsed_constraints": results.get("parsed_constraints", {}),
    }), 200


@search_bp.route("/embeddings/rebuild", methods=["POST"])
def rebuild_embeddings():
    """Trigger vector embedding rebuild for active spaces."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    space_id = payload.get("space_id")
    force = bool(payload.get("force", False))
    summary = VectorEngine.rebuild_embeddings(space_id=space_id, force=force)
    return jsonify({
        "success": True,
        "data": summary,
    }), 200
