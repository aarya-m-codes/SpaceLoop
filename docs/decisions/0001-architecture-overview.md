# ADR 0001: Architecture Overview & Monorepo Strategy

## Context
SpaceLoop combines real-time physical access, financial escrow settlement, complex identity verification, and an animated React user experience.

## Decision
We chose a modular architecture where:
1. The frontend remains decoupled with high-performance client-side rendering (React + Vite + Tailwind).
2. The backend services utilize modular Python blueprints allowing independent service boundaries (Escrow, Access, Verification, Trust & Safety) while sharing transaction boundaries.
3. Contracts (OpenAPI and Domain Events) serve as the single source of truth between frontend, backend, and external microservices.

## Consequences
- **Positive**: High development velocity, deterministic contract testing, rapid CI pipeline execution.
- **Negative**: Requires rigorous schema synchronization maintained through `contracts/`.
