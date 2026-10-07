"""SpaceLoop Root Execution Entrypoint."""
from backend.run import app

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=app.config.get("DEBUG", False))
