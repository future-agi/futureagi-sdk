"""Rerank response types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RerankResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    index: int
    relevance_score: float
    document: str | None = None  # Only present if return_documents=True


class RerankResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    results: list[RerankResult] = []
    model: str | None = None
    usage: dict | None = None  # Some providers return token usage
