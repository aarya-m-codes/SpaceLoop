import logging
import os
from datetime import datetime, timezone
from typing import Any
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.core.cors import init_cors
from backend.core.database import check_database_health, db, init_db
from config import BaseConfig, get_config


def configure_logging(app: Flask) -> None:
    """Configure structured logging for SpaceLoop."""
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    )


def register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers for consistent API error contracts."""

    @app.errorhandler(400)
    def handle_bad_request(err: Any):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "BAD_REQUEST",
                    "message": getattr(err, "description", "The request payload was invalid or malformed."),
                },
            }),
            400,
        )

    @app.errorhandler(401)
    def handle_unauthorized(err: Any):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": getattr(err, "description", "Authentication credentials are required or invalid."),
                },
            }),
            401,
        )

    @app.errorhandler(403)
    def handle_forbidden(err: Any):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": getattr(err, "description", "You do not have permission to access this resource."),
                },
            }),
            403,
        )

    @app.errorhandler(404)
    def handle_not_found(err: Any):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": getattr(err, "description", "The requested resource was not found."),
                },
            }),
            404,
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(err: Any):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": getattr(err, "description", f"Method {request.method} is not allowed on this endpoint."),
                },
            }),
            405,
        )

    @app.errorhandler(409)
    def handle_conflict(err: Any):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "CONFLICT",
                    "message": getattr(err, "description", "A conflicting resource or booking slot already exists."),
                },
            }),
            409,
        )

    @app.errorhandler(422)
    def handle_unprocessable(err: Any):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "UNPROCESSABLE_ENTITY",
                    "message": getattr(err, "description", "The request was well-formed but could not be processed."),
                },
            }),
            422,
        )

    @app.errorhandler(500)
    def handle_internal_error(err: Any):
        app.logger.error(f"Internal server error: {err}", exc_info=True)
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please try again later.",
                },
            }),
            500,
        )

    @app.errorhandler(HTTPException)
    def handle_generic_http_exception(err: HTTPException):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": err.name.upper().replace(" ", "_"),
                    "message": err.description,
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


def register_system_routes(app: Flask) -> None:
    """Register core platform routes including health and diagnostic checks."""

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
        return jsonify({
            "name": "SpaceLoop API",
            "tagline": "Peer-to-peer physical space marketplace for India",
            "documentation": "/api/v1/health",
            "version": "1.0.0",
        })


def register_cli_commands(app: Flask) -> None:
    """Register Flask CLI commands for database setup and seeding."""

    @app.cli.command("init-db")
    def init_db_command():
        """Initialize all database tables."""
        init_db(app)
        print("SpaceLoop database tables created successfully.")

    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed initial users, spaces, bookings, and reviews."""
        from seed_data import seed_all
        init_db(app)
        counts = seed_all(app)
        print(f"SpaceLoop database seeded: {counts}")


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    """SpaceLoop Application Factory."""
    app = Flask(__name__)

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
            x_port=num_proxies,
            x_prefix=num_proxies,
        )

    # Initialize extensions
    db.init_app(app)
    init_cors(app)

    # Session & User context loader
    from backend.modules.auth.session import init_session_context
    init_session_context(app)

    # Attach production security headers
    @app.after_request
    def attach_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' https:;"
        if app.config.get("ENV") == "production" or not app.config.get("DEBUG"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Register API blueprints
    from backend.app.api.v1.auth import auth_bp
    from backend.app.api.v1.bookings import bookings_bp
    from backend.app.api.v1.escrow import escrow_bp
    from backend.app.api.v1.spaces import spaces_bp
    from backend.modules.spaces.photo_service import UPLOAD_FOLDER
    from flask import send_from_directory

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(spaces_bp, url_prefix="/api/spaces")
    app.register_blueprint(spaces_bp, url_prefix="/api/v1/spaces", name="spaces_v1")
    app.register_blueprint(bookings_bp, url_prefix="/api/bookings")
    app.register_blueprint(bookings_bp, url_prefix="/api/v1/bookings", name="bookings_v1")
    app.register_blueprint(escrow_bp, url_prefix="/api/escrow")
    app.register_blueprint(escrow_bp, url_prefix="/api/v1/escrow", name="escrow_v1")

    @app.route("/uploads/<path:filename>", methods=["GET"])
    def uploaded_file(filename):
        return send_from_directory(UPLOAD_FOLDER, filename)

    # Register error handlers and core routes
    register_error_handlers(app)
    register_system_routes(app)
    register_cli_commands(app)

    return app


# Default application instance for WSGI servers (Gunicorn / uWSGI)
app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=app.config.get("DEBUG", False), use_reloader=False)
