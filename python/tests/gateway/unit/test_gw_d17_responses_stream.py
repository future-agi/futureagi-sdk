"""D-17: ``responses.create(stream=True)`` yields typed ``ResponseStreamEvent`` items and
raises ``StreamError`` on ``event: error``.

agentcc 1.x parsed Responses API frames as chat completion chunks, so every event
failed validation ("Stream interrupted: 5 validation errors for ChatCompletionChunk").
The frames are the parity catalog's (stream.responses.normal and
stream-cases-extra.json responses_event_error, written as the gateway's
responsesStreamErrorEvent).
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError
from fi.gateway.types.responses import ResponseStreamEvent

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "gateway"
EXTRA = {
    c["name"]: c
    for c in json.loads((FIXTURES / "stream-cases-extra.json").read_text())["cases"]
}
ERROR_REPLY = EXTRA["responses_event_error"]["reply"]
NORMAL = [
    'event: response.created\ndata: {"type":"response.created","sequence_number":0,"response":{"id":"resp_1","status":"in_progress"}}\n\n',
    'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":1,"item_id":"msg_1","delta":"Hi"}\n\n',
    'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":2,"item_id":"msg_1","delta":" there"}\n\n',
    'event: response.completed\ndata: {"type":"response.completed","sequence_number":3,"response":{"id":"resp_1","status":"completed","usage":{"input_tokens":3,"output_tokens":2,"total_tokens":5}}}\n\n',
]
GW = "http://127.0.0.1:8090"


class _Body(httpx.SyncByteStream):
    def __init__(self, chunks: list[str]) -> None:
        self.chunks = [c.encode() for c in chunks]
        self.closed = False

    def __iter__(self):
        yield from self.chunks

    def close(self) -> None:
        self.closed = True


def _client(
    chunks: list[str], headers: dict[str, str], seen: list, bodies: list
) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = _Body(chunks)
        bodies.append(body)
        return httpx.Response(200, headers=headers, stream=body)

    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_a_normal_stream_yields_typed_events() -> None:
    seen: list = []
    client = _client(NORMAL, {"content-type": "text/event-stream"}, seen, [])
    with client.responses.create(model="m", input="hi", stream=True) as stream:
        events = list(stream)
    assert json.loads(seen[0].content)["stream"] is True
    assert all(isinstance(e, ResponseStreamEvent) for e in events)
    assert [e.type for e in events] == [
        "response.created",
        "response.output_text.delta",
        "response.output_text.delta",
        "response.completed",
    ]
    assert [e.sequence_number for e in events] == [0, 1, 2, 3]
    assert (
        "".join(e.delta for e in events if e.type == "response.output_text.delta")
        == "Hi there"
    )
    assert events[1].item_id == "msg_1"  # extra fields are kept
    final = events[-1].response
    assert final is not None and final.id == "resp_1" and final.usage.total_tokens == 5


def test_event_error_raises_a_typed_stream_error_and_closes() -> None:
    bodies: list[_Body] = []
    client = _client(ERROR_REPLY["raw"], ERROR_REPLY["headers"], [], bodies)
    stream = client.responses.create(model="m", input="hi", stream=True)
    seen_types = []
    with pytest.raises(StreamError) as info:
        for event in stream:
            seen_types.append(event.type)
    err = info.value
    assert seen_types == ["response.created", "response.output_text.delta"]
    assert str(err) == "Content blocked by streaming guardrail"
    assert (err.type, err.code, err.param) == ("error", "stream_blocked", None)
    assert err.body["type"] == "error" and err.body["sequence_number"] == 2
    assert err.request_id == ERROR_REPLY["headers"]["x-agentcc-request-id"]
    assert bodies[0].closed
    assert stream.agentcc.request_id == "req-resp-1"


def test_a_json_cache_hit_is_one_completed_event() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"id": "resp_c", "object": "response", "status": "completed"}
        )

    client = AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    events = list(client.responses.create(model="m", input="hi", stream=True))
    assert [(e.type, e.response.id) for e in events] == [
        ("response.completed", "resp_c")
    ]


def test_a_malformed_frame_is_a_stream_error() -> None:
    client = _client(
        ["data: {not json}\n\n"], {"content-type": "text/event-stream"}, [], []
    )
    with pytest.raises(StreamError, match="Invalid JSON in SSE event"):
        list(client.responses.create(model="m", input="hi", stream=True))


async def test_the_async_stream_too() -> None:
    chunks = ERROR_REPLY["raw"]

    class _AsyncBody(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self):
            for chunk in chunks:
                yield chunk.encode()

        async def aclose(self) -> None:
            _AsyncBody.closed = True

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, stream=_AsyncBody()
        )

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    stream = await client.responses.create(model="m", input="hi", stream=True)
    types = []
    with pytest.raises(StreamError) as info:
        async for event in stream:
            types.append(event.type)
    assert types == ["response.created", "response.output_text.delta"]
    err = info.value
    assert (err.type, err.code, err.param) == ("error", "stream_blocked", None)
    assert _AsyncBody.closed


def test_a_plain_create_still_returns_the_response_object() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"id": "resp_9", "object": "response", "status": "completed"}
        )

    client = AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    assert client.responses.create(model="m", input="hi").id == "resp_9"
