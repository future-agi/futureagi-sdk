"""D-16: StreamEvent carries only the variants that fire; ``done`` comes after the body.

agentcc 1.x declared ``guardrail_warning``, ``guardrail_block``, ``guardrail_disclaimer``
and ``error`` events (and their fields) that nothing emitted. The late-error fixture
(stream-cases-extra.json ``late_error_after_finish_reason``) sends content, the finish
chunk and the usage chunk, then an error frame and ``[DONE]``: a consumer that stops at
``done`` must still see the error, which TypeScript 1.0.1 got wrong.
"""

from __future__ import annotations

import dataclasses
import json
import typing
from pathlib import Path

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError
from fi.gateway._streaming import StreamEvent

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "gateway"
EXTRA = {
    c["name"]: c
    for c in json.loads((FIXTURES / "stream-cases-extra.json").read_text())["cases"]
}
LATE = EXTRA["late_error_after_finish_reason"]["reply"]
GW = "http://127.0.0.1:8090"


def _body() -> bytes:
    return "".join(f"data: {frame}\n\n" for frame in LATE["sse"]).encode()


def _client() -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers=LATE["headers"], content=_body())

    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_only_the_emitted_variants_and_fields_remain() -> None:
    assert [f.name for f in dataclasses.fields(StreamEvent)] == [
        "type",
        "text",
        "index",
        "tool_call",
        "guardrail_name",
        "message",
        "confidence",
        "disclaimer_text",
        "usage",
        "error",
    ]
    hints = typing.get_type_hints(StreamEvent)
    assert hints["type"] is str
    for kind in ("content", "tool_call", "usage", "done", "guardrail_warning", "guardrail_block", "guardrail_disclaimer", "error"):
        assert StreamEvent(type=kind).type == kind


def test_the_fixture_ends_with_an_error_after_finish_and_usage() -> None:
    frames = [json.loads(f) for f in LATE["sse"] if f != "[DONE]"]
    assert frames[-1].get("error") and any(f.get("usage") for f in frames[:-1])
    assert any(
        c.get("finish_reason") for f in frames[:-1] for c in f.get("choices", [])
    )


def test_a_consumer_that_breaks_on_done_sees_the_late_error() -> None:
    seen: list[str] = []
    with _client().chat.completions.stream(model="m", messages=[]) as manager:
        with pytest.raises(StreamError) as info:
            for event in manager:
                seen.append(event.type)
                if event.type == "done":
                    break
    assert "done" not in seen
    assert seen[0] == "content" and "usage" in seen
    assert info.value.code is not None


def test_every_event_type_seen_on_a_full_stream_is_declared() -> None:
    sse = (
        "".join(
            f"data: {json.dumps(frame)}\n\n"
            for frame in [
                {
                    "id": "c",
                    "object": "chat.completion.chunk",
                    "created": 1,
                    "model": "m",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "content": "a",
                                "tool_calls": [
                                    {
                                        "index": 0,
                                        "id": "t",
                                        "type": "function",
                                        "function": {"name": "f", "arguments": "{}"},
                                    }
                                ],
                            },
                        }
                    ],
                },
                {
                    "id": "c",
                    "object": "chat.completion.chunk",
                    "created": 1,
                    "model": "m",
                    "choices": [],
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                    },
                },
            ]
        )
        + "data: [DONE]\n\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=sse.encode()
        )

    client = AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with client.chat.completions.stream(model="m", messages=[]) as manager:
        types = [event.type for event in manager]
    assert types == ["content", "tool_call", "usage", "done"]


async def test_the_async_manager_too() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers=LATE["headers"], content=_body())

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    seen: list[str] = []
    async with await client.chat.completions.stream(model="m", messages=[]) as manager:
        with pytest.raises(StreamError):
            async for event in manager:
                seen.append(event.type)
                if event.type == "done":
                    break
    assert "done" not in seen
