from collections.abc import Iterable
from flask import Flask, Response, request


class CORS:
    """Lightweight and configurable Cross-Origin Resource Sharing (CORS) handler."""

    def __init__(self, app: Flask | None = None, origins: Iterable[str] | str = "*"):
        self.origins = origins
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        origins_cfg = app.config.get("CORS_ORIGINS", "*")
        if isinstance(origins_cfg, str):
            self.origins = [o.strip() for o in origins_cfg.split(",") if o.strip()]
        else:
            self.origins = list(origins_cfg)

        @app.before_request
        def handle_preflight() -> Response | None:
            if request.method == "OPTIONS":
                response = Response(status=204)
                self._apply_cors_headers(response)
                return response
            return None

        @app.after_request
        def after_request_cors(response: Response) -> Response:
            self._apply_cors_headers(response)
            return response

    def _apply_cors_headers(self, response: Response) -> None:
        origin = request.headers.get("Origin")
        allowed_origin = "*"

        if origin:
            if "*" in self.origins:
                allowed_origin = "*"
            elif origin in self.origins:
                allowed_origin = origin
            else:
                return  # Origin not allowed; do not attach permissive headers
        elif "*" not in self.origins and self.origins:
            allowed_origin = self.origins[0]

        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With, Accept, Origin"
        )
        response.headers["Access-Control-Max-Age"] = "86400"
        if allowed_origin != "*":
            response.headers["Access-Control-Allow-Credentials"] = "true"


def init_cors(app: Flask) -> CORS:
    """Initialize CORS on the provided Flask application instance."""
    return CORS(app)
