"""Batch request/response types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class BatchResponse(BaseModel):
    """Response from the batch API."""

    model_config = ConfigDict(extra="allow")

    batch_id: str
    status: str
    total: int
    max_concurrency: int | None = None
    created_at: str | None = None
    completed_at: str | None = None
    results: list[Any] | None = None
    summary: dict[str, Any] | None = None
