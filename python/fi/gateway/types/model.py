"""Model list/retrieve response types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    """A single model object returned by the gateway."""

    model_config = ConfigDict(extra="allow")

    id: str
    object: str
    created: int
    owned_by: str


class ModelList(BaseModel):
    """Response from GET /v1/models."""

    object: str
    data: list[Model]
