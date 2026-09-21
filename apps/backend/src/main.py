import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from rate_limit import FixedWindowRateLimiter, limiter_from_env
from routers import demo, health

APP_NAME = os.getenv("APP_NAME", "solutions-vibe-starter")

# Health checks must stay un-throttled so probes always get a stable signal.
RATE_LIMIT_EXCLUDE_PREFIXES = ("/api/health",)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply a fixed-window rate limiter per client IP, skipping excluded paths."""

    def __init__(self, app, limiter: FixedWindowRateLimiter, exclude_prefixes: tuple[str, ...]) -> None:
        super().__init__(app)
        self.limiter = limiter
        self.exclude_prefixes = exclude_prefixes

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(prefix) for prefix in self.exclude_prefixes):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        if not self.limiter.is_allowed(client_ip):
            logger.warning("rate limit exceeded", name="rate_limit", client=client_ip, path=path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )
        return await call_next(request)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("application startup", app=APP_NAME)
    yield
    logger.info("application shutdown", app=APP_NAME)


app = FastAPI(title=f"{APP_NAME} API", version="0.1.0", lifespan=lifespan)

# Middlewares are applied outermost-first in reverse order of registration, so
# CORS is added last to stay the outermost layer — even a 429 then carries CORS
# headers.

# --- Rate limiting (health checks excluded) ---
app.add_middleware(
    RateLimitMiddleware,
    limiter=limiter_from_env(),
    exclude_prefixes=RATE_LIMIT_EXCLUDE_PREFIXES,
)

# --- CORS for the local Next.js frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(health.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
