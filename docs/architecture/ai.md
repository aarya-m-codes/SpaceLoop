# AI & Concierge (LoopBot) Architecture

## Overview
LoopBot is an intelligent workspace concierge designed to translate free-form user intents into structured search parameters and personalized space recommendations.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant NLPParser
    participant VectorEngine
    participant Database

    User->>Frontend: "Need a quiet studio near Connaught Place with fast WiFi"
    Frontend->>NLPParser: Parse Intent & Constraints
    NLPParser-->>NLPParser: Extract: type=studio, loc=Connaught Place, min_speed=100
    NLPParser->>VectorEngine: Generate Query Embedding
    VectorEngine->>Database: Hybrid Vector + SQL Filter Search
    Database-->>Frontend: Top Ranked Spaces
    Frontend-->>User: Visualized space cards with matching reason
```

## Guardrails & Fallback
- If the AI LLM service is degraded, LoopBot gracefully degrades to regex-based keyword extraction and popularity-ranked database listings without failing user requests.
