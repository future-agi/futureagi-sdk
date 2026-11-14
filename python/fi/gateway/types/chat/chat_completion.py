"""ChatCompletion — the primary response model for chat completions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from fi.gateway.types.chat.chat_completion_message import ChatCompletionMessage
from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.shared import Usage


class Choice(BaseModel):
    model_config = ConfigDict(extra="allow")

    index: int
    message: ChatCompletionMessage
    finish_reason: str | None = None
    logprobs: Any = None


class ChatCompletion(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    object: str
    created: int
    model: str
    choices: list[Choice]
    usage: Usage | None = None
    system_fingerprint: str | None = None
    service_tier: str | None = None
    agentcc: AgentCCMetadata | None = None
