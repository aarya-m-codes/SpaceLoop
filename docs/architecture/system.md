# SpaceLoop System Architecture

## High-Level Topology
SpaceLoop is architected as an event-aware, clean-layered peer-to-peer storage and workspace sharing marketplace.

```mermaid
flowchart TD
    Client[Web & Mobile Clients] --> Gateway[Reverse Proxy / Nginx Gateway]
    Gateway --> WebApp[Vite React Frontend]
    Gateway --> BackendAPI[Flask Application Layer]
    BackendAPI --> CoreAuth[Authentication & MFA]
    BackendAPI --> TrustEngine[Trust & Safety Engine A]
    BackendAPI --> FraudEngine[Autonomous ML Fraud Engine B]
    BackendAPI --> EscrowService[Micro-Escrow Settlement]
    BackendAPI --> AccessController[Geofenced Access Guard]
    BackendAPI --> AIEngine[LoopBot Multi-LLM Orchestrator]
    BackendAPI --> DB[(Relational DB / SQLite / Postgres)]
    BackendAPI --> Cache[(Redis Cache & Session Store)]
```

## Core Design Principles
1. **Separation of Concerns**: UI presentation never executes authoritative business rules or financial pricing.
2. **Deterministic Fallbacks**: Every AI and ML component features hard deterministic fallbacks when external LLMs or serialized model artifacts are unavailable.
3. **Idempotency & Double-Release Protection**: Micro-escrow and booking access states transition deterministically.
