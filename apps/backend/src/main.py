import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from routers import health

APP_NAME = os.getenv("APP_NAME", "solutions-vibe-starter")


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

# --- Routers ---
app.include_router(health.router, prefix="/api")
