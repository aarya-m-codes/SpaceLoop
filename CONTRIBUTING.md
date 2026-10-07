# Contributing to SpaceLoop

Thank you for your interest in contributing to SpaceLoop, the hyper-localized intelligent workspace marketplace.

## Development Workflow

1. **Fork & Branch**: Create a feature branch from `main` with a descriptive name (`feat/access-nfc`, `fix/nav-alignment`).
2. **Setup Environment**:
   ```bash
   npm install
   pip install -r requirements.txt
   ```
3. **Run Development Server**:
   ```bash
   npm run dev
   ```
4. **Code Quality**:
   - Ensure all components comply with accessibility (WCAG 2.1 AA) standards.
   - Maintain edge-to-edge layout styling with zero horizontal overflow.
   - Follow semantic Git commits (`feat:`, `fix:`, `docs:`, `chore:`).
5. **Testing**:
   - Run unit and integration tests before opening a pull request:
   ```bash
   npm test
   pytest tests/
   ```
6. **Pull Requests**:
   - Fill out the PR template completely.
   - Ensure CI checks pass.
   - Request review from designated code owners (`@aarya-m-codes`).
