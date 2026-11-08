"""The SDK-only behaviour fi.gateway must keep from agentcc 1.x, one test each.

What only the SDK does, the gateway not: (a) gateway stream error frames
raise a typed StreamError with type, code and param; (b) the request header helpers;
(c) the response metadata readers; (d) usage from the finish chunk when the request
has no ``stream_options``; (e) the gateway reads neither ``x-agentcc-sdk-version`` nor
the User-Agent (test_gw_d03_version.py). ``timeout-ms`` is a response header only, and
no SDK reads a guardrail ``-policy`` response header. Each behaviour is driven through
a real ``AgentCC`` / ``AsyncAgentCC`` on an ``httpx.MockTransport``; the gateway's own
frames come from
tests/fixtures/gateway (stream-error-frames.json, gateway source the recorded source;
stream-cases-extra.json, written as the gateway's responsesStreamErrorEvent).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from ._published_helpers import wire_snapshot
from fi.gateway import (
    AgentCC,
    AsyncAgentCC,
    CacheConfig,
    GatewayConfig,
    GuardrailBlockedError,
    StreamError,
    TimeoutConfig,
    create_headers,
)

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "gateway"
FRAMES = {
    c["name"]: c
    for c in json.loads((FIXTURES / "stream-error-frames.json").read_text())["cases"]
}
EXTRA = {
    c["name"]: c
    for c in json.loads((FIXTURES / "stream-cases-extra.json").read_text())["cases"]
}
GW = "http://127.0.0.1:8090"
MSG = [{"role": "user", "content": "x"}]
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": "hi"},
        }
    ],
}
SSE = {"content-type": "text/event-stream"}


def _sse(frames: list[str]) -> bytes:
    return "".join(f"data: {f}\n\n" for f in frames).encode()


def _client(
    reply: httpx.Response | Any, seen: list[httpx.Request] | None = None, **kwargs: Any
) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(wire_snapshot(request))
        return reply(request) if callable(reply) else reply

    return AgentCC(
        api_key="gw-key",
        base_url=GW,
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        **kwargs,
    )


# (a) stream error frames raise a typed StreamError --------------------------------


def test_a_data_error_frame_on_a_200_stream_raises_a_typed_stream_error() -> None:
    case = FRAMES["guardrail_block_after_content_then_done"]
    stream = _client(httpx.Response(200, headers=SSE, content=_sse(case["frames"])))
    texts = []
    with pytest.raises(StreamError) as info:
        for chunk in stream.chat.completions.create(
            model="m", messages=MSG, stream=True
        ):
            texts.append(chunk.choices[0].delta.content)
    err = info.value
    assert (err.type, err.code, err.param) == (
        "guardrail_error",
        "stream_blocked",
        None,
    )
    assert str(err) == f"Stream error: {err.body}"
    assert err.body["message"] == "Content blocked by streaming guardrail"
    assert texts == ["Hello", " world"]


async def test_a_data_error_frame_raises_on_the_async_client_too() -> None:
    case = FRAMES["guardrail_block_first_frame"]
    client = AsyncAgentCC(
        api_key="gw-key",
        base_url=GW,
        http_client=httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, headers=SSE, content=_sse(case["frames"]))
            )
        ),
    )
    stream = await client.chat.completions.create(model="m", messages=MSG, stream=True)
    with pytest.raises(StreamError) as info:
        async for _ in stream:
            pass
    assert info.value.code == case["expect"]["code"]


def test_a_responses_event_error_raises_a_typed_stream_error() -> None:
    reply = EXTRA["responses_event_error"]["reply"]
    body = "".join(reply["raw"]).encode()
    client = _client(httpx.Response(200, headers=reply["headers"], content=body))
    events = []
    with pytest.raises(StreamError) as info:
        for event in client.responses.create(model="m", input="x", stream=True):
            events.append(event.type)
    assert events == ["response.created", "response.output_text.delta"]
    assert info.value.code == "stream_blocked"
    assert info.value.request_id is None  # Non-ULID wire IDs are not gateway identity.
    assert str(info.value) == "Content blocked by streaming guardrail"
    # type, code and param all come from the frame; the gateway's frame is flat and
    # its "type" is "error".
    assert (info.value.type, info.value.code, info.value.param) == (
        "error",
        "stream_blocked",
        None,
    )
    frame = json.loads(reply["raw"][-1].split("data: ", 1)[1])
    assert frame["type"] == "error"
    assert info.value.body == frame


# (b) request header helpers ------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs, header, value",
    [
        pytest.param(
            {"config": GatewayConfig(cache=CacheConfig(ttl=60))},
            "x-agentcc-config",
            '{"cache":{"enabled":true,"strategy":"exact","ttl":60,"force_refresh":false,"cache_by_model":true}}',
            id='kwargs0-x-agentcc-config-{"cache":{"ttl":60,"force_refresh":false}}',
        ),
        ({"cache_ttl": 60}, "x-agentcc-cache-ttl", "60"),
        ({"cache_namespace": "ns"}, "x-agentcc-cache-namespace", "ns"),
        ({"cache_force_refresh": True}, "x-agentcc-cache-force-refresh", "true"),
        ({"session_id": "s1"}, "x-agentcc-session-id", "s1"),
        ({"session_name": "flow"}, "x-agentcc-session-name", "flow"),
        ({"session_path": "/a/b"}, "x-agentcc-session-path", "/a/b"),
        ({"trace_id": "t1"}, "x-agentcc-trace-id", "t1"),
        ({"user_id": "u1"}, "x-agentcc-user-id", "u1"),
        ({"metadata": {"team": "a"}}, "x-agentcc-metadata", '{"team":"a"}'),
        ({"properties": {"env": "prod"}}, "x-agentcc-property-env", "prod"),
        (
            {"config": GatewayConfig(timeout=TimeoutConfig(total=1.5))},
            "x-agentcc-request-timeout",
            "1500",
        ),
    ],
)
def test_b_create_headers_builds_each_gateway_header(
    kwargs: dict, header: str, value: str
) -> None:
    built = {k.lower(): v for k, v in create_headers(**kwargs).items()}
    assert built[header] == value


@pytest.mark.parametrize(
    "kwargs, header, value",
    [
        ({"cache_ttl": 60}, "x-agentcc-cache-ttl", "60"),
        ({"cache_namespace": "ns"}, "x-agentcc-cache-namespace", "ns"),
        ({"cache_force_refresh": True}, "x-agentcc-cache-force-refresh", "true"),
        ({"session_id": "s1"}, "x-agentcc-session-id", "s1"),
        ({"trace_id": "t1"}, "x-agentcc-trace-id", "t1"),
        ({"user_id": "u1"}, "x-agentcc-user-id", "u1"),
        ({"request_metadata": {"team": "a"}}, "x-agentcc-metadata", '{"team":"a"}'),
        ({"properties": {"env": "prod"}}, "x-agentcc-property-env", "prod"),
        # Integer milliseconds, as the gateway reads it.
        ({"request_timeout": 1500}, "x-agentcc-request-timeout", "1500"),
    ],
)
def test_b_per_request_parameters_reach_the_wire(
    kwargs: dict, header: str, value: str
) -> None:
    seen: list[httpx.Request] = []
    _client(httpx.Response(200, json=COMPLETION), seen).chat.completions.create(
        model="m", messages=MSG, **kwargs
    )
    assert seen[0].headers[header] == value


@pytest.mark.parametrize("mode", ["replace", "merge"])
def test_b_a_session_sends_id_name_path_and_metadata(mode: str) -> None:
    seen: list[httpx.Request] = []
    client = _client(httpx.Response(200, json=COMPLETION), seen, metadata_mode=mode)
    with client.session(
        session_id="s1", name="checkout", metadata={"cart": "c1"}, path="/pay"
    ) as sess:
        sess.step("confirm")
        client.chat.completions.create(model="m", messages=MSG)
    headers = seen[0].headers
    assert headers["x-agentcc-session-id"] == "s1"
    assert headers["x-agentcc-session-name"] == "checkout"
    assert headers["x-agentcc-session-path"] == "/pay/confirm"
    if mode == "merge":
        assert json.loads(headers["x-agentcc-metadata"]) == {"cart": "c1"}
    else:
        # Published default: per-key session metadata headers.
        assert headers["x-agentcc-metadata-cart"] == "c1"
        assert "x-agentcc-metadata" not in headers


def test_b_timeout_ms_is_a_response_header_only() -> None:
    """Inventory section 10 (b): no SDK sends x-agentcc-timeout-ms; it is read back."""
    seen: list[httpx.Request] = []
    reply = httpx.Response(
        200, json=COMPLETION, headers={"x-agentcc-timeout-ms": "30000"}
    )
    result = _client(reply, seen).chat.completions.create(
        model="m", messages=MSG, request_timeout=30000
    )
    assert "x-agentcc-timeout-ms" not in seen[0].headers
    assert result.agentcc.timeout_ms == 30000


# (c) response metadata readers -------------------------------------------------


@pytest.mark.parametrize(
    "header, value, field, expected",
    [
        pytest.param("x-agentcc-request-id", "req-9", "request_id", None,
                     id="x-agentcc-request-id-req-9-request_id-req-9"),
        ("x-agentcc-request-id", "01ARZ3NDEKTSV4RRFFQ69G5FAV", "request_id", "01ARZ3NDEKTSV4RRFFQ69G5FAV"),
        ("x-agentcc-provider", "openai", "provider", "openai"),
        ("x-agentcc-model-used", "gpt-4o-mini", "model_used", "gpt-4o-mini"),
        ("x-agentcc-latency-ms", "42", "latency_ms", 42),
        ("x-agentcc-cost", "0.25", "cost", 0.25),
        ("x-agentcc-cache", "hit_exact", "cache_status", "hit_exact"),
        ("x-agentcc-fallback-used", "true", "fallback_used", True),
        (
            "x-agentcc-routing-strategy",
            "least_latency",
            "routing_strategy",
            "least_latency",
        ),
        ("x-agentcc-guardrail-triggered", "true", "guardrail_triggered", True),
    ],
)
def test_c_each_response_header_is_read_into_agentcc_metadata(
    header: str, value: str, field: str, expected: Any
) -> None:
    reply = httpx.Response(200, json=COMPLETION, headers={header: value})
    result = _client(reply).chat.completions.create(model="m", messages=MSG)
    assert getattr(result.agentcc, field) == expected
    if field == "request_id":
        # Wire gateway identity is validated, not substituted from arbitrary text.
        assert result.agentcc.gateway_request_id == expected
        assert result.agentcc.http_response.headers[header] == value


def test_c_a_guardrail_block_carries_the_guardrail_headers() -> None:
    reply = httpx.Response(
        446,
        json={"error": {"message": "blocked: pii", "type": "guardrail_error"}},
        headers={
            "x-agentcc-guardrail-name": "pii",
            "x-agentcc-guardrail-action": "block",
            "x-agentcc-guardrail-confidence": "0.93",
            "x-agentcc-guardrail-message": "PII detected",
            "x-agentcc-request-id": "req-g",
        },
    )
    with pytest.raises(GuardrailBlockedError) as info:
        _client(reply).chat.completions.create(model="m", messages=MSG)
    err = info.value
    assert (err.guardrail_name, err.guardrail_action) == ("pii", "block")
    assert err.guardrail_confidence == 0.93
    assert err.guardrail_message == "PII detected"
    assert err.request_id is None  # Non-ULID wire IDs are not gateway identity.


# (d) usage from the finish chunk, with no stream_options -------------------------


def test_d_usage_comes_from_the_finish_chunk_and_no_stream_options_is_sent() -> None:
    chunk = {
        "id": "c",
        "object": "chat.completion.chunk",
        "created": 1,
        "model": "m",
    }
    frames = [
        json.dumps({**chunk, "choices": [{"index": 0, "delta": {"content": "hi"}}]}),
        json.dumps(
            {
                **chunk,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 1,
                    "total_tokens": 6,
                },
            }
        ),
        "[DONE]",
    ]
    seen: list[httpx.Request] = []
    client = _client(
        lambda r: httpx.Response(200, headers=SSE, content=_sse(frames)), seen
    )
    with client.chat.completions.stream(model="m", messages=MSG) as stream:
        events = list(stream)
        final = stream.get_final_completion()
    usage_events = [e for e in events if e.type == "usage"]
    assert len(usage_events) == 1 and usage_events[0].usage.total_tokens == 6
    assert final.usage is not None and final.usage.total_tokens == 6
    assert final.choices[0].message.content == "hi"
    body = json.loads(seen[0].content)
    assert body["stream"] is True and "stream_options" not in body
