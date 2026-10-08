"""SpaceLoop Enterprise Application Factory Bootstrap."""
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from flask import Flask, abort, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

# Ensure backend directory and repo root are in sys.path
BOOTSTRAP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BOOTSTRAP_DIR.parent.parent
REPO_ROOT = BACKEND_DIR.parent
for path in (str(BACKEND_DIR), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from backend.core.cors import init_cors
from backend.core.database import check_database_health, db, init_db

try:
    from backend.app.config import BaseConfig, get_config
except ImportError:
    try:
        from backend.config import BaseConfig, get_config
    except ImportError:
        from config import BaseConfig, get_config


def configure_logging(app: Flask) -> None:
    """Configure structured logging for SpaceLoop."""
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    )


def register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers for consistent API error contracts across all supported languages."""
    from backend.modules.i18n.middleware import get_request_language
    from backend.modules.i18n.lexicon import localize_error

    @app.errorhandler(400)
    def handle_bad_request(err: Any):
        lang = get_request_language()
        loc_msg = localize_error("BAD_REQUEST", lang)
        default_desc = str(getattr(err, "description", "Malformed request payload"))
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "BAD_REQUEST",
                    "message": loc_msg if lang != "en" else default_desc,
                    "localized_message": loc_msg,
                    "language": lang,
                },
            }),
            400,
        )

    @app.errorhandler(401)
    def handle_unauthorized(err: Any):
        lang = get_request_language()
        loc_msg = localize_error("UNAUTHORIZED", lang)
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": loc_msg if lang != "en" else "Authentication required to access this resource.",
                    "localized_message": loc_msg,
                    "language": lang,
                },
            }),
            401,
        )

    @app.errorhandler(403)
    def handle_forbidden(err: Any):
        lang = get_request_language()
        loc_msg = localize_error("FORBIDDEN", lang)
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": loc_msg if lang != "en" else "You do not have permission to perform this action.",
                    "localized_message": loc_msg,
                    "language": lang,
                },
            }),
            403,
        )

    @app.errorhandler(404)
    def handle_not_found(err: Any):
        if request.path.startswith("/api/"):
            lang = get_request_language()
            loc_msg = localize_error("NOT_FOUND", lang)
            return (
                jsonify({
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": loc_msg if lang != "en" else f"Resource not found: {request.path}",
                        "localized_message": loc_msg,
                        "language": lang,
                    },
                }),
                404,
            )
        # For non-API requests, let SPA routing fallback handle it
        dist_dir = find_frontend_dist_dir(app)
        if dist_dir:
            index_path = os.path.join(dist_dir, "index.html")
            if os.path.exists(index_path):
                return send_from_directory(dist_dir, "index.html")
        lang = get_request_language()
        loc_msg = localize_error("NOT_FOUND", lang)
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": loc_msg if lang != "en" else f"Endpoint not found: {request.path}",
                    "localized_message": loc_msg,
                    "language": lang,
                },
            }),
            404,
        )

    @app.errorhandler(409)
    def handle_conflict(err: Any):
        lang = get_request_language()
        loc_msg = localize_error("CONFLICT", lang)
        default_desc = str(getattr(err, "description", "Resource state conflict"))
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "CONFLICT",
                    "message": loc_msg if lang != "en" else default_desc,
                    "localized_message": loc_msg,
                    "language": lang,
                },
            }),
            409,
        )

    @app.errorhandler(422)
    def handle_unprocessable_entity(err: Any):
        lang = get_request_language()
        loc_msg = localize_error("VALIDATION_ERROR", lang)
        default_desc = str(getattr(err, "description", "Unprocessable entity"))
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": loc_msg if lang != "en" else default_desc,
                    "localized_message": loc_msg,
                    "language": lang,
                },
            }),
            422,
        )

    @app.errorhandler(429)
    def handle_rate_limit(err: Any):
        lang = get_request_language()
        loc_msg = localize_error("RATE_LIMIT_EXCEEDED", lang)
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": loc_msg if lang != "en" else "Too many requests. Please slow down.",
                    "localized_message": loc_msg,
                    "language": lang,
                },
            }),
            429,
        )

    @app.errorhandler(500)
    def handle_internal_error(err: Any):
        app.logger.error(f"Internal server error: {err}", exc_info=True)
        lang = get_request_language()
        loc_msg = localize_error("INTERNAL_SERVER_ERROR", lang)
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": loc_msg if lang != "en" else "An internal server error occurred.",
                    "localized_message": loc_msg,
                    "language": lang,
                },
            }),
            500,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        code = err.name.upper().replace(" ", "_") if getattr(err, "name", None) else f"HTTP_{err.code}"
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": code,
                    "message": err.description or "HTTP error occurred",
                },
            }),
            err.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(err: Exception):
        app.logger.error(f"Unhandled system error: {err}", exc_info=True)
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "An unexpected error occurred processing your request.",
                },
            }),
            500,
        )


def find_frontend_dist_dir(app: Flask) -> str | None:
    """Resolve the canonical frontend production distribution directory."""
    candidates = [
        # Canonical monorepo frontend location
        os.path.abspath(os.path.join(REPO_ROOT, "frontend", "dist")),
        os.path.abspath(os.path.join(BACKEND_DIR, "..", "frontend", "dist")),
        os.path.abspath(os.path.join(app.root_path, "frontend", "dist")),
        os.path.abspath(os.path.join(app.root_path, "..", "frontend", "dist")),
        # Fallback to local dist directory if built in root or backend
        os.path.abspath(os.path.join(app.root_path, "dist")),
        os.path.abspath(os.path.join(REPO_ROOT, "dist")),
    ]
    for candidate in candidates:
        if os.path.exists(os.path.join(candidate, "index.html")):
            return candidate
    return None


def register_system_routes(app: Flask) -> None:
    """Register core platform routes including health, diagnostic checks, and SPA serving."""

    @app.route("/health", methods=["GET"])
    @app.route("/api/v1/health", methods=["GET"])
    def health_check():
        db_health = check_database_health()
        overall_healthy = db_health.get("status") == "connected"
        status_code = 200 if overall_healthy else 503

        return (
            jsonify({
                "success": overall_healthy,
                "service": "SpaceLoop API",
                "version": "1.0.0",
                "environment": os.getenv("FLASK_ENV", "development"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database": db_health,
            }),
            status_code,
        )

    @app.route("/", methods=["GET"])
    def root():
        dist_dir = find_frontend_dist_dir(app)
        accept_header = request.headers.get("Accept", "")
        if dist_dir and ("text/html" in accept_header or "*/*" in accept_header):
            index_path = os.path.join(dist_dir, "index.html")
            if os.path.exists(index_path):
                return send_from_directory(dist_dir, "index.html")
        return jsonify({
            "name": "SpaceLoop API",
            "tagline": "Peer-to-peer physical space marketplace for India",
            "documentation": "/api/v1/health",
            "version": "1.0.0",
        })

    @app.route("/<path:path>", methods=["GET"])
    def serve_frontend_assets(path):
        # Do not intercept API, uploads, or health endpoints
        if path.startswith("api/") or path.startswith("uploads/") or path in ("health", "api/v1/health"):
            abort(404)

        dist_dir = find_frontend_dist_dir(app)
        if not dist_dir:
            abort(404)

        # Check for static file match (JS, CSS, images, etc.)
        file_path = os.path.join(dist_dir, path)
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            return send_from_directory(dist_dir, path)

        # SPA client-side routing fallback for browser reloads
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_file):
            return send_from_directory(dist_dir, "index.html")

        abort(404)


def register_cli_commands(app: Flask) -> None:
    """Register Flask CLI commands for database setup and seeding."""

    @app.cli.command("init-db")
    def init_db_command():
        """Initialize all database tables."""
        init_db(app)
        print("SpaceLoop database tables created successfully.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Ensure SpaceLoop demo accounts exist with valid credentials."""
        try:
            from backend.seed_data import ensure_demo_accounts
        except ImportError:
            from seed_data import ensure_demo_accounts
        init_db(app)
        report = ensure_demo_accounts(app)
        print(f"SpaceLoop demo accounts ensured: {report}")

    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed initial users, spaces, bookings, and reviews."""
        try:
            from backend.seed_data import ensure_demo_accounts, seed_all
        except ImportError:
            from seed_data import ensure_demo_accounts, seed_all
        init_db(app)
        ensure_demo_accounts(app)
        counts = seed_all(app)
        print(f"SpaceLoop database seeded: {counts}")


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    """SpaceLoop Application Factory."""
    # Base directory is workspace root
    base_dir = str(REPO_ROOT)
    app = Flask(__name__, root_path=base_dir)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Logging
    configure_logging(app)

    # Apply ProxyFix middleware if configured (e.g. running behind NGINX, ALB, or Traefik)
    if app.config.get("ENABLE_PROXY_FIX"):
        num_proxies = app.config.get("NUM_PROXIES", 1)
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=num_proxies,
            x_proto=num_proxies,
            x_host=num_proxies,
            x_prefix=num_proxies,
        )

    # Initialize extensions
    db.init_app(app)
    init_cors(app)

    # Session & User context loader
    from backend.modules.auth.session import init_session_context
    init_session_context(app)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' https:;"
        if app.config.get("ENV") == "production" or not app.config.get("DEBUG"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Import blueprints from canonical API layout
    from backend.app.api.v1.access import access_bp
    from backend.app.api.v1.admin import admin_bp
    from backend.app.api.v1.ai import _handle_chat_request, ai_bp
    from backend.app.api.v1.auth import auth_bp
    from backend.app.api.v1.bookings import bookings_bp
    from backend.app.api.v1.calculator import calculator_bp
    from backend.app.api.v1.escrow import escrow_bp
    from backend.app.api.v1.fraud import fraud_bp
    from backend.app.api.v1.loopbot import handle_loopbot_chat_request, loopbot_bp
    from backend.app.api.v1.search import search_bp
    from backend.app.api.v1.spaces import spaces_bp
    from backend.app.api.v1.system import system_bp
    from backend.app.api.v1.trust import trust_bp
    from backend.app.api.v1.trust_safety import trust_safety_bp
    from backend.app.api.v1.verification import verification_bp
    from backend.app.api.v1.sessions import sessions_bp
    from backend.app.api.v1.calculator import calculator_bp
    from backend.app.api.v1.leases import leases_bp
    from backend.app.api.v1.hosts import hosts_bp, get_host_dashboard
    from backend.modules.spaces.photo_service import UPLOAD_FOLDER

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(auth_bp, url_prefix="/api/auth", name="auth_legacy")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin", name="admin_v1")
    app.register_blueprint(spaces_bp, url_prefix="/api/spaces")
    app.register_blueprint(spaces_bp, url_prefix="/api/v1/spaces", name="spaces_v1")
    app.register_blueprint(bookings_bp, url_prefix="/api/bookings")
    app.register_blueprint(bookings_bp, url_prefix="/api/v1/bookings", name="bookings_v1")
    app.register_blueprint(bookings_bp, url_prefix="/api/booking", name="booking_singular")
    app.register_blueprint(bookings_bp, url_prefix="/api/v1/booking", name="booking_v1_singular")
    app.register_blueprint(calculator_bp, url_prefix="/api/calculator")
    app.register_blueprint(calculator_bp, url_prefix="/api/v1/calculator", name="calculator_v1")
    app.register_blueprint(system_bp, url_prefix="/api/system")
    app.register_blueprint(system_bp, url_prefix="/api/v1/system", name="system_v1")
    app.register_blueprint(trust_bp, url_prefix="/api/trust")
    app.register_blueprint(trust_bp, url_prefix="/api/v1/trust", name="trust_v1")
    app.register_blueprint(escrow_bp, url_prefix="/api/escrow")
    app.register_blueprint(escrow_bp, url_prefix="/api/v1/escrow", name="escrow_v1")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(ai_bp, url_prefix="/api/v1/ai", name="ai_v1")
    app.register_blueprint(loopbot_bp, url_prefix="/api/v1/loopbot")
    app.register_blueprint(loopbot_bp, url_prefix="/api/loopbot", name="loopbot_legacy")
    app.register_blueprint(loopbot_bp, url_prefix="/api/v1/loop", name="loop_v1")
    app.register_blueprint(loopbot_bp, url_prefix="/api/loop", name="loop_legacy")
    app.register_blueprint(trust_safety_bp, url_prefix="/api/v1/trust-safety")
    app.register_blueprint(trust_safety_bp, url_prefix="/api/trust-safety", name="trust_safety_legacy")
    app.register_blueprint(fraud_bp, url_prefix="/api/fraud")
    app.register_blueprint(fraud_bp, url_prefix="/api/v1/fraud", name="fraud_v1")
    app.register_blueprint(verification_bp, url_prefix="/api/verify")
    app.register_blueprint(verification_bp, url_prefix="/api/v1/verify", name="verify_v1")
    app.register_blueprint(verification_bp, url_prefix="/api/v1/verification", name="verification_canonical")
    app.register_blueprint(access_bp, url_prefix="/api/access")
    app.register_blueprint(access_bp, url_prefix="/api/v1/access", name="access_v1")
    app.register_blueprint(search_bp, url_prefix="/api/v1/search")
    app.register_blueprint(search_bp, url_prefix="/api/search", name="search_legacy")
    app.register_blueprint(sessions_bp, url_prefix="/api/v1/sessions")
    app.register_blueprint(sessions_bp, url_prefix="/api/sessions", name="sessions_legacy")
    app.register_blueprint(leases_bp, url_prefix="/api/v1/leases")
    app.register_blueprint(leases_bp, url_prefix="/api/leases", name="leases_legacy")
    app.register_blueprint(hosts_bp, url_prefix="/api/v1/hosts")
    app.register_blueprint(hosts_bp, url_prefix="/api/host", name="host_legacy")
    app.register_blueprint(hosts_bp, url_prefix="/api/hosts", name="hosts_legacy")

    # Direct routes for Host Dashboard
    app.add_url_rule("/api/dashboard", "api_dashboard_direct", get_host_dashboard, methods=["GET"])


    # Direct routes for LoopBot conversational endpoints
    app.add_url_rule("/api/assistant", "api_assistant", _handle_chat_request, methods=["POST"])
    app.add_url_rule("/api/v1/assistant", "api_v1_assistant", _handle_chat_request, methods=["POST"])
    app.add_url_rule("/api/concierge/chat", "api_concierge_chat", _handle_chat_request, methods=["POST"])
    app.add_url_rule("/api/v1/concierge/chat", "api_v1_concierge_chat", _handle_chat_request, methods=["POST"])
    app.add_url_rule("/api/nlp/dispatch", "api_nlp_dispatch", _handle_chat_request, methods=["POST"])
    app.add_url_rule("/api/v1/nlp/dispatch", "api_v1_nlp_dispatch", _handle_chat_request, methods=["POST"])

    @app.route("/uploads/<path:filename>", methods=["GET"])
    def uploaded_file(filename):
        return send_from_directory(UPLOAD_FOLDER, filename)

    # Register error handlers, system routes, CLI commands
    register_error_handlers(app)
    register_system_routes(app)
    register_cli_commands(app)

    # Auto-initialize database tables and demo accounts (idempotent)
    if not app.config.get("TESTING"):
        with app.app_context():
            try:
                from backend.app.persistence.models import Space
                db.create_all()
                try:
                    try:
                        from backend.seed_data import ensure_demo_accounts, seed_all
                    except ImportError:
                        from seed_data import ensure_demo_accounts, seed_all
                    ensure_demo_accounts(app)
                    if Space.query.count() == 0:
                        seed_all(app)
                except Exception as seed_err:
                    app.logger.info(f"Seed/demo data check: {seed_err}")
            except Exception as db_err:
                app.logger.warning(f"Database schema initialization deferred: {db_err}")

    return app


# Default application instance for WSGI servers
_default_app = None


def get_default_app():
    global _default_app
    if _default_app is None:
        _default_app = create_app()
    return _default_app


class _LazyApp:
    def __getattr__(self, name):
        return getattr(get_default_app(), name)

    def __call__(self, *args, **kwargs):
        return get_default_app()(*args, **kwargs)


app = _LazyApp()

