# Backend Architecture

## Clean Architecture Layers
1. **API / Presentation Layer** (`backend/app/api/v1/`): Blueprints handling HTTP routing, request deserialization, authorization decorators, and HTTP response formatting.
2. **Application / Service Layer** (`backend/app/services/`): Orchestrates business workflows, coordinates domain entities, and handles transactions.
3. **Domain & Engine Layer** (`backend/app/domain/`, `backend/app/engines/`): Pure domain logic, pricing algorithms, geofence computations, and risk scoring.
4. **Persistence Layer** (`backend/app/repositories/`, `models.py`): SQLAlchemy models and database repositories.
