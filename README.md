# SpaceLoop Enterprise Marketplace

[![CI Suite](https://github.com/aarya-m-codes/SpaceLoop/actions/workflows/ci.yml/badge.svg)](https://github.com/aarya-m-codes/SpaceLoop/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Node 20+](https://img.shields.io/badge/Node-20%2B-green.svg)](https://nodejs.org/)

SpaceLoop is an intelligent physical storage, creative studio, and workspace sharing marketplace. It pairs Seekers and Hosts through dynamic AI matching, verified identity credentials, micro-escrow deposits, GPS-geofenced temporal access controls, and autonomous fraud detection engines.

---

## Architecture Overview

SpaceLoop is organized around an enterprise modular domain architecture:

```
spaceloop/
├── .github/          # CI/CD workflows, CodeQL, security audits, and issue templates
├── frontend/         # Production React 18 + Vite frontend with modular feature structure
├── backend/          # Flask clean architecture: bootstrap, API v1, services, engines, AI
├── database/         # Schema definitions, migrations, seeds, and ER diagrams
├── contracts/        # OpenAPI specifications, domain events, and error schemas
├── infrastructure/   # Docker container definitions, Nginx gateway, and Redis configs
├── deployment/       # Staging, production, blue/green rollout configurations
├── config/           # Multi-environment configurations and feature flag defaults
├── security/         # Threat models, security policies, SBOM, and checklists
├── observability/    # Metrics, logging, OpenTelemetry integration, and alerts
├── operations/       # Runbooks, disaster recovery, incident response guides
├── docs/             # Technical architecture, system diagrams, and ADRs
└── scripts/          # Setup, testing, maintenance, and database automation
```

---

## Core Systems & Engines

### 1. Dual Fraud & Risk Intelligence
- **System A: Marketplace Trust & Safety Engine (`backend/modules/trust_safety/`)**:
  - Behavioral signal analysis: `SELF_BOOKING`, `COLLUSION_RING`, `VELOCITY_SPIKE`, `DEVICE_REUSE`, `DISCOM_MISMATCH`, `RAPID_DISPUTE`.
  - Multi-entity bipartite graph analysis connecting Users, Spaces, Devices, IPs, and Bookings.
  - LLM Forensic Narrative generation with cascading fallback: **Groq (Llama 3.3)** → **Google Gemini 1.5** → **Deterministic Rule Engine**.
- **System B: Autonomous ML Fraud Engine (`fraud_engine/`)**:
  - Event ingestion and numerical behavioral feature extraction.
  - Isolation Forest anomaly detection with deterministic statistical fallbacks.
  - Decision threshold matrix:
    - `Risk >= 0.80` $\to$ **BLOCK**
    - `Risk >= 0.60` $\to$ **HOLD / REVIEW**
    - `Risk >= 0.40` $\to$ **CHALLENGE / MFA**
    - `Risk < 0.40` $\to$ **ALLOW**

### 2. Physical Geofencing & Access Security
- 50-meter Haversine geofence validation for seeker check-in.
- 15-minute temporal window guard around booking start time.
- Dynamic rotating QR code verification with fallback time-bound 6-digit PIN.
- Immutable cryptographic check-in and checkout audit logs.

### 3. Financial Micro-Escrow & Pricing
- Authoritative server-side price computation.
- ₹100 refundable security deposit model held in micro-escrow until clean checkout inspection.
- 5% platform fee with transparent host and seeker breakdowns.
- Idempotent payout settlement with duplicate release prevention.

### 4. Multilingual AI Space Assistant (LoopBot)
- Natural language space search supporting English, Hindi, Hinglish, and Marathi.
- Multi-provider resilient execution with streaming responses and contextual suggestions.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- SQLite (development) or PostgreSQL (production)

### Setup & Installation
```bash
# Clone the repository
git clone https://github.com/aarya-m-codes/SpaceLoop.git
cd SpaceLoop

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup Frontend dependencies
npm install

# Copy environment template
cp .env.example .env
```

### Running Tests
```bash
# Run full 137 test suite
make test

# Or directly via unittest
python -m unittest discover -s tests -p "test_*.py"
```

### Building & Running
```bash
# Build frontend
npm run build

# Start backend server
python app.py
```

Visit `http://localhost:5000` to interact with SpaceLoop.

---

## License
MIT License - see [LICENSE](LICENSE) for details.
