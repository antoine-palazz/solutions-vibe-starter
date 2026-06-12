"""Minimal service-status primitives used by the health check.

In a real project these usually live in a shared package; they are inlined here
to keep the example self-contained.
"""

from enum import Enum

from pydantic import BaseModel


class Status(str, Enum):
    OK = "OK"
    ERROR = "ERROR"
    NOT_INITIALIZED = "NOT_INITIALIZED"


class ServiceStatus(BaseModel):
    status: Status
    details: str | None = None
