"""Factory functions for creating test data."""

from __future__ import annotations

from fi.gateway.types.chat.chat_completion import ChatCompletion, Choice
from fi.gateway.types.chat.chat_completion_message import ChatCompletionMessage, FunctionCall, ToolCall
from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.shared import Usage


def make_usage(
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
    total_tokens: int | None = None,
) -> Usage:
    return Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens if total_tokens is not None else prompt_tokens + completion_tokens,
    )


def make_agentcc_metadata(
    request_id: str = "req-test-001",
    trace_id: str = "trace-test-001",
    provider: str = "openai",
    latency_ms: int = 100,
    cost: float | None = None,
    cache_status: str | None = None,
    model_used: str | None = None,
) -> AgentCCMetadata:
    return AgentCCMetadata(
        request_id=request_id,
        trace_id=trace_id,
        provider=provider,
        latency_ms=latency_ms,
        cost=cost,
        cache_status=cache_status,
        model_used=model_used,
    )


def make_message(
    role: str = "assistant",
    content: str | None = "Hello!",
    tool_calls: list[ToolCall] | None = None,
) -> ChatCompletionMessage:
    return ChatCompletionMessage(role=role, content=content, tool_calls=tool_calls)


def make_tool_call(
    id: str = "call_001",
    name: str = "get_weather",
    arguments: str = '{"location": "NYC"}',
) -> ToolCall:
    return ToolCall(id=id, type="function", function=FunctionCall(name=name, arguments=arguments))


def make_completion(
    content: str = "Hello!",
    model: str = "gpt-4o",
    usage: Usage | None = None,
    agentcc: AgentCCMetadata | None = None,
    finish_reason: str = "stop",
    id: str = "chatcmpl-test",
    tool_calls: list[ToolCall] | None = None,
) -> ChatCompletion:
    message = make_message(content=content if not tool_calls else None, tool_calls=tool_calls)
    choice = Choice(index=0, message=message, finish_reason=finish_reason)
    comp = ChatCompletion(
        id=id,
        object="chat.completion",
        created=1700000000,
        model=model,
        choices=[choice],
        usage=usage or make_usage(),
        agentcc=agentcc,
    )
    return comp
