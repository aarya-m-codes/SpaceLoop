# SpaceLoop Threat Model (STRIDE)

| Threat Category | Potential Threat Vector | SpaceLoop Mitigation Control |
| --------------- | ----------------------- | ---------------------------- |
| **Spoofing** | Attacker impersonates host or seeker using forged tokens. | Cryptographic JWT signatures, token expiry, refresh token rotation, MFA support. |
| **Tampering** | Man-in-the-middle alters booking amount or PIN codes. | TLS 1.3 enforced, HMAC webhook validation, encrypted physical access payloads. |
| **Repudiation** | Host denies workspace was accessed or seeker denies check-in. | Immutable audit log of lock events, check-in timestamps, and photo dispute records. |
| **Information Disclosure** | Smart lock master credentials or PII leaked. | Salted Argon2/bcrypt password hashes, scoped door lock access tokens, zero PII in logs. |
| **Denial of Service** | DDoS on space search or booking slot lock exhaustion. | Redis sliding-window rate limiting, optimistic slot locking with 10-minute timeouts. |
| **Elevation of Privilege** | Seeker switches active context to Admin portal. | Server-side role authorization middleware (`@require_role('admin')`) verifying DB claim. |
