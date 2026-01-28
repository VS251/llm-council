## 1. Project Overview
- **Goal:** Build a "Council of LLMs" where multiple models debate a prompt before answering.
- **Stack:** Python 3.11, FastAPI (Backend), simple HTML/JS (Frontend).
- **Vibe:** Minimalist, high-performance, no-nonsense code.

## 2. Coding Standards 
- **No Abstractions:** Do not create classes unless absolutely necessary. Prefer simple functions.
- **No Bloat:** If a library isn't 100% needed, don't import it. Use standard libraries (json, os, sys) whenever possible.
- **Type Hints:** Use standard Python type hints (`def func(x: int) -> str:`).
- **Error Handling:** Crash early and loudly. Do not silence errors.
- **Comments:** Explain *why*, not *what*.

## 3. Common Commands
- Run Server: `uvicorn main:app --reload`
- Test: `pytest tests/`
- Lint: `ruff check .`

## 4. Architecture Constraints
- **State:** Keep state in memory for now. No database unless requested.
- **API Keys:** NEVER print API keys to logs. Always use `os.getenv()`.