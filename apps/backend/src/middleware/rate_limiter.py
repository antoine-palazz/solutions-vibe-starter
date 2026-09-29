"""Rate limiting middleware using Sliding Window algorithm.

This middleware implements a sliding window rate limiter to protect the API
from abuse and ensure fair usage. It stores request timestamps per client IP
and enforces configurable limits.

In a production environment with multiple workers, consider using a shared
store (like Redis) for cross-process rate limiting.
"""

from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Callable, Deque

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that limits request rate using a Sliding Window algorithm.

    The sliding window approach provides a smooth rate limiting by tracking
    individual request timestamps within a time window. Each request at time T
    counts for any window [T-window_size, T].

    Attributes:
        max_requests: Maximum number of requests allowed per window.
        window: Time window duration as a timedelta.
        exclude_paths: List of path prefixes to exclude from rate limiting.
        client_requests: Dictionary mapping client IPs to deque of timestamps.
    """

    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60,
        exclude_paths: list[str] | None = None,
    ) -> None:
        """Initialize the rate limiting middleware.

        Args:
            app: The FastAPI application.
            max_requests: Maximum requests allowed per window per client.
            window_seconds: Duration of the sliding window in seconds.
            exclude_paths: List of path prefixes to exclude (e.g., ["/api/health"]).
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.exclude_paths = exclude_paths or []
        self.client_requests: dict[str, Deque[datetime]] = {}

    def _get_client_ip(self, request: Request) -> str:
        """Extract the client IP address from the request.

        Checks for forwarded headers first (for clients behind proxies/load balancers),
        then falls back to the direct client host.

        Args:
            request: The incoming HTTP request.

        Returns:
            The client IP address as a string.
        """
        # Check for X-Forwarded-For header (may contain multiple IPs)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Check for X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to the direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _cleanup_expired_requests(self, client_ip: str, now: datetime) -> None:
        """Remove expired request timestamps for a client.

        This ensures we only keep requests within the sliding window,
        preventing memory growth from unbounded history.

        Args:
            client_ip: The client identifier.
            now: The current timestamp.
        """
        if client_ip not in self.client_requests:
            return

        # Remove timestamps that fall outside the window
        while (
            self.client_requests[client_ip]
            and now - self.client_requests[client_ip][0] > self.window
        ):
            self.client_requests[client_ip].popleft()

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> JSONResponse:
        """Process the request through the rate limiting middleware.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            JSONResponse with appropriate status code and rate limit headers.
        """
        client_ip = self._get_client_ip(request)
        request_path = request.url.path

        # Skip rate limiting for excluded paths
        if any(request_path.startswith(path) for path in self.exclude_paths):
            response = await call_next(request)
            return response

        now = datetime.now(timezone.utc)

        # Initialize client tracking if needed
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = deque()

        # Clean up expired requests
        self._cleanup_expired_requests(client_ip, now)

        # Check if rate limit is exceeded
        request_count = len(self.client_requests[client_ip])
        if request_count >= self.max_requests:
            logger.warning(
                "rate limit exceeded",
                client_ip=client_ip,
                path=request_path,
                request_count=request_count,
                max_requests=self.max_requests,
            )
            # Calculate reset timestamp: if deque is empty, use current time
            reset_timestamp = now
            if self.client_requests[client_ip]:
                reset_timestamp = self.client_requests[client_ip][0] + self.window
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "retry_after": int(self.window.total_seconds()),
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_timestamp.timestamp())),
                },
            )

        # Add current request timestamp
        self.client_requests[client_ip].append(now)

        # Call the next middleware/handler
        response = await call_next(request)

        # Add rate limit headers to the response
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.max_requests - request_count - 1)
        )
        response.headers["X-RateLimit-Reset"] = str(
            int((self.client_requests[client_ip][0] + self.window).timestamp())
        )

        return response
