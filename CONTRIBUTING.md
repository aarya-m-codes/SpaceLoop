# Contributing to SpaceLoop

Thank you for your interest in contributing to SpaceLoop!

SpaceLoop is an intelligent physical storage and workspace sharing marketplace powered by AI-driven space scanning, dynamic micro-escrow, geofenced access control, and behavioral fraud detection.

## Development Workflow

1. Fork and clone the repository.
2. Create a virtual environment and install backend requirements:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   npm install
   ```
4. Run tests before writing any code:
   ```bash
   make test
   make build
   ```

## Code Quality Standards

- Maintain zero regression across the 137 unit and integration tests.
- Always run `python -m unittest discover -s tests -p "test_*.py"` before submitting changes.
- Ensure Vite production build succeeds (`npm run build`).
- Do NOT commit credentials, secret tokens, or test private keys.
- Adhere to semantic commit messages (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).

## Submitting a Pull Request

- Provide a clear description referencing any corresponding issue.
- Verify tests pass in GitHub Actions.
- Ensure code coverage does not decrease.
