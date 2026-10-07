# Frontend Architecture

## Stack & Modular Design
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS + Custom CSS Variables
- **Motion**: Framer Motion
- **Icons**: Lucide React

## Layout & Domain Hierarchy
- `src/app/`: Router, Providers, Layouts, Guards, Configuration.
- `src/pages/`: Route-mapped page components (Seeker, Host, Admin).
- `src/features/`: Encapsulated domain logic (Auth, Spaces, Bookings, Access, Host, Trust, AI LoopBot).
- `src/components/`: Reusable design system UI components.
- `src/services/`: Axios-driven authenticated API clients with token interceptors.
