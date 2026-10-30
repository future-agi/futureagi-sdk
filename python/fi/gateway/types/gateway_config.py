"""Gateway health-check response types."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response from the gateway health/readiness endpoints."""

    status: str
