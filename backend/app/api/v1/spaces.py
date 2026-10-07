from typing import Any
from flask import Blueprint, g, jsonify, request

from backend.modules.auth.permissions import require_auth
from backend.modules.search import AIMatcher, DiscoveryPipeline
from backend.modules.spaces.photo_service import PhotoService
from backend.modules.spaces.service import SpaceService
from space_ai import SpaceAIAdapter

spaces_bp = Blueprint("spaces", __name__)


@spaces_bp.route("", methods=["GET"])
def list_spaces():
    """Discover spaces with optional filtering (category, space_type, city, price range)."""
    category = request.args.get("category")
    space_type = request.args.get("space_type")
    city = request.args.get("city")

    min_price = None
    if request.args.get("min_price"):
        try:
            min_price = float(request.args.get("min_price"))
        except ValueError:
            pass

    max_price = None
    if request.args.get("max_price"):
        try:
            max_price = float(request.args.get("max_price"))
        except ValueError:
            pass

    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    data = SpaceService.list_spaces(
        category=category,
        space_type=space_type,
        city=city,
        min_price=min_price,
        max_price=max_price,
        active_only=True,
        page=page,
        limit=limit,
    )

    return jsonify({
        "success": True,
        "spaces": data["items"],
        "items": data["items"],
        "data": data,
        "total": data["total"],
        "page": page,
        "limit": limit,
        "total_pages": data["total_pages"],
    }), 200


@spaces_bp.route("/<int:space_id>", methods=["GET"])
def get_space(space_id: int):
    """Retrieve detailed space listing."""
    space = SpaceService.get_space_by_id(space_id)
    if not space:
        return jsonify({
            "success": False,
            "error": {"code": "NOT_FOUND", "message": "Space listing not found."},
        }), 404

    return jsonify({
        "success": True,
        "data": space.to_dict(),
    }), 200


@spaces_bp.route("", methods=["POST"])
@require_auth
def create_space():
    """Create a new space listing (authenticated hosts)."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    result, err, status = SpaceService.create_space(g.current_user.id, payload)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Space created successfully.",
    }), 201


@spaces_bp.route("/<int:space_id>", methods=["PUT", "PATCH"])
@require_auth
def update_space(space_id: int):
    """Owner-only space updating."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    result, err, status = SpaceService.update_space(space_id, g.current_user, payload)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "UPDATE_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Space updated successfully.",
    }), 200


@spaces_bp.route("/<int:space_id>/toggle-status", methods=["POST"])
@require_auth
def toggle_space_status(space_id: int):
    """Owner-only activation/deactivation toggle."""
    result, err, status = SpaceService.toggle_space_status(space_id, g.current_user)

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "ACTION_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result["space"],
        "message": f"Space listing {result['status_text']}.",
    }), 200


@spaces_bp.route("/<int:space_id>/check-availability", methods=["GET"])
def check_availability(space_id: int):
    """Check slot availability against confirmed bookings."""
    date_str = request.args.get("date")
    start_time_str = request.args.get("start_time")
    end_time_str = request.args.get("end_time")

    result, err, status = SpaceService.check_availability(
        space_id=space_id,
        date_str=date_str,
        start_time_str=start_time_str,
        end_time_str=end_time_str,
    )

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "AVAILABILITY_QUERY_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
    }), 200


@spaces_bp.route("/<int:space_id>/reviews", methods=["GET"])
def list_reviews(space_id: int):
    """Fetch space verified stay reviews."""
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    result, err, status = SpaceService.list_reviews(space_id, page=page, limit=limit)
    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "REVIEWS_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
    }), 200


