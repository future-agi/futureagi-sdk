"""Tests for ChunkAccumulator — reassembles streaming chunks into ChatCompletion."""

from __future__ import annotations

from fi.gateway._streaming import ChunkAccumulator
from fi.gateway.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
    Delta,
    FunctionCallDelta,
    StreamChoice,
    ToolCallDelta,
)
from fi.gateway.types.shared import Usage


def _content_chunk(content: str, idx: int = 0, chunk_id: str = "abc") -> ChatCompletionChunk:
    return ChatCompletionChunk(
        id=chunk_id,
        object="chat.completion.chunk",
        created=1709000000,
        model="gpt-4o",
        choices=[StreamChoice(index=idx, delta=Delta(content=content), finish_reason=None)],
    )


def _role_chunk(role: str = "assistant", chunk_id: str = "abc") -> ChatCompletionChunk:
    return ChatCompletionChunk(
        id=chunk_id,
        object="chat.completion.chunk",
        created=1709000000,
        model="gpt-4o",
        choices=[StreamChoice(index=0, delta=Delta(role=role), finish_reason=None)],
    )


def _finish_chunk(reason: str = "stop", chunk_id: str = "abc") -> ChatCompletionChunk:
    return ChatCompletionChunk(
        id=chunk_id,
        object="chat.completion.chunk",
        created=1709000000,
        model="gpt-4o",
        choices=[StreamChoice(index=0, delta=Delta(), finish_reason=reason)],
    )


def _usage_chunk(prompt: int = 10, completion: int = 20, total: int = 30) -> ChatCompletionChunk:
    return ChatCompletionChunk(
        id="abc",
        object="chat.completion.chunk",
        created=1709000000,
        model="gpt-4o",
        choices=[],
        usage=Usage(prompt_tokens=prompt, completion_tokens=completion, total_tokens=total),
    )


def test_accumulate_content() -> None:
    acc = ChunkAccumulator()
    acc.add(_role_chunk())
    acc.add(_content_chunk("Hello"))
    acc.add(_content_chunk(" world"))
    acc.add(_content_chunk("!"))
    acc.add(_finish_chunk())

    result = acc.build()
    assert result.id == "abc"
    assert result.model == "gpt-4o"
    assert len(result.choices) == 1
    assert result.choices[0].message.content == "Hello world!"
    assert result.choices[0].message.role == "assistant"
    assert result.choices[0].finish_reason == "stop"


def test_accumulate_with_usage() -> None:
    acc = ChunkAccumulator()
    acc.add(_role_chunk())
    acc.add(_content_chunk("Hi"))
    acc.add(_finish_chunk())
    acc.add(_usage_chunk(10, 5, 15))

    result = acc.build()
    assert result.usage is not None
    assert result.usage.prompt_tokens == 10
    assert result.usage.completion_tokens == 5
    assert result.usage.total_tokens == 15


def test_accumulate_tool_calls() -> None:
    acc = ChunkAccumulator()
    acc.add(_role_chunk())

    # First tool call chunk: id + name start
    tc_chunk1 = ChatCompletionChunk(
        id="abc", object="chat.completion.chunk", created=1709000000, model="gpt-4o",
        choices=[StreamChoice(
            index=0,
            delta=Delta(tool_calls=[
                ToolCallDelta(index=0, id="call_1", type="function",
                              function=FunctionCallDelta(name="get_weather", arguments="")),
            ]),
            finish_reason=None,
        )],
    )
    acc.add(tc_chunk1)

    # Arguments streamed across chunks
    tc_chunk2 = ChatCompletionChunk(
        id="abc", object="chat.completion.chunk", created=1709000000, model="gpt-4o",
        choices=[StreamChoice(
            index=0,
            delta=Delta(tool_calls=[
                ToolCallDelta(index=0, function=FunctionCallDelta(arguments='{"location')),
            ]),
            finish_reason=None,
        )],
    )
    acc.add(tc_chunk2)

    tc_chunk3 = ChatCompletionChunk(
        id="abc", object="chat.completion.chunk", created=1709000000, model="gpt-4o",
        choices=[StreamChoice(
            index=0,
            delta=Delta(tool_calls=[
                ToolCallDelta(index=0, function=FunctionCallDelta(arguments='": "London"}')),
            ]),
            finish_reason=None,
        )],
    )
    acc.add(tc_chunk3)

    acc.add(_finish_chunk("tool_calls"))

    result = acc.build()
    msg = result.choices[0].message
    assert msg.content is None
    assert msg.tool_calls is not None
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0].id == "call_1"
    assert msg.tool_calls[0].function.name == "get_weather"
    assert msg.tool_calls[0].function.arguments == '{"location": "London"}'


def test_accumulate_multiple_choices() -> None:
    acc = ChunkAccumulator()
    acc.add(_content_chunk("A", idx=0))
    acc.add(_content_chunk("B", idx=1))
    acc.add(_content_chunk("!", idx=0))
    acc.add(_content_chunk("!", idx=1))

    result = acc.build()
    assert len(result.choices) == 2
    assert result.choices[0].message.content == "A!"
    assert result.choices[1].message.content == "B!"


def test_build_empty_accumulator() -> None:
    acc = ChunkAccumulator()
    result = acc.build()
    assert result.id == ""
    assert result.model == ""
    assert len(result.choices) == 0
