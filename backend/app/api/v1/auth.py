from typing import Any
from flask import Blueprint, current_app, g, jsonify, make_response, request

from backend.modules.auth.permissions import get_role_permissions, require_auth
from backend.modules.auth.service import AuthService
from backend.modules.auth.session import clear_auth_cookies, set_auth_cookies

auth_bp = Blueprint("auth", __name__)


def is_production() -> bool:
    """Check if current Flask environment is configured as production."""
    if current_app.config.get("TESTING") or current_app.config.get("DEBUG"):
        return False
    return current_app.config.get("ENV") == "production"


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    full_name = data.get("full_name", "")
    phone = data.get("phone")
    role = data.get("role", "seeker")

    result, err, status = AuthService.register_user(
        email=email,
        password=password,
        full_name=full_name,
        phone=phone,
        role=role,
    )

    if err or not result:
        return jsonify({"success": False, "error": {"code": "REGISTRATION_FAILED", "message": err}}), status

    response = make_response(jsonify({
        "success": True,
        "data": result,
        "message": "Account created successfully.",
    }), 201)

    set_auth_cookies(response, result["access_token"], is_secure=is_production())
    return response


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user with credentials, returning session token or MFA challenge."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    device_name = data.get("device_name")

    result, err, status = AuthService.login_user(
        email=email,
        password=password,
        device_name=device_name,
    )

    if err or not result:
        return jsonify({"success": False, "error": {"code": "LOGIN_FAILED", "message": err}}), status

    # If MFA is required, return challenge token without setting session cookie
    if result.get("mfa_required"):
        return jsonify({
            "success": True,
            "data": result,
            "message": "Two-factor challenge required.",
        }), 200

    response = make_response(jsonify({
        "success": True,
        "data": result,
        "message": "Login successful.",
    }), 200)

    set_auth_cookies(response, result["access_token"], is_secure=is_production())
    return response


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    """Invalidate current active session and clear HTTP-only cookies."""
    AuthService.logout_user(g.current_user)
    response = make_response(jsonify({
        "success": True,
        "message": "Logged out successfully.",
    }), 200)

    clear_auth_cookies(response)
    return response


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user():
    """Retrieve profile and permissions for the currently authenticated user."""
    user = g.current_user
    active_role = (user.active_context_role or user.role).lower()
    permissions = list(sorted(get_role_permissions(active_role)))

    return jsonify({
        "success": True,
        "data": {
            **user.to_dict(),
            "active_role": active_role,
            "permissions": permissions,
        },
    }), 200


@auth_bp.route("/context", methods=["POST"])
@require_auth
def switch_context():
    """Switch active operational context persona (e.g. seeker vs host)."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    new_role = data.get("role", "")

    result, err, status = AuthService.switch_context(g.current_user, new_role)
    if err or not result:
        return jsonify({"success": False, "error": {"code": "CONTEXT_SWITCH_FAILED", "message": err}}), status

    response = make_response(jsonify({
        "success": True,
        "data": result,
        "message": f"Context switched to '{result['active_role']}'.",
    }), 200)

    set_auth_cookies(response, result["access_token"], is_secure=is_production())
    return response


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Initiate password reset request."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    email = data.get("email", "")

    msg, raw_token = AuthService.request_password_reset(email)
    payload = {"message": msg}
    if current_app.config.get("TESTING") and raw_token:
        payload["dev_reset_token"] = raw_token

    return jsonify({
        "success": True,
        "data": payload,
    }), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Finalize password reset using provided token."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    token = data.get("token", "")
    new_password = data.get("new_password", "")

    ok, msg, status = AuthService.reset_password(token, new_password)
    if not ok:
        return jsonify({"success": False, "error": {"code": "RESET_FAILED", "message": msg}}), status

    return jsonify({
        "success": True,
        "message": msg,
    }), 200


@auth_bp.route("/mfa/setup", methods=["POST"])
@require_auth
def mfa_setup():
    """Generate TOTP secret and backup recovery codes."""
    setup_data = AuthService.setup_mfa(g.current_user)
    return jsonify({
        "success": True,
        "data": setup_data,
    }), 200


@auth_bp.route("/mfa/verify-setup", methods=["POST"])
@require_auth
def mfa_verify_setup():
    """Confirm TOTP code to finalize 2FA activation."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    code = data.get("code", "")

    ok, msg, status = AuthService.verify_mfa_setup(g.current_user, code)
    if not ok:
        return jsonify({"success": False, "error": {"code": "MFA_SETUP_FAILED", "message": msg}}), status

    return jsonify({
        "success": True,
        "message": msg,
    }), 200


@auth_bp.route("/mfa/verify", methods=["POST"])
def mfa_verify_challenge():
    """Complete login challenge using TOTP code or recovery code."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    mfa_token = data.get("mfa_token", "")
    code = data.get("code")
    recovery_code = data.get("recovery_code")
    device_name = data.get("device_name")

    result, err, status = AuthService.verify_mfa_challenge(
        mfa_token=mfa_token,
        code=code,
        recovery_code=recovery_code,
        device_name=device_name,
    )

    if err or not result:
        return jsonify({"success": False, "error": {"code": "MFA_VERIFICATION_FAILED", "message": err}}), status

    response = make_response(jsonify({
        "success": True,
        "data": result,
        "message": "Two-factor authentication successful.",
    }), 200)

    set_auth_cookies(response, result["access_token"], is_secure=is_production())
    return response


@auth_bp.route("/mfa/disable", methods=["POST"])
@require_auth
def mfa_disable():
    """Disable 2FA after password and second factor verification."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    password = data.get("password", "")
    code = data.get("code")
    recovery_code = data.get("recovery_code")

    ok, msg, status = AuthService.disable_mfa(
        user=g.current_user,
        password=password,
        code=code,
        recovery_code=recovery_code,
    )

    if not ok:
        return jsonify({"success": False, "error": {"code": "MFA_DISABLE_FAILED", "message": msg}}), status

    return jsonify({
        "success": True,
        "message": msg,
    }), 200


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    """Resend email verification token."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    email = data.get("email", "")

    msg, raw_token = AuthService.resend_verification_email(email)
    payload = {"message": msg}
    if current_app.config.get("TESTING") and raw_token:
        payload["dev_verification_token"] = raw_token

    return jsonify({
        "success": True,
        "data": payload,
    }), 200


@auth_bp.route("/instant-verify", methods=["POST"])
@require_auth
def instant_verify():
    """Instant verification endpoint for development, testing, and verified onboarding."""
    AuthService.instant_verify_user(g.current_user)
    return jsonify({
        "success": True,
        "data": g.current_user.to_dict(),
        "message": "Account has been verified.",
    }), 200


@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    """Verify email address via token (supports GET query parameter or POST JSON body)."""
    if request.method == "GET":
        token = request.args.get("token", "")
    else:
        data: dict[str, Any] = request.get_json(silent=True) or {}
        token = data.get("token", "")

    ok, msg, status = AuthService.verify_email(token)
    if not ok:
        return jsonify({"success": False, "error": {"code": "VERIFICATION_FAILED", "message": msg}}), status

    return jsonify({
        "success": True,
        "message": msg,
    }), 200
