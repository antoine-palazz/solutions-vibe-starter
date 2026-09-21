from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/demo", tags=["Demo"])


class PingResult(BaseModel):
    message: str


@router.get("/ping", response_model=PingResult)
async def ping() -> PingResult:
    """A tiny rate-limited endpoint used to demonstrate the 429 response."""
    return PingResult(message="pong")
