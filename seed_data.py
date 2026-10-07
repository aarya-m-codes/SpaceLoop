"""SpaceLoop Root Seed Script Wrapper."""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.bootstrap.application import create_app
from backend.seed_data import ensure_demo_accounts, seed_all

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("Ensuring SpaceLoop demo accounts...")
        status = ensure_demo_accounts(app)
        print("Demo accounts status:", status)
        print("Ensuring sample space catalog...")
        seed_res = seed_all(app)
        print("Seed summary:", seed_res)
