"""Chat completion message types — input TypedDicts and output Pydantic models."""

from __future__ import annotations

from typing import Any, Union

from pydantic import BaseModel, ConfigDict
from typing_extensions import Literal, Required, TypedDict

# --- Input types (TypedDicts for zero-overhead message construction) ---


class FunctionCallParam(TypedDict):
    name: Required[str]
    arguments: Required[str]


class ChatCompletionMessageToolCallParam(TypedDict):
    id: Required[str]
    type: Required[Literal["function"]]
    function: Required[FunctionCallParam]


class ChatCompletionSystemMessageParam(TypedDict, total=False):
    role: Required[Literal["system"]]
    content: Required[str]
    name: str


class ChatCompletionUserMessageParam(TypedDict, total=False):
    role: Required[Literal["user"]]
    content: Required[str | list[Any]]
    name: str


class ChatCompletionAssistantMessageParam(TypedDict, total=False):
    role: Required[Literal["assistant"]]
    content: str | None
    tool_calls: list[ChatCompletionMessageToolCallParam]
    name: str


class ChatCompletionToolMessageParam(TypedDict):
    role: Required[Literal["tool"]]
    content: Required[str]
    tool_call_id: Required[str]


ChatCompletionMessageParam = Union[
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionToolMessageParam,
]


# --- Output types (Pydantic models for validated responses) ---


class FunctionCall(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: str
    function: FunctionCall


class ChatCompletionMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    name: str | None = None
