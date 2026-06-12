---
name: python-testing
description: Pytest patterns for FastAPI — fixtures, TestClient, env-driven branches, and what to assert
user-invocable: false
---

# Python Testing (pytest)

## Structure
- Mirror the source tree under `tests/`
- One behaviour per test; name tests `test_<unit>_<expectation>`
- Configure import paths in `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  pythonpath = ["src"]
  ```

## FastAPI endpoints
- Use `fastapi.testclient.TestClient` for synchronous endpoint tests:
  ```python
  from fastapi.testclient import TestClient
  from main import app

  client = TestClient(app)

  def test_health_ok():
      resp = client.get("/api/health/check")
      assert resp.status_code == 200
      assert resp.json()["status"] == "OK"
  ```
- To test async helpers directly, use `httpx.AsyncClient` with an ASGI transport.

## Fixtures & isolation
- Use `pytest.fixture` for shared setup; keep fixtures small and explicit
- Use `monkeypatch.setenv(...)` to drive config-dependent branches
- Avoid shared mutable state between tests (in-memory stores, module globals)

## What to assert
- Test both the success and the failure path
- Every bug fix ships with a regression test that fails before the fix
- Assert on status codes AND response shape, not just one
