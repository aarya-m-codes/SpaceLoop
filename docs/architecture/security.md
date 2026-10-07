# Security Architecture & Policies

## Core Tenets
1. **Zero Raw Identity Storage**: Government IDs (Aadhaar) are irreversibly hashed with SHA-256 tokens.
2. **Access Control**: Role-based access control (RBAC) enforced via server-side decorators on every route.
3. **Defense in Depth**: CSRF protection, rate limiting (Redis/memory storage), XSS sanitization, and SQL injection prevention via ORM.
