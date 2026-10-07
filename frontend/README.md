# SpaceLoop Frontend Application

Modular enterprise React 18 client for the SpaceLoop peer-to-peer storage and workspace sharing marketplace.

## Architecture

- `src/app/`: Application bootstrap, routing, root providers, layouts, and route guards.
- `src/pages/`: Domain-grouped page components (public, auth, explore, spaces, booking, host, admin).
- `src/features/`: Encapsulated domain feature logic and hooks (trust, loop, booking, verification).
- `src/components/`: Reusable design system UI components.
- `src/services/`: REST API integration clients connecting to the SpaceLoop backend.

## Getting Started

```bash
npm install
npm run dev
```
