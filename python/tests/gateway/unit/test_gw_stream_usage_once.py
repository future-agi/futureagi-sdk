"""Released streaming semantics: one ``usage`` event per usage-bearing chunk.

Trailing chunks are not deduplicated or replaced with a final-only aggregate.
Consumers must not add cumulative usage snapshots. The final completion keeps
the last reported usage; the raw stream still yields every chunk. Historical
test ids are retained even where their old names describe deduplication.

``RECORDED`` is the frame list the gateway sent on a live stack for the
``usage_chunk_with_empty_choices`` case (the mock upstream's ``usage-chunk`` scenario),
byte for byte: the same usage in two trailing ``choices: []`` chunks.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError

GW = "http://127.0.0.1:8090"
SSE = {"content-type": "text/event-stream"}
MSG = [{"role": "user", "content": "hi"}]
_HEAD = '{"id":"chatcmpl-sdk101","object":"chat.completion.chunk","created":1761177600,"model":"gpt-4o-mini",'
RECORDED = [
    _HEAD
    + '"choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"},"finish_reason":null}]}',
    _HEAD + '"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}',
    _HEAD
    + '"choices":[],"usage":{"prompt_tokens":9,"completion_tokens":1,"total_tokens":10}}',
    _HEAD
    + '"choices":[],"usage":{"prompt_tokens":9,"completion_tokens":1,"total_tokens":10}}',
    "[DONE]",
]


def _usage(total: int) -> dict[str, int]:
    return {"prompt_tokens": 9, "completion_tokens": total - 9, "total_tokens": total}


def _chunk(choices: list[dict[str, Any]], usage: dict[str, int] | None = None) -> str:
    obj: dict[str, Any] = {
        "id": "c",
        "object": "chat.completion.chunk",
        "created": 1,
        "model": "m",
        "choices": choices,
    }
    if usage is not None:
        obj["usage"] = usage
    return json.dumps(obj)


# The C79 shape: usage in the finish chunk, then the gateway's metadata chunk repeats it.
FINISH_THEN_TRAILING = [
    _chunk([{"index": 0, "delta": {"role": "assistant", "content": "Hello"}}]),
    _chunk([{"index": 0, "delta": {"content": " world"}}]),
    _chunk([{"index": 0, "delta": {}, "finish_reason": "stop"}], _usage(11)),
    _chunk([], _usage(11)),
    "[DONE]",
]


def _body(frames: list[str]) -> bytes:
    return "".join(f"data: {f}\n\n" for f in frames).encode()


def _client(frames: list[str]) -> AgentCC:
    body = _body(frames)
    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, headers=SSE, content=body)
            )
        ),
    )


def _async_client(frames: list[str]) -> AsyncAgentCC:
    body = _body(frames)

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers=SSE, content=body)

    return AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


def test_the_recorded_frames_repeat_the_usage() -> None:
    carrying = [f for f in RECORDED[:-1] if json.loads(f).get("usage")]
    assert len(carrying) == 2 and carrying[0] == carrying[1]
    assert all(json.loads(f)["choices"] == [] for f in carrying)


def test_one_usage_event_for_the_recorded_frames() -> None:
    with _client(RECORDED).chat.completions.stream(model="m", messages=MSG) as s:
        events = list(s)
        final = s.get_final_completion()
    assert [e.type for e in events] == ["content", "usage", "usage", "done"]
    assert events[1].usage is not None and events[1].usage.total_tokens == 10
    assert [e.usage.total_tokens for e in events if e.type == "usage"] == [10, 10]
    assert final.usage is not None and final.usage.total_tokens == 10
    assert final.choices[0].message.content == "Hello"


def test_one_usage_event_when_the_finish_chunk_and_a_trailing_chunk_both_carry_it() -> None:
    with _client(FINISH_THEN_TRAILING).chat.completions.stream(
        model="m", messages=MSG
    ) as s:
        types = [e.type for e in s]
        final = s.get_final_completion()
    assert types == ["content", "content", "usage", "usage", "done"]
    assert final.usage is not None and final.usage.total_tokens == 11


def test_the_event_carries_the_first_usage_and_the_final_completion_the_last() -> None:
    frames = [
        _chunk(
            [{"index": 0, "delta": {"content": "x"}, "finish_reason": "stop"}],
            _usage(12),
        ),
        _chunk([], _usage(14)),
        "[DONE]",
    ]
    with _client(frames).chat.completions.stream(model="m", messages=MSG) as s:
        usage = [e.usage.total_tokens for e in s if e.type == "usage" and e.usage]
        final = s.get_final_completion()
    assert usage == [12, 14]
    assert final.usage is not None and final.usage.total_tokens == 14


def test_the_raw_stream_still_yields_every_chunk() -> None:
    stream = _client(RECORDED).chat.completions.create(
        model="m", messages=MSG, stream=True
    )
    chunks = list(stream)
    assert len(chunks) == 4
    assert [c.usage.total_tokens for c in chunks if c.usage] == [10, 10]


def test_a_late_error_after_the_usage_still_raises_before_done() -> None:
    frames = FINISH_THEN_TRAILING[:-1] + [
        json.dumps(
            {
                "error": {
                    "message": "late",
                    "type": "guardrail_error",
                    "param": None,
                    "code": "stream_blocked",
                }
            }
        ),
        "[DONE]",
    ]
    seen: list[str] = []
    with _client(frames).chat.completions.stream(model="m", messages=MSG) as s:
        with pytest.raises(StreamError) as info:
            for event in s:
                seen.append(event.type)
    assert seen == ["content", "content", "usage", "usage"]
    assert info.value.code == "stream_blocked"


@pytest.mark.anyio
@pytest.mark.parametrize("frames, expected", [
    (RECORDED, ["content", "usage", "usage", "done"]),
    (FINISH_THEN_TRAILING, ["content", "content", "usage", "usage", "done"]),
])
async def test_the_async_stream_manager_too(frames, expected) -> None:
    client = _async_client(frames)
    async with await client.chat.completions.stream(model="m", messages=MSG) as s:
        events = [e async for e in s]
        final = await s.get_final_completion()
    assert [e.type for e in events] == expected
    totals = [json.loads(frame)["usage"]["total_tokens"]
              for frame in frames[:-1] if json.loads(frame).get("usage")]
    assert [e.usage.total_tokens for e in events if e.type == "usage"] == totals
    assert final.usage is not None and final.usage.total_tokens == totals[-1]


@pytest.mark.anyio
async def test_the_async_event_carries_the_first_usage() -> None:
    frames = [
        _chunk([{"index": 0, "delta": {}, "finish_reason": "stop"}], _usage(12)),
        _chunk([], _usage(14)),
        "[DONE]",
    ]
    client = _async_client(frames)
    async with await client.chat.completions.stream(model="m", messages=MSG) as s:
        usage = [e.usage.total_tokens async for e in s if e.type == "usage" and e.usage]
        final = await s.get_final_completion()
    assert usage == [12, 14]
    assert final.usage is not None and final.usage.total_tokens == 14
