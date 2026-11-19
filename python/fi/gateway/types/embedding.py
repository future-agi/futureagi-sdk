"""Embedding response types, accepting vectors and released base64 responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, ValidatorFunctionWrapHandler, field_validator

from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.shared import Usage


class EmbeddingUsage(Usage):
    """Embeddings carry prompt_tokens and total_tokens; completion_tokens defaults to 0."""

    completion_tokens: int = 0


class Embedding(BaseModel):
    """One embedding; decode base64 vectors with decode_base64_embedding."""

    object: str = "embedding"
    embedding: list[float] | str
    index: int
    model_config = ConfigDict(extra="allow")


from fi.gateway._deprecation import deprecated


@deprecated
def decode_base64_embedding(value: list[float] | str) -> list[float]:
    """Decode a packed little-endian float32 array, or copy an existing vector."""
    if not isinstance(value, str):
        return list(value)
    import base64
    import struct

    raw = base64.b64decode(value)
    return list(struct.unpack(f"<{len(raw) // 4}f", raw))


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[Embedding]
    model: str
    usage: Usage | None = None
    agentcc: AgentCCMetadata | None = None
    model_config = ConfigDict(extra="allow")

    @field_validator("usage", mode="wrap")
    @classmethod
    def _parse_embedding_usage(
        cls, value: Any, handler: ValidatorFunctionWrapHandler
    ) -> Usage | None:
        # Let the published field validate first, preserving strict/context flags
        # and supplied Usage instances. Only wire dictionaries need the subtype.
        usage = handler(value)
        if isinstance(value, dict) and usage is not None:
            return EmbeddingUsage.model_construct(
                _fields_set=usage.model_fields_set,
                **{name: getattr(usage, name) for name in Usage.model_fields},
            ).model_copy(update=usage.model_extra or {})
        return usage
