"""``completions.create(stream=True)`` yields the text completion chunks the gateway relays.

A legacy completions stream carries ``{"object": "text_completion", "choices": [{"text":
...}]}`` chunks, with no ``delta``. agentcc 1.x parsed them as chat chunks, so the first
real chunk raised ``StreamError("Stream interrupted: ... choices.0.delta Field
required")``. Each chunk is now a ``Completion``; a cache-hit JSON answer is one
``Completion``; a gateway error frame still raises a typed ``StreamError``.
"""

from __future__ import annotations

import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError
from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk
from fi.gateway.types.completion import Completion

GW = "http://127.0.0.1:8090"


def _chunk(text: str, finish: str | None) -> str:
    return json.dumps(
        {
            "id": "cmpl-1",
            "object": "text_completion",
            "created": 1,
            "model": "gpt-3.5-turbo-instruct",
            "choices": [{"index": 0, "text": text, "finish_reason": finish}],
        }
    )


SSE = (
    f"data: {_chunk(' wor', None)}\n\ndata: {_chunk('ld', 'stop')}\n\ndata: [DONE]\n\n"
)
CACHED = {
    "id": "cmpl-c",
    "object": "text_completion",
    "created": 1,
    "model": "gpt-3.5-turbo-instruct",
    "choices": [{"index": 0, "text": "cached", "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}
ERROR = (
    f"data: {_chunk('Hel', None)}\n\n"
    'data: {"error":{"type":"guardrail_error","code":"stream_blocked",'
    '"message":"blocked","param":null}}\n\n'
)


def _answer(kind: str) -> httpx.Response:
    if kind == "cached":
        return httpx.Response(200, json=CACHED)
    body = SSE if kind == "sse" else ERROR
    return httpx.Response(
        200, headers={"content-type": "text/event-stream"}, content=body.encode()
    )


def _sync(kind: str) -> AgentCC:
    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(
            transport=httpx.MockTransport(lambda request: _answer(kind))
        ),
    )


def _async(kind: str) -> AsyncAgentCC:
    async def handler(request: httpx.Request) -> httpx.Response:
        return _answer(kind)

    return AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


def test_each_chunk_is_a_completion() -> None:
    stream = _sync("sse").completions.create(model="m", prompt="Hello", stream=True)
    chunks = list(stream)
    assert [type(c) for c in chunks] == [Completion, Completion]
    assert "".join(c.choices[0].text for c in chunks) == " world"
    assert chunks[-1].choices[0].finish_reason == "stop"


def test_a_cache_hit_json_answer_is_one_completion() -> None:
    stream = _sync("cached").completions.create(model="m", prompt="Hello", stream=True)
    (only,) = list(stream)
    assert isinstance(only, Completion)
    assert only.choices[0].text == "cached"
    assert only.usage is not None and only.usage.total_tokens == 2


def test_a_gateway_error_frame_raises_a_typed_stream_error() -> None:
    stream = _sync("error").completions.create(model="m", prompt="Hello", stream=True)
    seen = []
    with pytest.raises(StreamError) as raised:
        for chunk in stream:
            seen.append(chunk.choices[0].text)
    assert seen == ["Hel"]
    assert (raised.value.type, raised.value.code) == (
        "guardrail_error",
        "stream_blocked",
    )
    assert stream.response.is_closed


def test_chat_streams_still_yield_chat_chunks() -> None:
    chat = {
        "id": "c",
        "object": "chat.completion",
        "created": 1,
        "model": "m",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
    }
    client = AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json=chat))
        ),
    )
    stream = client.chat.completions.create(model="m", messages=[], stream=True)
    (only,) = list(stream)
    assert isinstance(only, ChatCompletionChunk)
    assert only.choices[0].delta.content == "hi"


async def test_the_async_stream_yields_completions_too() -> None:
    stream = await _async("sse").completions.create(
        model="m", prompt="Hello", stream=True
    )
    texts = [c.choices[0].text async for c in stream]
    assert texts == [" wor", "ld"]
    cached = await _async("cached").completions.create(
        model="m", prompt="Hello", stream=True
    )
    items = [c async for c in cached]
    assert [type(c) for c in items] == [Completion]
    failing = await _async("error").completions.create(
        model="m", prompt="Hello", stream=True
    )
    with pytest.raises(StreamError, match="blocked"):
        async for _ in failing:
            pass
