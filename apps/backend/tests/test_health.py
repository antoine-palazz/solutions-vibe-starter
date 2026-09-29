"""Smoke test for the backend.

The health check itself has a known issue (see DEMO.md / issue #1) — fixing it,
with a proper regression test, is part of the walkthrough. This smoke test only
checks that the app boots and exposes its schema.
"""

import os

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_app_exposes_openapi():
    assert client.get("/openapi.json").status_code == 200


def test_health_check_returns_200_when_db_unavailable(monkeypatch):
    """Regression test for PROJ-101: health-check must return 200 even when DB is down."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "9999")

    response = client.get("/api/health/check")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "DEGRADED"
    assert "database" in data["services"]
    assert data["services"]["database"]["status"] == "ERROR"
    assert data["services"]["database"]["details"] is not None
