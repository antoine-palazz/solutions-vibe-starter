---
name: fastapi
description: FastAPI patterns, middleware, dependency injection, and testing best practices
user-invocable: false
---

# FastAPI Patterns

## Routing
- Use `APIRouter` with `prefix` and `tags` for organization
- Group related endpoints in a single router file
- Use dependency injection via `Depends()` for shared logic (auth, db sessions)

## Middleware
- Use `@app.middleware("http")` for cross-cutting concerns
- For rate limiting, use `slowapi` with `Limiter`:
  ```python
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)

  @router.get("/endpoint")
  @limiter.limit("10/minute")
  async def endpoint(request: Request):
      ...
  ```
- Configure limits via environment variables for per-environment flexibility

## Error Handling
- Always wrap external service calls in try/except
- Return structured error responses with proper HTTP codes
- Use `HTTPException` for expected errors, middleware for unexpected ones
- Health check endpoints must never crash — return degraded status instead:
  ```python
  try:
      status = await service.get_status()
  except Exception as e:
      logger.error("service unavailable", error=str(e))
      status = ServiceStatus(status=Status.ERROR, message=str(e))
  ```

## Testing
- Use `pytest` with `httpx.AsyncClient` for endpoint tests:
  ```python
  async with AsyncClient(app=app, base_url="http://test") as client:
      response = await client.get("/api/health/check")
      assert response.status_code == 200
  ```
- Test both success and error paths
- Use `pytest.fixture` for shared test setup

## Pydantic Models
- Define request/response models with Pydantic v2
- Use `model_validate()` for ORM → DTO conversion
- Keep API models in a dedicated `models/api_models.py`
