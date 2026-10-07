# Database Architecture & Schemas

## Authoritative Single Source of Truth
SpaceLoop adheres to a strict single-source-of-truth persistence architecture for all core marketplace entities (`User`, `Space`, `Booking`, `EscrowTransaction`, `AccessLog`, etc.).

1. **Unified Storage**:
   - There is NO division between "Marketplace records" and "Application database".
   - All modules (REST API, Discovery Pipeline, AI Matcher, Concurrency Manager, Escrow Engine, and Admin Panel) read and write to the identical authoritative database.
   - Development Engine: SQLite with WAL mode, normal synchronous pragmas, 5000ms busy timeout, and memory-mapped I/O, stored canonically in `instance/spaceloop_dev.db`.
   - Production Engine: PostgreSQL 15+ with connection pooling, indexed JSONB, and foreign key constraints.

2. **Unified ORM Model Metadata**:
   - Authoritative schema definitions reside in `backend/app/persistence/models/schema.py`.
   - Both root `models.py` and `backend/models.py` delegate strictly to `backend.app.persistence.models`, guaranteeing singleton ORM metadata and zero model class drift.
   - Scoped database sessions are managed uniformly through `backend.core.database.db.session` and `backend.app.persistence.session.get_session()`.

3. **Discovery & Search Data Consistency**:
   - Hybrid search and discovery engines query the authoritative database directly (`Space.query`, `Booking.query`).
   - Listing mutations (price changes, capacity adjustments, activation toggles) and booking confirmations are immediately reflected across search, matching, and checkout validations without secondary index staleness.

## Primary Tables
- `users`: Authentication, MFA secret, role, verification status, trust metrics.
- `spaces`: Listing metadata, geo-coordinates, base rates, amenities, AI environmental attributes.
- `bookings`: Reservations, temporal guards, status, escrow hold linkage, check-in pins.
- `escrow_transactions`: Financial balances, deposit holds, settlement and release tracking.
- `access_logs`: Temporal geofenced check-ins and check-outs.
- `fraud_event_records` / `risk_assessments`: Auditable risk evaluations and anomaly telemetry.
- `reviews`: Verified stay reviews and rating aggregation.
- `space_inquiries`: Peer-to-peer user-host communications.
- `notifications`: Real-time system and transactional notifications.
