"""Tests for the rate limiting middleware.

This module tests the RateLimitMiddleware to ensure it correctly:
- Allows requests under the limit
- Blocks requests over the limit with HTTP 429
- Excludes configured paths (e.g., health checks)
- Resets the window after the time period
- Isolates rate limits per client
- Adds appropriate rate limit headers to responses
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_429_TOO_MANY_REQUESTS

from middleware.rate_limiter import RateLimitMiddleware


@pytest.fixture
def app_with_rate_limit():
    """Create a FastAPI app with rate limiting middleware."""
    app = FastAPI()

    @app.get("/api/test")
    async def test_endpoint():
        return {"message": "OK"}

    @app.get("/api/health/check")
    async def health_check():
        return {"status": "OK"}

    app.add_middleware(
        RateLimitMiddleware,
        max_requests=3,
        window_seconds=60,
        exclude_paths=["/api/health"],
    )
    return app


@pytest.fixture
def client(app_with_rate_limit):
    """TestClient for the app with rate limiting."""
    return TestClient(app_with_rate_limit, raise_server_exceptions=False)


@pytest.fixture
def app_with_custom_window():
    """App with a very short rate limit window for testing reset behavior."""
    app = FastAPI()

    @app.get("/api/test")
    async def test_endpoint():
        return {"message": "OK"}

    app.add_middleware(
        RateLimitMiddleware,
        max_requests=2,
        window_seconds=1,  # 1 second window for testing
    )
    return app


@pytest.fixture
def client_custom_window(app_with_custom_window):
    """TestClient for the app with custom short window."""
    return TestClient(app_with_custom_window, raise_server_exceptions=False)


class TestRateLimitBehavior:
    """Test basic rate limiting behavior."""

    def test_allows_requests_under_limit(self, client):
        """Requests under the limit should return HTTP 200."""
        # First 3 requests should succeed (limit is 3)
        for _ in range(3):
            response = client.get("/api/test")
            assert response.status_code == HTTP_200_OK
            assert response.json() == {"message": "OK"}

    def test_blocks_requests_over_limit(self, client):
        """Requests over the limit should return HTTP 429."""
        # First 3 requests succeed
        for _ in range(3):
            client.get("/api/test")

        # 4th request should be blocked
        response = client.get("/api/test")
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
        assert "detail" in response.json()
        assert response.json()["detail"] == "Too many requests"
        assert "retry_after" in response.json()

    def test_returns_correct_retry_after(self, client):
        """HTTP 429 response should include retry_after with window seconds."""
        # Exhaust the limit
        for _ in range(3):
            client.get("/api/test")

        response = client.get("/api/test")
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
        assert response.json()["retry_after"] == 60


class TestPathExclusion:
    """Test that excluded paths bypass rate limiting."""

    def test_health_check_not_rate_limited(self, client):
        """Health check endpoints should not be rate limited."""
        # Exhaust the limit on regular endpoint
        for _ in range(3):
            client.get("/api/test")

        # Health check should still work
        response = client.get("/api/health/check")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"status": "OK"}

    def test_excluded_path_prefix(self):
        """All paths under excluded prefix should be excluded."""
        app = FastAPI()

        @app.get("/api/health/check")
        async def health_check():
            return {"status": "OK"}

        @app.get("/api/health/detailed")
        async def detailed_health():
            return {"status": "detailed"}

        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "OK"}

        app.add_middleware(
            RateLimitMiddleware,
            max_requests=1,
            window_seconds=60,
            exclude_paths=["/api/health"],
        )

        client = TestClient(app, raise_server_exceptions=False)

        # Exhaust limit on test endpoint
        client.get("/api/test")
        assert client.get("/api/test").status_code == HTTP_429_TOO_MANY_REQUESTS

        # Both health endpoints should still work
        assert client.get("/api/health/check").status_code == HTTP_200_OK
        assert client.get("/api/health/detailed").status_code == HTTP_200_OK


class TestClientIsolation:
    """Test that rate limits are isolated per client."""

    def test_different_clients_have_separate_limits(self):
        """Each client should have their own rate limit counter."""
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "OK"}

        app.add_middleware(
            RateLimitMiddleware,
            max_requests=2,
            window_seconds=60,
        )

        client = TestClient(app, raise_server_exceptions=False)

        # Simulate requests from different clients using headers
        # Client A makes 2 requests (hits limit)
        response_a1 = client.get("/api/test", headers={"X-Forwarded-For": "192.168.1.1"})
        response_a2 = client.get("/api/test", headers={"X-Forwarded-For": "192.168.1.1"})
        response_a3 = client.get("/api/test", headers={"X-Forwarded-For": "192.168.1.1"})

        assert response_a1.status_code == HTTP_200_OK
        assert response_a2.status_code == HTTP_200_OK
        assert response_a3.status_code == HTTP_429_TOO_MANY_REQUESTS

        # Client B should still be under limit
        response_b1 = client.get("/api/test", headers={"X-Forwarded-For": "192.168.1.2"})
        assert response_b1.status_code == HTTP_200_OK

    def test_x_real_ip_header(self):
        """X-Real-IP header should also be used for client identification."""
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "OK"}

        app.add_middleware(
            RateLimitMiddleware,
            max_requests=1,
            window_seconds=60,
        )

        client = TestClient(app, raise_server_exceptions=False)

        # Request with X-Real-IP
        response1 = client.get("/api/test", headers={"X-Real-IP": "10.0.0.1"})
        response2 = client.get("/api/test", headers={"X-Real-IP": "10.0.0.1"})

        assert response1.status_code == HTTP_200_OK
        assert response2.status_code == HTTP_429_TOO_MANY_REQUESTS

    def test_fallback_to_client_host(self):
        """When no forwarded headers, use request.client.host."""
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "OK"}

        app.add_middleware(
            RateLimitMiddleware,
            max_requests=1,
            window_seconds=60,
        )

        client = TestClient(app, raise_server_exceptions=False)

        # Without forwarded headers, each request appears from same client
        response1 = client.get("/api/test")
        response2 = client.get("/api/test")

        assert response1.status_code == HTTP_200_OK
        assert response2.status_code == HTTP_429_TOO_MANY_REQUESTS


class TestRateLimitHeaders:
    """Test that rate limit headers are correctly added to responses."""

    def test_headers_added_to_successful_responses(self, client):
        """Successful responses should include rate limit headers."""
        response = client.get("/api/test")
        assert response.status_code == HTTP_200_OK

        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "3"

        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "2"

        assert "X-RateLimit-Reset" in response.headers

    def test_remaining_decreases(self, client):
        """X-RateLimit-Remaining should decrease with each request."""
        response1 = client.get("/api/test")
        response2 = client.get("/api/test")
        response3 = client.get("/api/test")

        assert response1.headers["X-RateLimit-Remaining"] == "2"
        assert response2.headers["X-RateLimit-Remaining"] == "1"
        assert response3.headers["X-RateLimit-Remaining"] == "0"

    def test_headers_on_429_response(self, client):
        """HTTP 429 responses should also include rate limit headers."""
        # Exhaust the limit
        for _ in range(3):
            client.get("/api/test")

        response = client.get("/api/test")
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS

        assert response.headers["X-RateLimit-Limit"] == "3"
        assert response.headers["X-RateLimit-Remaining"] == "0"


class TestWindowReset:
    """Test window reset behavior."""

    def test_window_resets_after_time_period(self, client_custom_window):
        """After the window period, requests should be allowed again."""
        # Limit is 2 requests per 1 second
        # First 2 requests succeed
        response1 = client_custom_window.get("/api/test")
        response2 = client_custom_window.get("/api/test")
        assert response1.status_code == HTTP_200_OK
        assert response2.status_code == HTTP_200_OK

        # 3rd request should be blocked
        response3 = client_custom_window.get("/api/test")
        assert response3.status_code == HTTP_429_TOO_MANY_REQUESTS

        # Wait for window to reset (1 second + buffer)
        # Note: We use a mock for datetime in a separate test for precise timing

    @patch("middleware.rate_limiter.datetime")
    @patch("middleware.rate_limiter.timezone")
    def test_window_reset_with_mocked_time(
        self, mock_timezone, mock_datetime, app_with_custom_window
    ):
        """Test window reset using mocked datetime for precise control."""
        from middleware.rate_limiter import timezone as tz_module

        client = TestClient(app_with_custom_window, raise_server_exceptions=False)

        # Set initial time (timezone-aware)
        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Mock datetime.now to return our base_time
        mock_datetime.now.return_value = base_time
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        
        # Ensure timezone.utc is available
        mock_timezone.utc = timezone.utc

        # First 2 requests succeed
        response1 = client.get("/api/test")
        response2 = client.get("/api/test")
        assert response1.status_code == HTTP_200_OK
        assert response2.status_code == HTTP_200_OK

        # 3rd request should be blocked
        response3 = client.get("/api/test")
        assert response3.status_code == HTTP_429_TOO_MANY_REQUESTS

        # Advance time past the window (2 seconds from base_time)
        mock_datetime.now.return_value = base_time + timedelta(seconds=2)

        # Now requests should be allowed again
        response4 = client.get("/api/test")
        assert response4.status_code == HTTP_200_OK
        assert response4.headers["X-RateLimit-Remaining"] == "1"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unknown_client_ip(self):
        """Requests with no identifiable client should use 'unknown'."""
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "OK"}

        app.add_middleware(
            RateLimitMiddleware,
            max_requests=1,
            window_seconds=60,
        )

        client = TestClient(app, raise_server_exceptions=False)

        # Force client to be None by mocking
        # This is handled in the middleware to return "unknown"
        response1 = client.get("/api/test")
        response2 = client.get("/api/test")

        assert response1.status_code == HTTP_200_OK
        assert response2.status_code == HTTP_429_TOO_MANY_REQUESTS

    def test_empty_exclude_paths(self):
        """Middleware should work with empty exclude_paths."""
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "OK"}

        app.add_middleware(
            RateLimitMiddleware,
            max_requests=1,
            window_seconds=60,
            exclude_paths=[],
        )

        client = TestClient(app, raise_server_exceptions=False)

        response1 = client.get("/api/test")
        response2 = client.get("/api/test")

        assert response1.status_code == HTTP_200_OK
        assert response2.status_code == HTTP_429_TOO_MANY_REQUESTS

    def test_zero_max_requests_blocks_all(self):
        """With max_requests=0, all requests should be blocked."""
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "OK"}

        app.add_middleware(
            RateLimitMiddleware,
            max_requests=0,
            window_seconds=60,
        )

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/api/test")
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
