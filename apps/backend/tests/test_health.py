"""Tests for the health check endpoint.

Covers the regression from issue #1: a failing dependency must not take the
endpoint down — it degrades gracefully to a 200 with a per-service status.
"""

import socket

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_app_exposes_openapi():
    assert client.get("/openapi.json").status_code == 200


def test_health_degrades_when_database_down(monkeypatch):
    """Regression for issue #1: DB down -> 200 DEGRADED, not 500."""

    def _refuse(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(socket, "create_connection", _refuse)

    resp = client.get("/api/health/check")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "DEGRADED"
    assert body["services"]["database"]["status"] == "ERROR"


def test_health_ok_when_database_up(monkeypatch):
    """When the probe succeeds, the aggregate status is OK."""

    class _FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: _FakeConn())

    resp = client.get("/api/health/check")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "OK"
    assert body["services"]["database"]["status"] == "OK"
