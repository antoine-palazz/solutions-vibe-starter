import os
import socket

from fastapi import APIRouter
from pydantic import BaseModel

from status import ServiceStatus, Status

router = APIRouter(prefix="/health", tags=["Health"])

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))


class HealthCheckResult(BaseModel):
    status: str
    services: dict[str, ServiceStatus]


def _check_database() -> ServiceStatus:
    """Probe the database by opening a TCP connection."""
    with socket.create_connection((DB_HOST, DB_PORT), timeout=1):
        return ServiceStatus(status=Status.OK)


@router.get("/check", response_model=HealthCheckResult)
async def health_check() -> HealthCheckResult:
    services = {
        "database": _check_database(),
    }

    overall_status = "OK" if all(s.status == Status.OK for s in services.values()) else "DEGRADED"
    return HealthCheckResult(status=overall_status, services=services)
