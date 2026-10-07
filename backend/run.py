"""SpaceLoop Backend Service Entrypoint."""
import os
import sys
from pathlib import Path

# Ensure backend directory and repo root are in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
for p in (str(BACKEND_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app.bootstrap.application import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=app.config.get("DEBUG", False))
