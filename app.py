"""SpaceLoop Root Application Module (delegating directly to backend.app.bootstrap.application)."""
import os
from backend.app.bootstrap.application import app, create_app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=app.config.get("DEBUG", False), use_reloader=False)
