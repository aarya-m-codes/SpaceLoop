"""SpaceLoop Marketplace Trust & Safety Engine (System A).

Specialized in:
- Behavioral signal extraction (SELF_BOOKING, COLLUSION_RING, VELOCITY_SPIKE, DEVICE_REUSE, DISCOM_MISMATCH, RAPID_DISPUTE)
- Multi-partite graph relationship analysis over Users, Spaces, Devices, IPs, and Bookings
- Suspicious circular transaction & cycle detection
- Multi-tier forensic narrative generation (Groq -> Gemini -> Deterministic)
"""

from backend.modules.trust_safety.service import TrustSafetyService

__all__ = ["TrustSafetyService"]
