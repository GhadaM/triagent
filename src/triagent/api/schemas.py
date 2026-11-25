"""Pydantic request and response models for the API."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness check payload."""

    status: Literal["ok"]
    version: str
    env: str
