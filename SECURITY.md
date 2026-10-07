# SpaceLoop Security Policy

## Reporting Vulnerabilities
SpaceLoop values security researchers and community feedback. If you discover a vulnerability or security flaw, please notify us immediately through coordinated vulnerability disclosure at `security@spaceloop.app`.

Please provide:
- Vulnerability description and scope
- Reproduction steps and proof of concept
- Potential impact analysis
- Remediation recommendations if known

## Security Principles
1. **Defense in Depth**: Every API endpoint verifies authentication, authorization, and tenant isolation server-side.
2. **Zero Raw Identity Storage**: Government IDs such as Aadhaar are strictly hashed with SHA-256 and salted tokens; raw identity numbers are never persisted.
3. **Financial Protection**: All financial settlements and micro-escrow releases require double-spend prevention, idempotent state transitions, and server-side calculation.
4. **Physical Geofencing**: Check-in requires GPS verification within 50 meters of listing coordinates and within a 15-minute temporal arrival window.
