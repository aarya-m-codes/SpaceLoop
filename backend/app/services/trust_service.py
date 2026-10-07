"""SpaceLoop Trust & Safety Service."""
from backend.modules.trust_safety.service import TrustSafetyService

TrustService = TrustSafetyService

__all__ = ["TrustService", "TrustSafetyService"]
