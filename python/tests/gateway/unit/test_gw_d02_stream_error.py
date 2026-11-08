"""D-02: a gateway error frame raises a typed StreamError and the response is closed.

agentcc 1.0 Python raised ``StreamError("Stream error: {'message': ..., 'type': ...}")``
(the dict's repr) and left the connection open. Now the message is ``error.message`` and
``type``, ``code``, ``param``, ``body`` and ``request_id`` are fields, with the same rules
as the TypeScript client (the recorded source streaming.ts streamErrorFromEvent). The frames are the
gateway's (tests/fixtures/gateway/stream-error-frames.json, gateway the recorded source) and the
malformed ones the parity catalog's (sse-malformed.json).
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "gateway"
FRAMES = json.loads((FIXTURES / "stream-error-frames.json").read_text())["cases"]
MALFORMED = json.loads((FIXTURES / "sse-malformed.json").read_text())["cases"]
ERROR_CASES = [c for c in FRAMES if c["expect"]["raises"]]
GW = "http://127.0.0.1:8090"


class _Body(httpx.SyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.closed = False

    def __iter__(self):
        yield from self.chunks

    def close(self) -> None:
        self.closed = True


def _client(chunks: list[bytes], bodies: list[_Body]) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        body = _Body(chunks)
        bodies.append(body)
        return httpx.Response(
            200,
            headers={
                "content-type": "text/event-stream",
                "x-agentcc-request-id": "gw-req-9",
            },
            stream=body,
        )

    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _frames(case: dict[str, Any]) -> list[bytes]:
    return [f"data: {frame}\n\n".encode() for frame in case["frames"]]


@pytest.mark.parametrize("case", ERROR_CASES, ids=[c["name"] for c in ERROR_CASES])
def test_gateway_frames_raise_typed_stream_errors(case: dict[str, Any]) -> None:
    expect = case["expect"]
    bodies: list[_Body] = []
    client = _client(_frames(case), bodies)
    stream = client.chat.completions.create(model="m", messages=[], stream=True)
    texts = []
    with pytest.raises(StreamError) as info:
        for chunk in stream:
            texts.extend(c.delta.content or "" for c in chunk.choices)
    err = info.value
    assert str(err) == err.message == f"Stream error: {err.body}"
    assert err.body["message"] == expect["message"]
    assert (err.type, err.code, err.param) == (expect["type"], expect["code"], None)
    assert err.body == {
        "message": expect["message"],
        "type": expect["type"],
        "param": None,
        "code": expect["code"],
    }
    assert err.request_id is None  # Non-ULID wire IDs are not gateway identity.
    assert "".join(texts) == expect["text_before_error"]
    assert bodies[0].closed, "the connection is released at the error frame"
    assert repr(err) == f"StreamError({str(err)!r})"


@pytest.mark.parametrize(
    "name, message, fields",
    [
        (
            "error_is_string",
            "plain string error",
            {"type": None, "code": None, "body": "plain string error"},
        ),
        (
            "error_without_message",
            'Stream error: {"type":"x","code":"y"}',
            {"type": "x", "code": "y", "body": {"type": "x", "code": "y"}},
        ),
    ],
)
def test_odd_error_frames(name: str, message: str, fields: dict[str, Any]) -> None:
    bodies: list[_Body] = []
    client = _client([chunk.encode() for chunk in MALFORMED[name]], bodies)
    with pytest.raises(StreamError) as info:
        list(client.chat.completions.create(model="m", messages=[], stream=True))
    assert str(info.value) == f"Stream error: {fields['body']}"
    if isinstance(fields["body"], str):
        assert fields["body"] == message
    else:
        assert message == "Stream error: " + json.dumps(fields["body"], separators=(",", ":"))
    for key, value in fields.items():
        assert getattr(info.value, key) == value, key
    assert bodies[0].closed


def test_other_stream_failures_carry_no_fields() -> None:
    bodies: list[_Body] = []
    client = _client(
        [chunk.encode() for chunk in MALFORMED["invalid_json_frame"]], bodies
    )
    with pytest.raises(StreamError) as info:
        list(client.chat.completions.create(model="m", messages=[], stream=True))
    assert str(info.value).startswith("Invalid JSON in SSE event:")
    assert (
        info.value.type,
        info.value.code,
        info.value.body,
        info.value.request_id,
    ) == (None, None, None, None)


def test_the_stream_manager_raises_the_same_error() -> None:
    case = ERROR_CASES[0]
    bodies: list[_Body] = []
    client = _client(_frames(case), bodies)
    with client.chat.completions.stream(model="m", messages=[]) as manager:
        with pytest.raises(StreamError) as info:
            manager.get_final_completion()
    assert info.value.code == case["expect"]["code"]


async def test_the_async_stream_closes_and_raises() -> None:
    case = ERROR_CASES[0]
    closed: list[bool] = []

    class _AsyncBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            for frame in _frames(case):
                yield frame

        async def aclose(self) -> None:
            closed.append(True)

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, stream=_AsyncBody()
        )

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    stream = await client.chat.completions.create(model="m", messages=[], stream=True)
    with pytest.raises(StreamError) as info:
        async for _ in stream:
            pass
    assert info.value.code == case["expect"]["code"] and info.value.request_id is None
    assert closed


def test_the_fields_survive_pickling() -> None:
    err = StreamError(
        "blocked",
        type="guardrail_error",
        code="stream_blocked",
        body={"a": 1},
        request_id="r",
    )
    back = pickle.loads(pickle.dumps(err))
    assert (
        type(back) is StreamError
        and str(back) == "blocked"
        and back.args == ("blocked",)
    )
    assert (back.type, back.code, back.param, back.body, back.request_id) == (
        "guardrail_error",
        "stream_blocked",
        None,
        {"a": 1},
        "r",
    )


def test_a_bare_stream_error_is_1_0s() -> None:
    err = StreamError("stream broke")
    assert (str(err), repr(err), err.args) == (
        "stream broke",
        "StreamError('stream broke')",
        ("stream broke",),
    )
