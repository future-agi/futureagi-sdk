"""Embedding response types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.shared import Usage


class Embedding(BaseModel):
    """One embedding: a list of floats, or the base64 string the provider returns for
    ``encoding_format="base64"`` (decode it with :func:`decode_base64_embedding`)."""

    object: str = "embedding"
    embedding: list[float] | str
    index: int
    model_config = ConfigDict(extra="allow")


def decode_base64_embedding(value: list[float] | str) -> list[float]:
    """The embedding as floats, whichever representation the provider used (base64 is a
    packed little-endian float32 array)."""
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
