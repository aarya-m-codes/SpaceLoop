"""SpaceLoop Backend Package."""
import sys
from pathlib import Path

# Ensure backend directory and repo root are in sys.path for direct imports
_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_DIR.parent
for _p in (str(_BACKEND_DIR), str(_REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
