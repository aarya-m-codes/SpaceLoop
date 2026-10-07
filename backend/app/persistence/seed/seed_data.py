"""SpaceLoop Persistence Seed Module (delegating to backend.seed_data)."""
from backend.seed_data import ensure_demo_accounts, seed_all

__all__ = ["ensure_demo_accounts", "seed_all"]
