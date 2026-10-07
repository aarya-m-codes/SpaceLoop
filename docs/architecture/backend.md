# Backend Architecture

## Clean Architecture Layers
1. **API / Presentation Layer** (`backend/app/api/v1/`): REST JSON Blueprints handling HTTP routing, request deserialization, security decorators, and response serialization.
2. **Application / Service Layer** (`backend/app/services/`, `backend/modules/`): Orchestrates business workflows, manages transactional boundaries, coordinates domain engines, and enforces security policies.
3. **Domain & Engine Layer** (`backend/app/domain/`, `backend/app/engines/`, `backend/modules/search/`, `backend/modules/bookings/`): Pure domain logic, six-stage hybrid discovery pipeline, dynamic pricing algorithms, geofence computations, and fraud scoring.
4. **Authoritative Persistence Layer** (`backend/app/persistence/`, `backend/core/database.py`, `models.py`): Unified SQLAlchemy ORM models, scoped session lifecycle, and transaction management against a single authoritative persistence store. All components (REST API, Search Pipeline, Booking Engine, Admin) share this exact persistence layer.
