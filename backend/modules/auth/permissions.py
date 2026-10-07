from collections.abc import Callable
from functools import wraps
from typing import Any
from flask import g, jsonify


ROLE_SEEKER = "seeker"
ROLE_HOST = "host"
ROLE_ADMIN = "admin"

ALL_ROLES = {ROLE_SEEKER, ROLE_HOST, ROLE_ADMIN}

# Permission sets mapped by role (Role-Based & Permission-Based Access Control)
ROLE_PERMISSIONS: dict[str, set[str]] = {
    ROLE_SEEKER: {
        "space:view",
        "space:search",
        "booking:create",
        "booking:view_own",
        "booking:cancel_own",
        "review:create",
        "inquiry:create",
        "access:check_in",
        "access:check_out",
    },
    ROLE_HOST: {
        "space:view",
        "space:search",
        "space:create",
        "space:update_own",
        "space:delete_own",
        "booking:view_host",
        "review:reply",
        "inquiry:reply",
        "escrow:view_own",
        "access:check_in",
        "access:check_out",
    },
    ROLE_ADMIN: {
        "*",  # Super-admin wildcard
        "admin:all",
        "space:approve",
        "space:delete_any",
        "booking:view_any",
        "escrow:override",
        "fraud:review",
        "user:manage",
        "audit:view",
    },
}


def normalize_role(role: str | None) -> str:
    """Normalize role strings, converting legacy aliases like 'guest' to 'seeker'."""
    if not role:
        return ROLE_SEEKER
    clean = role.strip().lower()
    if clean in ("guest", "seeker"):
        return ROLE_SEEKER
    if clean == "host":
        return ROLE_HOST
    if clean == "admin":
        return ROLE_ADMIN
    return ROLE_SEEKER


def get_role_permissions(role: str) -> set[str]:
    """Retrieve full permission set associated with a role."""
    norm = normalize_role(role)
    return ROLE_PERMISSIONS.get(norm, set())


def has_permission(role: str, permission: str) -> bool:
    """Check if a given role is granted a specific permission."""
    norm = normalize_role(role)
    perms = ROLE_PERMISSIONS.get(norm, set())
    if "*" in perms or "admin:all" in perms:
        return True
    return permission in perms


def require_auth(f: Callable) -> Callable:
    """Decorator ensuring that an authenticated user is present in the request context."""
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        current_user = getattr(g, "current_user", None)
        if not current_user:
            return (
                jsonify({
                    "success": False,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required. Please log in or provide a valid access token.",
                    },
                }),
                401,
            )
        if not current_user.is_active:
            return (
                jsonify({
                    "success": False,
                    "error": {
                        "code": "ACCOUNT_DISABLED",
                        "message": "This account has been deactivated. Please contact support.",
                    },
                }),
                403,
            )
        return f(*args, **kwargs)
    return decorated


def require_role(*allowed_roles: str) -> Callable:
    """Decorator requiring the authenticated user to hold one of the specified roles."""
    normalized_allowed = {normalize_role(r) for r in allowed_roles}

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            current_user = getattr(g, "current_user", None)
            if not current_user:
                return (
                    jsonify({
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Authentication required.",
                        },
                    }),
                    401,
                )

            user_role = normalize_role(current_user.role)
            active_role = normalize_role(current_user.active_context_role or user_role)

            # Admins always have access
            if user_role == ROLE_ADMIN or active_role == ROLE_ADMIN:
                return f(*args, **kwargs)

            if user_role not in normalized_allowed and active_role not in normalized_allowed:
                return (
                    jsonify({
                        "success": False,
                        "error": {
                            "code": "FORBIDDEN",
                            "message": f"Access forbidden. Required role: {', '.join(sorted(normalized_allowed))}",
                        },
                    }),
                    403,
                )
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_permission(*required_permissions: str) -> Callable:
    """Decorator verifying that the authenticated user possesses the specified permissions."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            current_user = getattr(g, "current_user", None)
            if not current_user:
                return (
                    jsonify({
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Authentication required.",
                        },
                    }),
                    401,
                )

            effective_role = normalize_role(current_user.active_context_role or current_user.role)

            for perm in required_permissions:
                if not has_permission(effective_role, perm):
                    return (
                        jsonify({
                            "success": False,
                            "error": {
                                "code": "FORBIDDEN",
                                "message": f"Missing required permission: '{perm}'.",
                            },
                        }),
                        403,
                    )
            return f(*args, **kwargs)
        return decorated
    return decorator
