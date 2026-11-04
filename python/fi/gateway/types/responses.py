"""Responses API types — OpenAI next-gen /v1/responses endpoint."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ContentPart(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = "output_text"
    text: str | None = None


class ResponseOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str | None = None
    content: list[ContentPart] = []


class ResponseUsage(BaseModel):
    model_config = ConfigDict(extra="allow")

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ResponseObject(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "response"
    model: str | None = None
    created_at: int | None = None
    status: str | None = None
    output: list[ResponseOutput] = []
    usage: ResponseUsage | None = None
    metadata: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class ResponseStreamEvent(BaseModel):
    """One server-sent event of a streamed `/v1/responses` call.

    `delta` is the text fragment of `response.output_text.delta` and
    `response.function_call_arguments.delta` events (a string), or a structured delta on
    others; `response` carries the full object on `response.created` / `response.completed`.
    """

    model_config = ConfigDict(extra="allow")

    type: str
    response: ResponseObject | None = None
    delta: Any = None
    sequence_number: int | None = None
    output_index: int | None = None
    content_index: int | None = None
    item_id: str | None = None
