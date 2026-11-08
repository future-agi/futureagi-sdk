"""A Responses ``event: error`` frame raises a StreamError carrying type, code and param.

The SDK-only behaviour list for the gateway (section 3 (a)) asks for a typed StreamError
with ``type``, ``code`` and ``param`` on both kinds of gateway stream error: a
``data: {"error": {...}}`` frame on chat completions and ``event: error`` on
``/v1/responses``. The gateway writes the second one flat
(``{"code", "message", "param", "type": "error"}``, handlers_responses.go
responsesStreamErrorEvent), so its ``type`` is ``"error"``.

``RECORDED`` is the frame sequence the gateway sent on a live stack for a
keyword-guardrail block of a streamed Responses answer (the mock upstream's
``block-mid`` scenario), byte for byte, with the SSE ``event:`` lines it carried.
"""

from __future__ import annotations

import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError

GW = "http://127.0.0.1:8090"
BLOCK = (
    "Request blocked by guardrail: keyword-blocklist — Blocked keywords found: "
    "kumquatforbidden"
)
RECORDED = [
    (
        "response.created",
        '{"type": "response.created", "sequence_number": 0, "response": {"id": '
        '"resp_mock", "object": "response", "created_at": 1761177600, "model": '
        '"gpt-4o-mini", "status": "in_progress", "output": []}}',
    ),
    (
        "response.output_text.delta",
        '{"type": "response.output_text.delta", "sequence_number": 1, "item_id": '
        '"msg_1", "output_index": 0, "content_index": 0, "delta": "Hi "}',
    ),
    (
        "error",
        json.dumps(
            {
                "code": "content_blocked",
                "message": BLOCK,
                "param": None,
                "type": "error",
            },
            separators=(",", ":"),
        ),
    ),
]


def _sse(frames: list[tuple[str, str]]) -> bytes:
    return "".join(f"event: {e}\ndata: {d}\n\n" for e, d in frames).encode()


def _client(body: bytes) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream", "x-agentcc-request-id": "r1"},
            content=body,
        )

    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _raise(body: bytes) -> tuple[list[str], StreamError]:
    seen: list[str] = []
    with pytest.raises(StreamError) as info:
        for event in _client(body).responses.create(model="m", input="x", stream=True):
            seen.append(event.type)
    return seen, info.value


def test_the_recorded_gateway_frame_gives_type_code_and_param() -> None:
    seen, err = _raise(_sse(RECORDED))
    assert seen == ["response.created", "response.output_text.delta"]
    assert (err.type, err.code, err.param) == ("error", "content_blocked", None)
    assert str(err) == BLOCK
    assert err.request_id == "r1"
    assert err.body == json.loads(RECORDED[-1][1])


def test_a_param_in_the_frame_is_carried() -> None:
    frame = {
        "type": "error",
        "code": "invalid_value",
        "message": "bad",
        "param": "input",
    }
    _, err = _raise(_sse([("error", json.dumps(frame))]))
    assert (err.type, err.code, err.param) == ("error", "invalid_value", "input")


def test_a_nested_error_object_gives_its_own_fields() -> None:
    frame = {
        "type": "error",
        "sequence_number": 4,
        "error": {
            "type": "guardrail_error",
            "code": "content_blocked",
            "message": "blocked",
            "param": "input",
        },
    }
    _, err = _raise(_sse([("error", json.dumps(frame))]))
    assert (err.type, err.code, err.param) == (
        "guardrail_error",
        "content_blocked",
        "input",
    )
    assert str(err) == "blocked"
    assert err.body == frame


def test_nested_fields_fall_back_to_the_frame_s_own() -> None:
    frame = {"type": "error", "code": "top", "message": "m", "error": {"param": "p"}}
    _, err = _raise(_sse([("error", json.dumps(frame))]))
    assert (err.type, err.code, err.param) == ("error", "top", "p")
    assert str(err) == "m"


def test_a_frame_that_is_not_an_object_still_has_a_type() -> None:
    _, err = _raise(_sse([("error", '"upstream went away"')]))
    assert (err.type, err.code, err.param) == ("error", None, None)
    assert err.body == "upstream went away"
    assert str(err) == 'Stream error: "upstream went away"'


def test_a_data_only_frame_with_type_error_is_the_same_error() -> None:
    frame = json.dumps({"type": "error", "code": "c", "message": "m", "param": None})
    _, err = _raise(f"data: {frame}\n\n".encode())
    assert (err.type, err.code, err.param) == ("error", "c", None)


async def test_the_async_client_gives_the_same_fields() -> None:
    body = _sse(RECORDED)

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=body
        )

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    seen: list[str] = []
    with pytest.raises(StreamError) as info:
        async for event in await client.responses.create(
            model="m", input="x", stream=True
        ):
            seen.append(event.type)
    assert seen == ["response.created", "response.output_text.delta"]
    err = info.value
    assert (err.type, err.code, err.param) == ("error", "content_blocked", None)
