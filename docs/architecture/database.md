# Database Architecture & Schemas

## Storage Engines
- Development: SQLite with WAL mode and performance pragmas.
- Production: PostgreSQL 15+ with indexed JSONB and foreign key constraints.

## Primary Tables
- `users`: Authentication, MFA secret, role, verification status.
- `spaces`: Listing metadata, geo-coordinates, base rates.
- `bookings`: Reservations, temporal guards, status.
- `escrow_transactions`: Financial balances, release tracking.
- `access_logs`: Temporal geofenced check-ins.
- `fraud_events` / `risk_assessments`: Auditable risk evaluations.
