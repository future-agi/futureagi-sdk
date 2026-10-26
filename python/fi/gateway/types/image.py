"""Image generation response types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from fi.gateway.types.agentcc_metadata import AgentCCMetadata


class Image(BaseModel):
    url: str | None = None
    b64_json: str | None = None
    revised_prompt: str | None = None
    model_config = ConfigDict(extra="allow")


class ImageResponse(BaseModel):
    created: int
    data: list[Image]
    agentcc: AgentCCMetadata | None = None
    model_config = ConfigDict(extra="allow")