@spaces_bp.route("/<int:space_id>/reviews", methods=["POST"])
@require_auth
def add_review(space_id: int):
    """Submit a verified review (requires verified completed booking stay)."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    rating = payload.get("rating")
    comment = payload.get("comment", "")
    booking_id = payload.get("booking_id")

    if rating is None:
        return jsonify({
            "success": False,
            "error": {"code": "BAD_REQUEST", "message": "Rating (1-5) is required."},
        }), 400

    result, err, status = SpaceService.add_review(
        space_id=space_id,
        guest_user=g.current_user,
        rating=rating,
        comment=comment,
        booking_id=booking_id,
    )

    if err or not result:
        return jsonify({
            "success": False,
            "error": {"code": "REVIEW_SUBMISSION_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": result,
        "message": "Review submitted successfully.",
    }), 201


@spaces_bp.route("/upload-photo", methods=["POST"])
@require_auth
def upload_photo():
    """Upload listing photo with 5MB limit and binary magic byte validation."""
    if "photo" not in request.files and "file" not in request.files:
        return jsonify({
            "success": False,
            "error": {"code": "BAD_REQUEST", "message": "No file uploaded under key 'photo' or 'file'."},
        }), 400

    file = request.files.get("photo") or request.files.get("file")
    url, err, status = PhotoService.save_photo(file)

    if err or not url:
        return jsonify({
            "success": False,
            "error": {"code": "UPLOAD_FAILED", "message": err},
        }), status

    return jsonify({
        "success": True,
        "data": {
            "url": url,
            "filename": url.split("/")[-1],
        },
        "message": "Photo uploaded successfully.",
    }), 201


@spaces_bp.route("/ai-scan", methods=["POST"])
def ai_scan():
    """AI endpoint adapter: analyzes space photos and typology for lighting, noise, power, and uses."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    photo_url = data.get("photo_url")
    space_type = data.get("space_type", "desk")
    category = data.get("category", "commercial")
    amenities = data.get("amenities", [])

    scan_result = SpaceAIAdapter.scan_space(
        photo_url=photo_url,
        space_type=space_type,
        category=category,
        amenities=amenities,
    )

    return jsonify({
        "success": True,
        "data": scan_result,
    }), 200


@spaces_bp.route("/assist-listing", methods=["POST"])
def assist_listing():
    """AI endpoint adapter: generates optimized listing descriptions, smart pricing, and rules."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    title = data.get("title")
    space_type = data.get("space_type", "desk")
    neighborhood = data.get("neighborhood")
    city = data.get("city")
    amenities = data.get("amenities", [])

    assist_result = SpaceAIAdapter.assist_listing(
        title=title,
        space_type=space_type,
        neighborhood=neighborhood,
        city=city,
        amenities=amenities,
    )

    return jsonify({
        "success": True,
        "data": assist_result,
    }), 200


@spaces_bp.route("/search", methods=["POST", "GET"])
def search_spaces():
    """Six-stage hybrid discovery pipeline: NLP parsing, constraints, SQL filters, availability, vector/keyword similarity, and composite ranking."""
    if request.method == "POST":
        payload: dict[str, Any] = request.get_json(silent=True) or {}
        query = payload.get("query")
        date = payload.get("date")
        hours = payload.get("hours")
        budget = payload.get("budget") or payload.get("max_price")
        location = payload.get("location")
        page = max(1, int(payload.get("page", 1)))
        limit = min(100, max(1, int(payload.get("limit", 20))))
        require_available = bool(payload.get("require_available", False))
    else:
        query = request.args.get("query") or request.args.get("q")
        date = request.args.get("date")
        hours = request.args.get("hours")
        budget = request.args.get("budget") or request.args.get("max_price")
        location = request.args.get("location")
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 20))))
        require_available = request.args.get("require_available", "").lower() in ("true", "1")

    result = DiscoveryPipeline.search(
        query=query,
        date=date,
        hours=hours,
        budget=budget,
        location=location,
        page=page,
        limit=limit,
        require_available=require_available,
    )

    return jsonify({
        "success": True,
        "spaces": result["items"],
        "matches": result["items"],
        "items": result["items"],
        "data": result,
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
        "total_pages": result["total_pages"],
        "parsed_constraints": result.get("parsed_constraints", {}),
    }), 200


@spaces_bp.route("/ai-match", methods=["POST"])
def ai_match():
    """AI space recommendation and natural language match explanation."""
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    query = payload.get("query")
    date = payload.get("date")
    hours = payload.get("hours")
    budget = payload.get("budget") or payload.get("max_price")
    location = payload.get("location")
    top_k = min(50, max(1, int(payload.get("top_k", 5))))

    match_result = AIMatcher.match(
        query=query,
        date=date,
        hours=hours,
        budget=budget,
        location=location,
        top_k=top_k,
    )

    return jsonify({
        "success": True,
        "spaces": match_result["top_matches"],
        "matches": match_result["top_matches"],
        "top_matches": match_result["top_matches"],
        "explanation": match_result["match_explanation"],
        "match_explanation": match_result["match_explanation"],
        "data": match_result,
        "total": match_result.get("total_matches", len(match_result["top_matches"])),
    }), 200

