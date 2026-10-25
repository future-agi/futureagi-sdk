"""Embedding response types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.shared import Usage


class Embedding(BaseModel):
    object: str = "embedding"
    embedding: list[float]
    index: int
    model_config = ConfigDict(extra="allow")


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[Embedding]
    model: str
    usage: Usage | None = None
    agentcc: AgentCCMetadata | None = None
    model_config = ConfigDict(extra="allow")
