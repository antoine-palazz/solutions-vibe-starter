"""Minimal in-memory rate limiter (standard library only).

Dependency-free so it runs offline and adds no supply-chain surface — a good fit
for a regulated / on-prem context. This module has no FastAPI/Starlette import, so
`FixedWindowRateLimiter` can be unit-tested in isolation. The ASGI middleware that
uses it lives in `main.py`.

Note: the counters are per-process and in-memory. For a multi-worker or
multi-instance deployment, back this with a shared store (e.g. Redis).
"""

import os
import threading
import time
from collections import defaultdict


class FixedWindowRateLimiter:
    """Fixed-window counter: at most `max_requests` per `window_seconds` per key."""

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        # key -> (window_start, count)
        self._hits: dict[str, tuple[float, int]] = defaultdict(lambda: (0.0, 0))

    def is_allowed(self, key: str, now: float | None = None) -> bool:
        """Return True if a request for `key` is within the limit, else False."""
        now = time.monotonic() if now is None else now
        with self._lock:
            window_start, count = self._hits[key]
            if now - window_start >= self.window_seconds:
                # New window
                self._hits[key] = (now, 1)
                return True
            if count < self.max_requests:
                self._hits[key] = (window_start, count + 1)
                return True
            return False


def limiter_from_env() -> FixedWindowRateLimiter:
    """Build a limiter from env vars, with demo-friendly defaults."""
    max_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    window_seconds = float(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    return FixedWindowRateLimiter(max_requests=max_requests, window_seconds=window_seconds)
