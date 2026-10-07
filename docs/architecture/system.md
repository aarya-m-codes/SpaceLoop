# SpaceLoop System Architecture

```mermaid
graph TD
    Client[Web & Mobile Clients] -->|HTTPS / TLS 1.3| Gateway[Nginx Reverse Proxy & Gateway]
    Gateway -->|Static SPA Assets| ReactApp[React 18 Frontend]
    Gateway -->|/api REST| FlaskBackend[Flask Modular Backend]
    
    FlaskBackend --> PostgreSQL[(PostgreSQL Primary)]
    FlaskBackend --> Redis[(Redis Cache & PubSub)]
    FlaskBackend --> CeleryWorkers[Background Task Workers]
    
    FlaskBackend --> AIOrchestrator[LoopBot AI Concierge]
    FlaskBackend --> SmartLock[Physical Access Smart Locks]
    FlaskBackend --> PaymentGateway[Escrow Settlement Gateway]
    FlaskBackend --> TrustSafety[Fraud & Risk Engine]
```

## Core Tenets
1. **Separation of Concerns**: Clean presentation layer with full-width responsive UX, decoupled from microservice modules.
2. **Deterministic Security**: Zero client-side trust; physical smart access credentials only generated after escrow confirmation.
3. **Resilience**: Redis caching for search pipelines with background asynchronous task processing for email/webhooks.
