---
name: python-modern-standards
description: Enforces the 2025 Python stack. Replaces legacy tools (pip, flake8, isort) with modern, fast equivalents (uv, ruff). Mandates strict type hints.
license: MIT
---

## What I do
- Setup Python projects using `uv` (The successor to pip/poetry).
- Configure `ruff` for linting/formatting (replacing Black/Flake8).
- Implement Pydantic V2 for strict data validation.
- Enforce `mypy` strict mode.

## When to use me
- When creating a new Python project (FastAPI, Django, Scripts).
- When asked to "lint" or "format" python code.
- When fixing python dependency issues.
- Triggers: "python setup", "uv", "ruff", "pydantic", "fastapi".

## Instructions

### 1. Project Management (uv)
- **Tool**: Use `uv` for everything.
  - Init: `uv init`
  - Add Dep: `uv add fastapi`
  - Run: `uv run main.py`
- **Lockfile**: Always commit `uv.lock`.
- **Python Version**: Pin it in `pyproject.toml` (e.g., `requires-python = ">=3.12"`).

### 2. Linting & Formatting (Ruff)
- **Config**: Use `pyproject.toml` for ruff config.
- **Rules**: Enable `I` (isort), `B` (bugbear), `UP` (pyupgrade).
  ```toml
  [tool.ruff]
  target-version = "py312"
  select = ["E", "F", "I", "B", "UP"]
  ```

### 3. Type Safety
- **Strictness**: Types are NOT optional in 2025 production code.
- **Pydantic**: Use `BaseModel` for all complex data structures.
  ```python
  from pydantic import BaseModel, EmailStr

  class UserCreate(BaseModel):
      username: str
      email: EmailStr
  ```

### 4. Anti-Patterns
- **`requirements.txt`**: Legacy. Use `pyproject.toml` + `uv.lock`.
- **`from module import *`**: Never. Explicit imports only.
- **Mutable Defaults**: `def func(list=[]):` is forbidden. Use `None`.
