"""Smoke test for the backend.

The health check itself has a known issue (see DEMO.md / issue #1) — fixing it,
with a proper regression test, is part of the walkthrough. This smoke test only
checks that the app boots and exposes its schema.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_app_exposes_openapi():
    assert client.get("/openapi.json").status_code == 200
