"""Tests for request rate limiting (issue #2).

The `FixedWindowRateLimiter` unit tests use only the standard library. The
endpoint tests build a fresh app with a small limit so the 429 path is
deterministic and independent of the env-driven default.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from main import RateLimitMiddleware
from rate_limit import FixedWindowRateLimiter
from routers import demo, health


def _build_app(max_requests: int) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        limiter=FixedWindowRateLimiter(max_requests=max_requests, window_seconds=60),
        exclude_prefixes=("/api/health",),
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(demo.router, prefix="/api")
    return app


# --- Unit tests for the limiter core (stdlib only) ---


def test_limiter_allows_up_to_max():
    rl = FixedWindowRateLimiter(max_requests=2, window_seconds=10)
    assert rl.is_allowed("a", now=0.0) is True
    assert rl.is_allowed("a", now=1.0) is True
    assert rl.is_allowed("a", now=2.0) is False


def test_limiter_resets_after_window():
    rl = FixedWindowRateLimiter(max_requests=1, window_seconds=10)
    assert rl.is_allowed("a", now=0.0) is True
    assert rl.is_allowed("a", now=5.0) is False
    assert rl.is_allowed("a", now=10.0) is True


def test_limiter_is_per_key():
    rl = FixedWindowRateLimiter(max_requests=1, window_seconds=10)
    assert rl.is_allowed("a", now=0.0) is True
    assert rl.is_allowed("b", now=0.0) is True
    assert rl.is_allowed("a", now=0.0) is False


# --- Endpoint behaviour ---


def test_ping_ok_within_limit():
    client = TestClient(_build_app(max_requests=3))
    resp = client.get("/api/demo/ping")
    assert resp.status_code == 200
    assert resp.json()["message"] == "pong"


def test_ping_rate_limited_after_threshold():
    client = TestClient(_build_app(max_requests=3))
    statuses = [client.get("/api/demo/ping").status_code for _ in range(5)]
    assert statuses[:3] == [200, 200, 200]
    assert 429 in statuses[3:]


def test_health_never_rate_limited():
    client = TestClient(_build_app(max_requests=1))
    statuses = [client.get("/api/health/check").status_code for _ in range(5)]
    assert all(s == 200 for s in statuses)
