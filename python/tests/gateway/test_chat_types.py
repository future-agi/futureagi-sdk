"""Tests for chat completion types — input TypedDicts and output Pydantic models."""

from __future__ import annotations

# --- Fixture data matching real gateway response format ---

COMPLETION_JSON = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1709000000,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?",
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 12,
        "total_tokens": 22,
    },
    "system_fingerprint": "fp_abc123",
}

TOOL_CALL_COMPLETION_JSON = {
    "id": "chatcmpl-tool-123",
    "object": "chat.completion",
    "created": 1709000000,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_abc",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "London"}',
                        },
                    }
                ],
            },
            "finish_reason": "tool_calls",
        }
    ],
    "usage": {
        "prompt_tokens": 20,
        "completion_tokens": 15,
        "total_tokens": 35,
    },
}

CHUNK_JSON = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion.chunk",
    "created": 1709000000,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "delta": {
                "role": "assistant",
                "content": "Hello",
            },
            "finish_reason": None,
        }
    ],
}

TOOL_CALL_CHUNK_JSON = {
    "id": "chatcmpl-tool-123",
    "object": "chat.completion.chunk",
    "created": 1709000000,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "delta": {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "call_abc",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": ""},
                    }
                ],
            },
            "finish_reason": None,
        }
    ],
}


# --- ChatCompletion tests ---


def test_chat_completion_parse() -> None:
    from fi.gateway.types.chat.chat_completion import ChatCompletion

    comp = ChatCompletion.model_validate(COMPLETION_JSON)
    assert comp.id == "chatcmpl-abc123"
    assert comp.object == "chat.completion"
    assert comp.model == "gpt-4o"
    assert comp.created == 1709000000
    assert comp.system_fingerprint == "fp_abc123"


def test_chat_completion_choices_access() -> None:
    from fi.gateway.types.chat.chat_completion import ChatCompletion

    comp = ChatCompletion.model_validate(COMPLETION_JSON)
    assert len(comp.choices) == 1
    assert comp.choices[0].index == 0
    assert comp.choices[0].message.content == "Hello! How can I help you today?"
    assert comp.choices[0].message.role == "assistant"
    assert comp.choices[0].finish_reason == "stop"


def test_chat_completion_usage() -> None:
    from fi.gateway.types.chat.chat_completion import ChatCompletion

    comp = ChatCompletion.model_validate(COMPLETION_JSON)
    assert comp.usage is not None
    assert comp.usage.prompt_tokens == 10
    assert comp.usage.completion_tokens == 12
    assert comp.usage.total_tokens == 22


def test_chat_completion_extra_fields() -> None:
    from fi.gateway.types.chat.chat_completion import ChatCompletion

    data = {**COMPLETION_JSON, "future_field": "value"}
    comp = ChatCompletion.model_validate(data)
    assert comp.id == "chatcmpl-abc123"
    dumped = comp.model_dump()
    assert dumped["future_field"] == "value"


def test_chat_completion_tool_calls() -> None:
    from fi.gateway.types.chat.chat_completion import ChatCompletion

    comp = ChatCompletion.model_validate(TOOL_CALL_COMPLETION_JSON)
    msg = comp.choices[0].message
    assert msg.content is None
    assert msg.tool_calls is not None
    assert len(msg.tool_calls) == 1
    tc = msg.tool_calls[0]
    assert tc.id == "call_abc"
    assert tc.type == "function"
    assert tc.function.name == "get_weather"
    assert tc.function.arguments == '{"location": "London"}'


def test_chat_completion_agentcc_field_default_none() -> None:
    from fi.gateway.types.chat.chat_completion import ChatCompletion

    comp = ChatCompletion.model_validate(COMPLETION_JSON)
    assert comp.agentcc is None


# --- ChatCompletionChunk tests ---


def test_chunk_parse() -> None:
    from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk

    chunk = ChatCompletionChunk.model_validate(CHUNK_JSON)
    assert chunk.id == "chatcmpl-abc123"
    assert chunk.object == "chat.completion.chunk"
    assert chunk.model == "gpt-4o"


def test_chunk_delta_content() -> None:
    from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk

    chunk = ChatCompletionChunk.model_validate(CHUNK_JSON)
    assert len(chunk.choices) == 1
    assert chunk.choices[0].delta.content == "Hello"
    assert chunk.choices[0].delta.role == "assistant"
    assert chunk.choices[0].finish_reason is None


def test_chunk_delta_tool_calls() -> None:
    from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk

    chunk = ChatCompletionChunk.model_validate(TOOL_CALL_CHUNK_JSON)
    delta = chunk.choices[0].delta
    assert delta.tool_calls is not None
    assert len(delta.tool_calls) == 1
    assert delta.tool_calls[0].index == 0
    assert delta.tool_calls[0].function is not None
    assert delta.tool_calls[0].function.name == "get_weather"


def test_chunk_extra_fields() -> None:
    from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk

    data = {**CHUNK_JSON, "unknown_field": True}
    chunk = ChatCompletionChunk.model_validate(data)
    assert chunk.id == "chatcmpl-abc123"


# --- Input TypedDict tests ---


def test_system_message_param() -> None:
    from fi.gateway.types.chat.chat_completion_message import ChatCompletionSystemMessageParam

    msg: ChatCompletionSystemMessageParam = {"role": "system", "content": "You are helpful."}
    assert msg["role"] == "system"
    assert msg["content"] == "You are helpful."


def test_user_message_param() -> None:
    from fi.gateway.types.chat.chat_completion_message import ChatCompletionUserMessageParam

    msg: ChatCompletionUserMessageParam = {"role": "user", "content": "Hello"}
    assert msg["role"] == "user"


def test_assistant_message_param_with_tool_calls() -> None:
    from fi.gateway.types.chat.chat_completion_message import ChatCompletionAssistantMessageParam

    msg: ChatCompletionAssistantMessageParam = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": "call_1", "type": "function", "function": {"name": "test", "arguments": "{}"}},
        ],
    }
    assert msg["role"] == "assistant"
    assert len(msg["tool_calls"]) == 1


def test_tool_message_param() -> None:
    from fi.gateway.types.chat.chat_completion_message import ChatCompletionToolMessageParam

    msg: ChatCompletionToolMessageParam = {"role": "tool", "content": "result", "tool_call_id": "call_1"}
    assert msg["tool_call_id"] == "call_1"


def test_completion_create_params() -> None:
    from fi.gateway.types.chat.completion_create_params import CompletionCreateParams

    params: CompletionCreateParams = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        "session_id": "sess-1",
        "cache_ttl": "10m",
    }
    assert params["model"] == "gpt-4o"
    assert params["session_id"] == "sess-1"


# --- Re-export tests ---


def test_chat_types_importable() -> None:
    from fi.gateway.types.chat import (
        ChatCompletion,
        ChatCompletionChunk,
        ChatCompletionMessage,
        ChatCompletionMessageParam,
        Choice,
        CompletionCreateParams,
        Delta,
        FunctionCall,
        StreamChoice,
        StreamOptions,
        ToolCall,
        ToolCallDelta,
    )

    assert ChatCompletion is not None
    assert ChatCompletionChunk is not None
    assert ChatCompletionMessage is not None
    assert Choice is not None
    assert Delta is not None
    assert StreamChoice is not None
    assert ToolCall is not None
    assert FunctionCall is not None
    assert ToolCallDelta is not None
    assert CompletionCreateParams is not None
    assert StreamOptions is not None
    assert ChatCompletionMessageParam is not None
