"""Model refusal text survives raw streams and accumulated chat completions."""

from __future__ import annotations

import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, AsyncGateway, Gateway
from fi.gateway._streaming import ChunkAccumulator, stream_chunk_builder
from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk, Delta

REFUSAL_PARTS = ["I cannot help ", "with that request."]
REFUSAL = "".join(REFUSAL_PARTS)
MESSAGES = [{"role": "user", "content": "Hello"}]
USAGE = {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}


def _chunk(delta, index=0, finish_reason=None):
    return {
        "id": "chatcmpl-synthetic",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": "synthetic-model",
        "choices": [{"index": index, "delta": delta, "finish_reason": finish_reason}],
    }


def _completion():
    return {
        "id": "chatcmpl-synthetic",
        "object": "chat.completion",
        "created": 0,
        "model": "synthetic-model",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": None, "refusal": REFUSAL},
            "finish_reason": "stop",
        }],
        "usage": USAGE,
    }


@pytest.fixture(params=["sse", "cache"])
def response_kind(request):
    return request.param


@pytest.fixture
def transport(response_kind):
    def send(request):
        body = json.loads(request.content)
        if not body.get("stream") or response_kind == "cache":
            return httpx.Response(200, json=_completion())
        frames = [
            _chunk({"role": "assistant", "content": None, "refusal": REFUSAL_PARTS[0]}),
            _chunk({"refusal": REFUSAL_PARTS[1]}),
            _chunk({}, finish_reason="stop"),
            {**_chunk({}), "choices": [], "usage": USAGE},
        ]
        data = "".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"},
            content=(data + "data: [DONE]\n\n").encode(),
        )

    return httpx.MockTransport(send)


def _assert_raw_refusal(chunks, response_kind):
    # Attribute access and serialization must both retain the wire field.
    deltas = [choice.delta for chunk in chunks for choice in chunk.choices]
    expected = REFUSAL_PARTS + [None] if response_kind == "sse" else [REFUSAL]
    assert [delta.model_dump().get("refusal") for delta in deltas] == expected
    assert [delta.refusal for delta in deltas] == expected
    assert all(delta.content is None for delta in deltas)
    _assert_final_refusal(stream_chunk_builder(chunks))


def _assert_final_refusal(completion):
    choice = completion.choices[0]
    assert choice.message.model_dump().get("refusal") == REFUSAL
    assert choice.message.refusal == REFUSAL
    assert choice.message.content is None
    assert choice.message.role == "assistant"
    assert choice.finish_reason == "stop"
    assert completion.usage.model_dump(exclude_none=True) == USAGE


@pytest.mark.parametrize("client_cls", [AgentCC, Gateway])
def test_raw_stream_retains_refusal(client_cls, transport, response_kind):
    with httpx.Client(transport=transport) as http:
        client = client_cls(
            api_key="synthetic-virtual-key", base_url="https://gateway.example.test",
            http_client=http,
        )
        control = client.chat.completions.create(model="synthetic-model", messages=MESSAGES)
        assert control.choices[0].message.refusal == REFUSAL
        chunks = list(client.chat.completions.create(
            model="synthetic-model", messages=MESSAGES, stream=True,
        ))
        _assert_raw_refusal(chunks, response_kind)


@pytest.mark.parametrize("client_cls", [AgentCC, Gateway])
def test_stream_manager_retains_refusal(client_cls, transport):
    with httpx.Client(transport=transport) as http:
        client = client_cls(
            api_key="synthetic-virtual-key", base_url="https://gateway.example.test",
            http_client=http,
        )
        with client.chat.completions.stream(
            model="synthetic-model", messages=MESSAGES,
        ) as stream:
            _assert_final_refusal(stream.get_final_completion())
            assert stream.get_final_message().refusal == REFUSAL


@pytest.mark.asyncio
@pytest.mark.parametrize("client_cls", [AsyncAgentCC, AsyncGateway])
async def test_async_raw_stream_retains_refusal(client_cls, transport, response_kind):
    async with httpx.AsyncClient(transport=transport) as http:
        client = client_cls(
            api_key="synthetic-virtual-key", base_url="https://gateway.example.test",
            http_client=http,
        )
        control = await client.chat.completions.create(model="synthetic-model", messages=MESSAGES)
        assert control.choices[0].message.refusal == REFUSAL
        stream = await client.chat.completions.create(
            model="synthetic-model", messages=MESSAGES, stream=True,
        )
        _assert_raw_refusal([chunk async for chunk in stream], response_kind)


@pytest.mark.asyncio
@pytest.mark.parametrize("client_cls", [AsyncAgentCC, AsyncGateway])
async def test_async_stream_manager_retains_refusal(client_cls, transport):
    async with httpx.AsyncClient(transport=transport) as http:
        client = client_cls(
            api_key="synthetic-virtual-key", base_url="https://gateway.example.test",
            http_client=http,
        )
        async with await client.chat.completions.stream(
            model="synthetic-model", messages=MESSAGES,
        ) as stream:
            _assert_final_refusal(await stream.get_final_completion())
            assert (await stream.get_final_message()).refusal == REFUSAL


def test_accumulator_keeps_refusal_separate_per_choice_and_from_content_and_tools():
    frames = [
        _chunk({"role": "assistant", "refusal": "Cannot "}, index=1),
        _chunk({"role": "assistant", "content": "Hello", "refusal": "Not "}),
        _chunk({"refusal": "answer."}, index=1, finish_reason="stop"),
        _chunk({"content": "!", "refusal": "that.", "tool_calls": [{
            "index": 0, "id": "call-synthetic", "type": "function",
            "function": {"name": "example", "arguments": "{}"},
        }]}, finish_reason="tool_calls"),
    ]
    acc = ChunkAccumulator()
    for frame in frames:
        acc.add(ChatCompletionChunk.model_validate(frame))
    result = acc.build()
    assert [choice.index for choice in result.choices] == [0, 1]
    first, second = [choice.message for choice in result.choices]
    assert first.model_dump().get("refusal") == "Not that."
    assert second.model_dump().get("refusal") == "Cannot answer."
    assert first.content == "Hello!"
    assert second.content is None
    assert first.tool_calls[0].function.arguments == "{}"
    assert second.tool_calls is None
    assert [choice.finish_reason for choice in result.choices] == ["tool_calls", "stop"]
    assert acc.build() == result


@pytest.mark.parametrize("delta,expected", [
    ({}, None),
    ({"refusal": None}, None),
    ({"refusal": ""}, ""),
    ({"refusal": "No."}, "No."),
])
def test_missing_null_and_empty_refusal(delta, expected):
    typed = Delta.model_validate(delta)
    assert typed.refusal == expected
    acc = ChunkAccumulator()
    acc.add(ChatCompletionChunk.model_validate(_chunk(delta)))
    # Role-only, null and terminal deltas must not erase prior refusal fragments.
    acc.add(ChatCompletionChunk.model_validate(_chunk({"role": "assistant", "refusal": None})))
    acc.add(ChatCompletionChunk.model_validate(_chunk({}, finish_reason="stop")))
    message = acc.build().choices[0].message
    assert message.refusal == expected
    assert message.content is None
