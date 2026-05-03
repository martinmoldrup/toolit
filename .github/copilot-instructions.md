# Copilot Instructions For This Repository

## Design Principles

- Prefer explicit data models over loosely structured dictionaries when representing domain concepts.
- Favor Domain-Driven Design (DDD) thinking for new features and refactors when it fits the change:
  - Keep domain concepts, language, and invariants clear.
  - Organize code around domain behavior and boundaries, not only technical layers.
  - Avoid leaking infrastructure details into core domain logic.
- Keep business rules close to domain models and domain services.
- Use modern python syntax for python 3.10 and higher, such as pattern matching, type hints, dataclasses, enums, f-strings, and more.
- Favor pathlib for file system paths and operations
- Follow pep8 and use type hints (avoid dynamically typed Any when possible, prefer more specific types)
## Command Execution

- Use `uv run` when project Python dependencies or the project environment are needed.
- This applies to tests, linting, type-checking, scripts, and local tooling commands that rely on the repository environment.
- It is acceptable to run commands without `uv run` when the `.venv` or project dependencies are not needed.
- Prefer forms like:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run mypy .`
  - `uv run python <script>.py`

## Change Discipline

- Preserve existing behavior unless a change request explicitly asks for behavior changes.
- Keep changes minimal and focused on the requested outcome.
- Add or update tests when behavior is added or changed.

## Test driven development (TDD)
- If the change is a bug fix, first write a test that reproduces the bug. The test should fail before the fix is implemented.
- For new features, and changes this is optional but encouraged. Do it when it makes sense.