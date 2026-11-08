"""Streams release their connection on every error, and a Responses ``event: error``
frame whose data is not JSON still raises the gateway's typed refusal.

Every way a ``responses.create(stream=True)`` stream can fail closes the HTTP response
before the ``StreamError`` reaches the caller: an ``event: error`` frame (flat, nested,
not an object, or not JSON), a frame that is not JSON, a frame that is not an object,
and an event that fails validation. An ``event: error`` frame with invalid JSON raises
with ``type="error"``, the frame's text as ``body`` and the response's request id.
Chat streams (``chat.completions.create(stream=True)``) close on the same failures;
before, only a gateway error frame closed either stream.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError

GW = "http://127.0.0.1:8090"
HEADERS = {"content-type": "text/event-stream", "x-agentcc-request-id": "req-r"}
CREATED = (
    'event: response.created\ndata: {"type":"response.created","sequence_number":0,'
    '"response":{"id":"r","status":"in_progress"}}\n\n'
)
FAILURES = {
    "error frame, invalid JSON": "event: error\ndata: {not json\n\n",
    "error frame, flat": (
        'event: error\ndata: {"type":"error","code":"content_blocked",'
        '"message":"blocked","param":"input"}\n\n'
    ),
    "error frame, not an object": 'event: error\ndata: "refused"\n\n',
    "data frame, invalid JSON": "event: response.output_text.delta\ndata: {nope\n\n",
    "data frame, not an object": "event: response.output_text.delta\ndata: [1]\n\n",
    "data frame, fails validation": (
        'event: response.created\ndata: {"type":"response.created",'
        '"sequence_number":"not a number"}\n\n'
    ),
}


class _Body(httpx.SyncByteStream, httpx.AsyncByteStream):
    def __init__(self, frames: list[str]) -> None:
        self.frames = [f.encode() for f in frames]
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        yield from self.frames

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for frame in self.frames:
            yield frame

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.closed = True


def _sync(body: _Body) -> AgentCC:
    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, headers=HEADERS, stream=body)
            )
        ),
    )


def _async(body: _Body) -> AsyncAgentCC:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers=HEADERS, stream=body)

    return AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


@pytest.mark.parametrize("frame", list(FAILURES.values()), ids=list(FAILURES))
def test_every_failure_closes_the_response(frame: str) -> None:
    body = _Body([CREATED, frame])
    stream = _sync(body).responses.create(model="m", input="x", stream=True)
    seen = []
    with pytest.raises(StreamError):
        for event in stream:
            seen.append(event.type)
    assert seen == ["response.created"]
    assert body.closed
    assert stream.response.is_closed


def test_an_error_frame_with_invalid_json_is_the_typed_refusal() -> None:
    body = _Body([CREATED, FAILURES["error frame, invalid JSON"]])
    stream = _sync(body).responses.create(model="m", input="x", stream=True)
    with pytest.raises(StreamError) as raised:
        list(stream)
    error = raised.value
    assert (error.type, error.code, error.param) == ("error", None, None)
    assert error.body == "{not json"
    assert error.request_id is None  # Non-ULID wire IDs are not gateway identity.
    assert str(error) == "Stream error: {not json"


@pytest.mark.parametrize("frame", list(FAILURES.values()), ids=list(FAILURES))
async def test_every_async_failure_closes_the_response(frame: str) -> None:
    body = _Body([CREATED, frame])
    stream = await _async(body).responses.create(model="m", input="x", stream=True)
    seen = []
    with pytest.raises(StreamError) as raised:
        async for event in stream:
            seen.append(event.type)
    assert seen == ["response.created"]
    assert body.closed
    assert stream.response.is_closed
    if frame is FAILURES["error frame, invalid JSON"]:
        assert (raised.value.type, raised.value.request_id) == ("error", None)
        assert raised.value.gateway_request_id is None
        assert raised.value.body == "{not json"
        assert stream.response.headers["x-agentcc-request-id"] == "req-r"


CHAT_OK = (
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
    '"choices":[{"index":0,"delta":{"content":"Hel"},"finish_reason":null}]}\n\n'
)
CHAT_FAILURES = {
    "error frame": (
        'data: {"error":{"type":"guardrail_error","code":"stream_blocked",'
        '"message":"blocked","param":null}}\n\n'
    ),
    "invalid JSON": "data: {nope\n\n",
    "fails validation": 'data: {"id":"c","choices":[{"index":0}]}\n\n',
}


@pytest.mark.parametrize("frame", list(CHAT_FAILURES.values()), ids=list(CHAT_FAILURES))
def test_every_chat_stream_failure_closes_the_response(frame: str) -> None:
    body = _Body([CHAT_OK, frame])
    stream = _sync(body).chat.completions.create(model="m", messages=[], stream=True)
    seen = []
    with pytest.raises(StreamError):
        for chunk in stream:
            seen.append(chunk.choices[0].delta.content)
    assert seen == ["Hel"]
    assert body.closed and stream.response.is_closed


@pytest.mark.parametrize("frame", list(CHAT_FAILURES.values()), ids=list(CHAT_FAILURES))
async def test_every_async_chat_stream_failure_closes_the_response(frame: str) -> None:
    body = _Body([CHAT_OK, frame])
    stream = await _async(body).chat.completions.create(
        model="m", messages=[], stream=True
    )
    with pytest.raises(StreamError):
        async for _ in stream:
            pass
    assert body.closed and stream.response.is_closed
