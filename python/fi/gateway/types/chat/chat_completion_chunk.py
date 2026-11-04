"""ChatCompletionChunk — the streaming response model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from fi.gateway.types.shared import Usage


class FunctionCallDelta(BaseModel):
    name: str | None = None
    arguments: str | None = None


class ToolCallDelta(BaseModel):
    index: int
    id: str | None = None
    type: str | None = None
    function: FunctionCallDelta | None = None


class Delta(BaseModel):
    role: str | None = None
    content: str | None = None
    tool_calls: list[ToolCallDelta] | None = None


class StreamChoice(BaseModel):
    model_config = ConfigDict(extra="allow")

    index: int
    delta: Delta
    finish_reason: str | None = None
    logprobs: Any = None


class ChatCompletionChunk(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    object: str
    created: int
    model: str
    choices: list[StreamChoice]
    usage: Usage | None = None
    system_fingerprint: str | None = None
