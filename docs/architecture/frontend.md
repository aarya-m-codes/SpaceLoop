# Frontend Architecture

## Technology Stack
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS with custom glassmorphism and theme variables
- **Motion & Dynamics**: Framer Motion and custom hardware-accelerated CSS keyframes
- **Icons**: Lucide React
- **Routing**: React Router DOM v6 with route-level role-based guards

## Architectural Patterns
1. **Living Hero Sequence**:
   - 2.0-second timeline animating sky gradient, architectural ascent, brand drop, and subtitle reveal.
   - Smooth page-turn slide transition between the hero and discovery catalog.
2. **Global Navigation**:
   - Full-width edge-to-edge header.
   - Left-aligned Hamburger menu dropdown with How It Works, List a Space, and Bookings adjacent to Infinity brand badge.
   - Right-aligned Context Pill, Theme Toggle, and Profile Dropdown.
3. **Context Providers**:
   - `AuthContext`: Manages JWT tokens, user state, and multi-persona switching (Seeker / Host / Admin).
   - `ThemeContext`: Handles light/dark system preferences with real-time DOM synchronization.
   - `ToastContext`: Global notifications and transaction status feedback.
