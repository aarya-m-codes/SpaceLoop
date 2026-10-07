# Backend Architecture

## Technology Stack
- **Framework**: Python 3.11 with Flask modular blueprints & SQLAlchemy ORM
- **Database**: PostgreSQL 15 with pg_trgm and UUID extensions
- **Cache & Message Broker**: Redis 7
- **AI Engine**: Gemini Flash API & Local NLP embeddings extractor

## Core Domains & Modules
- `backend/modules/spaces`: Space creation, geocoding, photo verification, and amenity tagging.
- `backend/modules/escrow`: Two-phase payment capture, milestone holding, and automated host settlement.
- `backend/modules/search`: Hybrid lexical and vector ranking pipeline for workspace discovery.
- `backend/modules/trust_safety`: Graph-based fraud detection, risk scoring, and identity verification adapters.
- `backend/modules/verification`: External integration adapters for Aadhaar, UPI, Electricity Discoms, and Student IDs.
- `backend/modules/email`: Transactional email delivery with Brevo, Resend, and SMTP adapters.
