# System Context Diagram

```mermaid
graph TD
  Seeker --> SpaceLoop
  Host --> SpaceLoop
  Admin --> SpaceLoop
  SpaceLoop --> AIProviders[Groq / Gemini]
  SpaceLoop --> PostgreSQL
```
