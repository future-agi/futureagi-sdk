"""Legacy text completion types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.shared import Usage


class CompletionChoice(BaseModel):
    text: str
    index: int
    logprobs: object | None = None
    finish_reason: str | None = None
    model_config = ConfigDict(extra="allow")


class Completion(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[CompletionChoice]
    usage: Usage | None = None
    system_fingerprint: str | None = None
    agentcc: AgentCCMetadata | None = None
    model_config = ConfigDict(extra="allow")
