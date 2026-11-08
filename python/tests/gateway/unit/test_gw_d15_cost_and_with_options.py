"""D-15: ``current_cost`` sums ``x-agentcc-cost``; ``with_options`` applies ``trace_id`` and
carries ``retry_policy``.

agentcc 1.x never called ``_track_cost``, so ``current_cost`` stayed 0.0; its
``with_options(trace_id=)`` accepted the value and dropped it, and the copy lost the
client's ``retry_policy``.
"""

from __future__ import annotations

import httpx
import pytest

from fi.gateway import (
    AgentCC,
    AsyncAgentCC,
    BadRequestError,
    InternalServerError,
    RetryPolicy,
)

GW = "http://127.0.0.1:8090"
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}
SSE = (
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
    '"choices":[{"index":0,"delta":{"content":"a"},"finish_reason":null}]}\n\n'
    "data: [DONE]\n\n"
)


def _handler(seen: list[httpx.Request], costs: list[str | None]):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        cost = costs.pop(0) if costs else None
        headers = {"x-agentcc-cost": cost} if cost is not None else {}
        if request.url.path == "/v1/audio/speech":
            return httpx.Response(200, headers=headers, content=b"mp3")
        if b'"stream":true' in request.content:
            return httpx.Response(
                200,
                headers={**headers, "content-type": "text/event-stream"},
                content=SSE,
            )
        return httpx.Response(200, headers=headers, json=COMPLETION)

    return handler


def _client(
    costs: list[str | None], seen: list[httpx.Request] | None = None, **kwargs
) -> AgentCC:
    transport = httpx.MockTransport(_handler(seen if seen is not None else [], costs))
    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=transport),
        **kwargs,
    )


def test_current_cost_sums_the_cost_header() -> None:
    client = _client(["0.001", "0.002", None, "not-a-number"])
    for _ in range(4):
        client.chat.completions.create(model="m", messages=[])
    assert client.current_cost == pytest.approx(0.003)
    client.reset_cost()
    assert client.current_cost == 0.0


def test_streams_and_raw_responses_count_their_header_cost() -> None:
    client = _client(["0.01", "0.02", "0.04"])
    for _ in client.chat.completions.create(model="m", messages=[], stream=True):
        pass
    with client.chat.completions.stream(model="m", messages=[]) as stream:
        stream.get_final_text()
    client.audio.speech.create(model="tts", input="hi", voice="v")
    assert client.current_cost == pytest.approx(0.07)


def test_an_error_response_adds_nothing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400, headers={"x-agentcc-cost": "9"}, json={"error": {"message": "bad"}}
        )

    client = AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(BadRequestError):
        client.chat.completions.create(model="m", messages=[])
    assert client.current_cost == 0.0


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_with_options_copies_share_the_ledger() -> None:
    client = _client(["0.5", "0.25"])
    copy = client.with_options(timeout=5)
    client.chat.completions.create(model="m", messages=[])
    copy.chat.completions.create(model="m", messages=[])
    assert client.current_cost == copy.current_cost == pytest.approx(0.75)
    copy.reset_cost()
    assert client.current_cost == 0.0


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
async def test_the_async_client_counts_too() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"x-agentcc-cost": "0.125"}, json=COMPLETION)

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    await client.chat.completions.create(model="m", messages=[])
    await client.with_options(max_retries=0).chat.completions.create(
        model="m", messages=[]
    )
    assert client.current_cost == pytest.approx(0.25)


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_with_options_trace_id_is_sent_and_a_request_trace_id_wins() -> None:
    seen: list[httpx.Request] = []
    client = _client([], seen)
    traced = client.with_options(trace_id="trace-from-options")
    traced.chat.completions.create(model="m", messages=[])
    traced.chat.completions.create(model="m", messages=[], trace_id="per-request")
    client.chat.completions.create(model="m", messages=[])
    assert [r.headers.get("x-agentcc-trace-id") for r in seen] == [
        "trace-from-options",
        "per-request",
        None,
    ]


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_with_options_trace_id_beats_an_extra_header_of_the_same_name() -> None:
    seen: list[httpx.Request] = []
    client = _client([], seen)
    client.with_options(
        extra_headers={"x-agentcc-trace-id": "from-headers"}, trace_id="from-trace-id"
    ).chat.completions.create(model="m", messages=[])
    assert seen[0].headers["x-agentcc-trace-id"] == "from-trace-id"


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_with_options_keeps_the_retry_policy() -> None:
    policy = RetryPolicy(InternalServerErrorRetries=2)
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        return httpx.Response(500, json={"error": {"message": "boom"}})

    client = AgentCC(
        api_key="k",
        base_url=GW,
        retry_policy=policy,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    copy = client.with_options(timeout=5)
    assert copy._retry_policy is policy
    copy._get_base_client()._calculate_delay = lambda attempt, headers=None: 0.0
    with pytest.raises(InternalServerError):
        copy.chat.completions.create(model="m", messages=[])
    assert len(attempts) == 3  # one try and the policy's two retries for a 500
