# Project Conventions — Vibe Starter

> This file is the project handbook. Vibe loads it automatically, so every agent
> follows the same conventions. **Skills** (in `.vibe/skills/` or `~/.vibe/skills/`)
> are the cross-repo toolbox; **this file** is what is specific to *this* repo.

## Architecture
- **Backend**: FastAPI (Python 3.11+) in `apps/backend/` — a health check
  endpoint. Intentionally minimal.
- **Frontend**: Next.js + TypeScript in `apps/frontend/` — a status page.
- **Deployment**: Docker Compose for local, in `deployment/docker/`.

## Coding Standards

### Python (Backend)
- Use structured logging with kwargs — never `print()` or f-strings in log
  messages (`logger.info("message", key=value)`).
- Type hints are mandatory on all public functions.
- Use Pydantic models for API request/response schemas.

### Error Handling
- Wrap external service calls in try/except with proper error logging.
- API endpoints return appropriate HTTP status codes — never raw 500s.
- Health check endpoints must never crash — return a degraded status instead
  (see `apps/backend/src/routers/health.py`).

### Testing
- Use `pytest`; tests live in `tests/` mirroring the source structure.
- Use `fastapi.testclient.TestClient` for endpoint tests.
- Every bug fix must include a regression test.

### Git Conventions
- Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- One logical change per commit.

## Project Commands
```bash
# Backend
cd apps/backend && uv run pytest                                   # tests
cd apps/backend && uv run uvicorn main:app --app-dir src --reload  # dev server

# Frontend
cd apps/frontend && pnpm install && pnpm dev                       # http://localhost:3000

# Full stack
docker compose -f deployment/docker/docker-compose.yml up --build
```
