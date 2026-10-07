"""API Routes for External Verification Adapters.

Endpoints:
- POST /api/verify/student: Student enrollment status & 15% discount rate
- POST /api/verify/host: DISCOM utility bill + UPI penny-drop host verification
- POST /api/verify/aadhaar: Aadhaar tokenization & privacy-preserving verification
"""

import logging
from flask import Blueprint, current_app, g, jsonify, request

from backend.modules.auth.session import resolve_authenticated_user
from backend.modules.verification.service import VerificationService

logger = logging.getLogger("spaceloop.api.verification")

verification_bp = Blueprint("verification", __name__)


def _resolve_target_user_id(payload: dict) -> int | None:
    """Resolve target user securely to prevent IDOR vulnerabilities.
    - Authenticated regular users can only verify themselves.
    - Authenticated admins can specify target user_id.
    - In TESTING mode, user_id can be passed directly to facilitate unit testing.
    """
    current_user = getattr(g, "current_user", None) or resolve_authenticated_user()
    is_testing = bool(current_app and current_app.config.get("TESTING"))

    if current_user:
        is_admin = getattr(current_user, "role", "").lower() == "admin"
        if is_admin and payload.get("user_id"):
            try:
                return int(payload.get("user_id"))
            except (ValueError, TypeError):
                return current_user.id
        return current_user.id

    if is_testing and payload.get("user_id"):
        try:
            return int(payload.get("user_id"))
        except (ValueError, TypeError):
            return None

    return None


@verification_bp.route("/student", methods=["POST"])
def verify_student():
    """Verify student enrollment status and grant 15% discount rate.

    Request Body:
    {
      "student_id": "STU-2026-9901",
      "university_email": "student@iitb.ac.in",
      "user_id": 123 (optional if authenticated)
    }
    """
    payload = request.get_json() or {}
    student_id = payload.get("student_id")
    university_email = payload.get("university_email")

    if not student_id or not university_email:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_REQUIRED_FIELDS",
                "message": "Both 'student_id' and 'university_email' are required.",
            },
        }), 400

    target_user_id = _resolve_target_user_id(payload)

    try:
        result = VerificationService.verify_student(
            user_id=target_user_id,
            student_id=student_id,
            university_email=university_email,
            context=payload,
        )

        if not result.get("student_verified"):
            return jsonify({
                "success": False,
                "error": {
                    "code": "STUDENT_VERIFICATION_FAILED",
                    "message": result.get("error", "Student verification failed."),
                    "verification_mode": result.get("verification_mode"),
                    "external_verified": result.get("external_verified"),
                },
            }), 422

        return jsonify({
            "success": True,
            "data": result,
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e),
            },
        }), 400
    except Exception as e:
        logger.error(f"Student verification error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred during student verification.",
            },
        }), 500


@verification_bp.route("/host", methods=["POST"])
def verify_host():
    """Verify host electricity connection and UPI payout beneficiary name.

    Request Body:
    {
      "discom_consumer_no": "1029384756",
      "discom_provider": "Adani Electricity Mumbai",
      "upi_vpa": "host@okhdfcbank",
      "user_id": 123 (optional if authenticated)
    }
    """
    payload = request.get_json() or {}
    discom_consumer_no = payload.get("discom_consumer_no") or payload.get("consumer_number")
    discom_provider = payload.get("discom_provider") or payload.get("provider")
    upi_vpa = payload.get("upi_vpa") or payload.get("vpa")

    if not discom_consumer_no or not discom_provider or not upi_vpa:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_REQUIRED_FIELDS",
                "message": "'discom_consumer_no', 'discom_provider', and 'upi_vpa' are all required.",
            },
        }), 400

    target_user_id = _resolve_target_user_id(payload)

    try:
        result = VerificationService.verify_host(
            user_id=target_user_id,
            discom_consumer_no=discom_consumer_no,
            discom_provider=discom_provider,
            upi_vpa=upi_vpa,
            context=payload,
        )

        if not result.get("host_verified"):
            return jsonify({
                "success": False,
                "error": {
                    "code": "HOST_VERIFICATION_FAILED",
                    "message": result.get("error", "Host verification failed."),
                    "discom_verified": result.get("discom_verified"),
                    "upi_verified": result.get("upi_verified"),
                    "verification_mode": result.get("verification_mode"),
                    "external_verified": result.get("external_verified"),
                },
            }), 422

        return jsonify({
            "success": True,
            "data": result,
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e),
            },
        }), 400
    except Exception as e:
        logger.error(f"Host verification error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred during host verification.",
            },
        }), 500


@verification_bp.route("/aadhaar", methods=["POST"])
def verify_aadhaar():
    """Verify Aadhaar identity via SHA-256 tokenization (zero raw storage).

    Request Body:
    {
      "aadhaar_number": "123456789012",
      "user_id": 123 (optional if authenticated)
    }
    """
    payload = request.get_json() or {}
    aadhaar_number = payload.get("aadhaar_number") or payload.get("aadhaar")

    if not aadhaar_number:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_REQUIRED_FIELDS",
                "message": "'aadhaar_number' is required.",
            },
        }), 400

    target_user_id = _resolve_target_user_id(payload)

    try:
        result = VerificationService.verify_aadhaar(
            user_id=target_user_id,
            raw_aadhaar=str(aadhaar_number),
            context=payload,
        )

        if not result.get("aadhaar_verified"):
            return jsonify({
                "success": False,
                "error": {
                    "code": "AADHAAR_VERIFICATION_FAILED",
                    "message": result.get("error", "Aadhaar verification failed."),
                    "verification_mode": result.get("verification_mode"),
                    "external_verified": result.get("external_verified"),
                },
            }), 422

        return jsonify({
            "success": True,
            "data": result,
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e),
            },
        }), 400
    except Exception as e:
        logger.error(f"Aadhaar verification error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred during Aadhaar verification.",
            },
        }), 500
