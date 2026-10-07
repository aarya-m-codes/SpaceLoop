# SpaceLoop Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Node 20+](https://img.shields.io/badge/Node-20%2B-green.svg)](https://nodejs.org/)

SpaceLoop is an intelligent physical storage, creative studio, and workspace sharing marketplace. It connects Seekers and Hosts through dynamic AI matching, verified identity credentials, micro-escrow deposits, GPS-geofenced temporal access controls, and autonomous fraud detection engines.

---

## Canonical Architecture

The repository follows a clean, decoupled monorepo architecture:

```
SpaceLoop/
├── frontend/         # Canonical React 18 + Vite frontend application
│   ├── src/          # Components, pages, hooks, contexts, routes, and styles
│   ├── public/       # Static assets and images
│   ├── index.html    # Vite entrypoint HTML
│   ├── vite.config.js# Vite build and dev configuration (proxies /api to backend)
│   ├── package.json  # Frontend npm dependencies
│   └── package-lock.json
├── backend/          # Canonical Flask Python backend application
│   ├── app/          # Application factory bootstrap and v1 REST API blueprints
│   ├── core/         # Core extensions: SQLAlchemy database, CORS, Geo, Cache
│   ├── modules/      # Domain modules: auth, bookings, escrow, search, spaces, trust_safety
│   ├── fraud_engine/ # ML Isolation Forest & heuristic fraud detection engine
│   ├── config.py     # Environment configurations (Development, Testing, Production)
│   ├── models.py     # Unified SQLAlchemy data models
│   ├── security.py   # Password hashing, cryptographic tokens, and access PINs
│   ├── space_ai.py   # AI search adaptation & deterministic fallback engine
│   ├── seed_data.py  # Seed generator for bootstrap development data
│   ├── requirements.txt # Python production dependencies
│   └── run.py        # Authoritative WSGI / server entrypoint (`backend.run:app`)
├── database/         # Schema definitions, migrations, and seeds
├── contracts/        # API schemas and specifications
├── infrastructure/   # Docker container configurations and Nginx gateway
├── deployment/       # Staging and production deployment manifests
├── tests/            # Automated pytest test suites and production simulation tests
├── render.yaml       # Render blueprint specification for Web Service & PostgreSQL
├── Procfile          # Render web service process definition
├── Dockerfile        # Multi-stage production container build
├── .env.example      # Reference environment variable specification
└── README.md
```

---

## Database Configuration

- **Development**: SQLite stored locally in `instance/spaceloop_dev.db`. Automatically configured when `DATABASE_URL` is unset.
- **Production**: PostgreSQL configured via `DATABASE_URL`. Handles standard connection pooling and automatically normalizes legacy `postgres://` URLs to `postgresql://` for SQLAlchemy 2.0.
- **Initialization Command**:
  ```bash
  python -m flask --app backend.run:app init-db
  ```
- **Seeding Command (Development)**:
  ```bash
  python -m flask --app backend.run:app seed-db
  ```

---

## Environment Variables

Copy `.env.example` to `.env` and set values appropriate for your environment:

```bash
cp .env.example .env
```

Key variables:
- `DATABASE_URL`: Connection string (SQLite in dev, PostgreSQL in prod).
- `SECRET_KEY`: Random 32+ character key for sessions and cryptography.
- `JWT_SECRET_KEY`: Random 32+ character key for JWT token signing.
- `CORS_ORIGINS`: Allowed origins (e.g. `http://localhost:3000,http://127.0.0.1:3000`).
- `FLASK_ENV`: `development` or `production`.
- `PORT`: HTTP port (defaults to 5000).

---

## Local Development Workflow

### 1. Install Dependencies

```bash
# Python backend dependencies
pip install -r backend/requirements.txt

# Frontend dependencies
cd frontend
npm ci
cd ..
```

### 2. Initialize Development Database

```bash
python -m flask --app backend.run:app init-db
python -m flask --app backend.run:app seed-db
```

### 3. Run Development Servers

**Backend:**
```bash
python backend/run.py
```
Backend runs on `http://localhost:5000`.

**Frontend:**
```bash
cd frontend
npm run dev
```
Frontend development server runs on `http://localhost:3000` and automatically proxies `/api` and `/uploads` requests to the backend.

---

## Testing

Run the full automated test suite with pytest:

```bash
python -m pytest
```

Run specific test modules:
```bash
# Core API & journey tests
python -m pytest tests/integration/test_end_to_end_journeys.py

# Production single-service simulation tests
python -m pytest tests/test_production_simulation.py
```

---

## Production Build & Single-Service Hosting

The backend is configured to serve the production frontend SPA build directly alongside all REST APIs, enabling deployment on a single Web Service without requiring separate frontend hosting.

### Build Production Frontend:
```bash
npm run build --prefix frontend
```
Builds the optimized production bundle to `frontend/dist/`.

### Start Production Backend:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 120 backend.run:app
```

The server serves:
- `GET /` $\to$ `frontend/dist/index.html`
- `GET /<asset>` $\to$ static JS, CSS, and image assets from `frontend/dist/`
- `GET /<client-route>` $\to$ SPA fallback routing (returns `index.html` so browser refreshes do not 404)
- `GET /health` and `GET /api/v1/health` $\to$ platform health and database status
- `ALL /api/...` $\to$ Flask REST API endpoints

---

## Deployment to Render

Deploy as **one Render Web Service** connected to a **Render PostgreSQL** instance:

### 1. Render Web Service Settings
- **Environment**: Python
- **Build Command**:
  ```bash
  pip install -r backend/requirements.txt && npm ci --prefix frontend && npm run build --prefix frontend
  ```
- **Start Command**:
  ```bash
  gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120 backend.run:app
  ```

### 2. Render Environment Variables
Add the following in the Render Dashboard:
- `DATABASE_URL`: Set to the Render PostgreSQL Internal Database URL.
- `SECRET_KEY`: Strong random secret key.
- `JWT_SECRET_KEY`: Strong random JWT signing key.
- `FLASK_ENV`: `production`
- `PYTHON_VERSION`: `3.11` (or `3.12` / `3.13`)

### 3. Initialize Database on Render
Run this one-time command via the Render Shell or one-off Job:
```bash
python -m flask --app backend.run:app init-db
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
