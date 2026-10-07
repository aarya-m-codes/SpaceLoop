# Authentication & Identity Architecture

- **Session Tokens**: JWT with HMAC-SHA256 and configurable expiration.
- **Multi-Factor Authentication (MFA)**: TOTP standard (RFC 6238) with backup recovery codes.
- **Password Hashing**: PBKDF2-HMAC-SHA256 with random salting.
