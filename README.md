# SpaceLoop ♾️

> **Find a space, make it yours.**  
> Next-generation, hyper-localized intelligent workspace marketplace with seamless physical access, multi-party escrow, and AI concierge matching.

---

## 🌟 Key Capabilities

- **Cinematic Living Atmosphere**: Immersive visual onboarding with full-screen light/dark architectural environments and smooth slide transitions.
- **Micro-Lease Bookings**: On-demand hourly, daily, and monthly desk, studio, and boardroom reservations.
- **Smart PIN & QR Access**: Automated keyless check-in credentials issued instantly upon confirmed payment.
- **Two-Tier Escrow Settlement**: Automated dispute protection holding host payouts until check-in confirmation milestones.
- **LoopBot Intelligent Concierge**: AI-driven natural language space discovery with attribute ranking and constraint resolution.
- **Trust & Safety Engine**: Multi-source identity verification (Govt ID, UPI, Utility bills), fraud detection graph, and automated risk scoring.
- **Governance Portal**: Comprehensive administrative tools for dispute handling, audit trails, and listing approvals.

---

## 🏗️ Architecture Overview

```
spaceloop/
├── .github/          # CI/CD Workflows, security scans, issue templates
├── contracts/        # OpenAPI contracts, domain event schemas, webhooks
├── infrastructure/   # Docker, Kubernetes, Nginx, Redis, PostgreSQL specs
├── deployment/       # Multi-environment configurations and release playbooks
├── config/           # Centralized environment configs and feature flags
├── security/         # Threat models, security policies, and SBOM specs
├── observability/    # Metrics, OpenTelemetry, Grafana dashboards, SLOs
├── operations/       # Operational runbooks, incident response & DR plans
├── docs/             # Technical architecture and decision records (ADRs)
├── scripts/          # Developer tooling, database migration & seed scripts
├── database/         # Schemas, migrations, indexing, and seed data
├── src/              # React 18 + Vite frontend application
└── backend/          # Flask & Python microservices ecosystem
```

---

## 🚀 Quick Start

### Prerequisites
- **Node.js**: >= 18.0
- **Python**: >= 3.10
- **Docker & Compose**: (optional for containerized runtime)

### Local Development Setup

1. **Clone & Install Dependencies**:
   ```bash
   git clone https://github.com/aarya-m-codes/SpaceLoop.git
   cd SpaceLoop
   npm install
   pip install -r requirements.txt
   ```

2. **Run Frontend Application**:
   ```bash
   npm run dev
   ```
   Access the frontend at `http://localhost:3000`.

3. **Run Backend Services**:
   ```bash
   python app.py
   ```
   Access API endpoints at `http://localhost:5000`.

4. **Run via Docker Compose**:
   ```bash
   docker-compose up -d
   ```

---

## 🧪 Testing

```bash
# Frontend unit & integration tests
npm test

# Backend suite
pytest tests/
```

---

## 🛡️ Security & Governance

For vulnerability disclosure, please refer to [SECURITY.md](SECURITY.md).  
SpaceLoop implements end-to-end token validation, role-based access control (Seeker, Host, Admin), and continuous CI security auditing.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
