"""Chat completion type definitions."""

from __future__ import annotations

from fi.gateway.types.chat.chat_completion import ChatCompletion, Choice
from fi.gateway.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
    Delta,
    FunctionCallDelta,
    StreamChoice,
    ToolCallDelta,
)
from fi.gateway.types.chat.chat_completion_message import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
    FunctionCall,
    FunctionCallParam,
    ToolCall,
)
from fi.gateway.types.chat.completion_create_params import CompletionCreateParams, StreamOptions

__all__ = [
    "ChatCompletion",
    "ChatCompletionAssistantMessageParam",
    "ChatCompletionChunk",
    "ChatCompletionMessage",
    "ChatCompletionMessageParam",
    "ChatCompletionMessageToolCallParam",
    "ChatCompletionSystemMessageParam",
    "ChatCompletionToolMessageParam",
    "ChatCompletionUserMessageParam",
    "Choice",
    "CompletionCreateParams",
    "Delta",
    "FunctionCall",
    "FunctionCallDelta",
    "FunctionCallParam",
    "StreamChoice",
    "StreamOptions",
    "ToolCall",
    "ToolCallDelta",
]
