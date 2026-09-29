import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from middleware.rate_limiter import RateLimitMiddleware
from routers import health

APP_NAME = os.getenv("APP_NAME", "solutions-vibe-starter")
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_EXCLUDE_PATHS = os.getenv(
    "RATE_LIMIT_EXCLUDE_PATHS", "/api/health"
).split(",")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("application startup", app=APP_NAME)
    yield
    logger.info("application shutdown", app=APP_NAME)


app = FastAPI(title=f"{APP_NAME} API", version="0.1.0", lifespan=lifespan)

# --- CORS for the local Next.js frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate Limiting ---
app.add_middleware(
    RateLimitMiddleware,
    max_requests=RATE_LIMIT_MAX_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    exclude_paths=RATE_LIMIT_EXCLUDE_PATHS,
)

# --- Routers ---
app.include_router(health.router, prefix="/api")
