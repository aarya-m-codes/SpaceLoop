"""Pytest configuration and environment initialization for SpaceLoop."""
import os
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"

for p in (str(BACKEND_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
