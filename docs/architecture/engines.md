# SpaceLoop Intelligence Engines

## System A: Marketplace Trust & Safety Engine
- Location: `backend/modules/trust_safety/`
- Behavioral Signals: SELF_BOOKING, COLLUSION_RING, VELOCITY_SPIKE, DEVICE_REUSE, DISCOM_MISMATCH, RAPID_DISPUTE.
- Bipartite Graph Analysis: Users, Spaces, Devices, IPs, Bookings.
- Forensic Narrative Generation: Groq -> Gemini -> Deterministic Rule fallback.

## System B: Autonomous ML Fraud Engine
- Location: `fraud_engine/`
- Isolation Forest anomaly detection + statistical sliding windows.
- Risk Threshold Matrix:
  - >= 0.80: BLOCK
  - >= 0.60: HOLD / REVIEW
  - >= 0.40: CHALLENGE / MFA / KYC
  - < 0.40: ALLOW
