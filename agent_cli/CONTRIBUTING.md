# Contributing Guide

1. **Set up the environment**
   - Install dependencies from `pyproject.toml` using a virtualenv.
   - Copy `.env.example` to `.env` and adjust any connection details.

2. **Follow the TDD workflow**
   - Write or update tests under `tests/` before changing implementation code.
   - Use `python -m pytest tests` to run the full suite.

3. **Code style**
   - Format with `black` and lint with `ruff` (configured via `pyproject.toml`).
   - Keep modules ASCII-only unless Unicode is required for UX (e.g. status icons).
   - Prefer descriptive inline comments for non-obvious logic paths.

4. **Git hygiene**
   - Avoid force pushes to main; work in feature branches.
   - Keep commits scoped and reference issue IDs where available.

5. **Security & reliability**
   - Never trust agent output blindly; validate paths before file operations.
   - Exercise undo/redo stacks when adding destructive actions.
   - Ensure the UI remains responsive even when the agent is offline or misbehaving.

6. **Review checklist**
   - Tests covering the change pass locally.
   - No regressions across panels (Home, Tasks, Thinking, Logs, Editor, Config, Verification, Help).
   - State persists as expected when switching panels.
   - Rendering behaves under 80x24 and larger terminal sizes.

