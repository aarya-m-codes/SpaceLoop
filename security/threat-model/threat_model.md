# SpaceLoop Threat Model (STRIDE)

| Threat Category | Potential Attack Vector | SpaceLoop Mitigation |
| --------------- | ----------------------- | -------------------- |
| **Spoofing** | Fake GPS coordinates during check-in | Client device location cross-checked with geofencing & rotating QR codes. |
| **Tampering** | Frontend price alteration during checkout | Authoritative pricing computed strictly on backend; inputs validated against DB rates. |
| **Repudiation** | Host denying space availability or check-in | Immutable database access logs and cryptographically recorded state transitions. |
| **Information Disclosure** | Leakage of Government IDs (Aadhaar) | Raw numbers discarded; SHA-256 tokenization used exclusively. |
| **Denial of Service** | High-velocity automated booking requests | IP-based and user-based token bucket rate limiting on Redis/in-memory storage. |
| **Elevation of Privilege** | Seeker attempting to access admin endpoints | Server-side role validation on every administrative route. |
