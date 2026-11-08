"""Explicit merge mode layers client, session and request metadata.

Replacement, including an empty dictionary, remains the published default.
"""

from __future__ import annotations

import itertools
import json
from typing import Any

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

GW = "http://127.0.0.1:8090"
MSG = [{"role": "user", "content": "hi"}]
CHAT = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}
SSE = (
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
    '"choices":[{"index":0,"delta":{"content":"hi"},"finish_reason":"stop"}]}\n\n'
    "data: [DONE]\n\n"
)
LAYERS = {
    "client": {"tenant": "A", "tier": "gold", "who": "client"},
    "session": {"cart": "c1", "tier": "silver", "who": "session"},
    "request": {"step": "pay", "who": "request"},
}


def _reply(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/v1/files":
        return httpx.Response(
            200,
            json={
                "id": "f",
                "object": "file",
                "bytes": 1,
                "created_at": 1,
                "filename": "a",
                "purpose": "batch",
            },
        )
    if request.url.path == "/v1/completions":
        return httpx.Response(
            200,
            json={
                "id": "t",
                "object": "text_completion",
                "created": 1,
                "model": "m",
                "choices": [{"index": 0, "text": "hi", "finish_reason": "stop"}],
            },
        )
    if request.url.path == "/v1/responses":
        return httpx.Response(
            200, json={"id": "r", "object": "response", "status": "completed"}
        )
    if b'"stream":true' in request.content:
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=SSE.encode()
        )
    return httpx.Response(200, json=CHAT)


def _client(seen: list[httpx.Request], **kwargs: Any) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _reply(request)

    return AgentCC(
        api_key="k",
        base_url=GW,
        metadata_mode="merge",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        **kwargs,
    )


def _metadata(request: httpx.Request) -> Any:
    assert not [
        k for k in request.headers if k.lower().startswith("x-agentcc-metadata-")
    ]
    raw = request.headers.get("x-agentcc-metadata")
    return None if raw is None else json.loads(raw)


def _expected(names: tuple[str, ...]) -> dict[str, Any] | None:
    if not names:
        return None
    out: dict[str, Any] = {}
    for name in names:
        out.update(LAYERS[name])
    return out


COMBINATIONS = [
    combo
    for n in range(4)
    for combo in itertools.combinations(("client", "session", "request"), n)
]


@pytest.mark.parametrize("names", COMBINATIONS, ids=lambda c: "+".join(c) or "none")
def test_every_combination_of_the_three_layers(names: tuple[str, ...]) -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, metadata=LAYERS["client"] if "client" in names else None)
    kwargs = {"request_metadata": LAYERS["request"]} if "request" in names else {}
    if "session" in names:
        with client.session(metadata=LAYERS["session"]):
            client.chat.completions.create(model="m", messages=MSG, **kwargs)
    else:
        client.chat.completions.create(model="m", messages=MSG, **kwargs)
    assert _metadata(seen[0]) == _expected(names)


def test_the_later_layer_wins_on_a_shared_key_and_keeps_key_order() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, metadata=LAYERS["client"])
    with client.session(metadata=LAYERS["session"]):
        client.chat.completions.create(
            model="m", messages=MSG, request_metadata=LAYERS["request"]
        )
    assert seen[0].headers["x-agentcc-metadata"] == (
        '{"tenant":"A","tier":"silver","who":"request","cart":"c1","step":"pay"}'
    )


def test_the_same_rule_with_and_without_session_metadata() -> None:
    """Outside a session, in a session with no metadata and in one with ``{}``, the
    request's keys merge over the client's in the same way."""
    seen: list[httpx.Request] = []
    client = _client(seen, metadata={"tenant": "A"})
    client.chat.completions.create(model="m", messages=MSG, request_metadata={"x": 1})
    with client.session(name="bare"):
        client.chat.completions.create(
            model="m", messages=MSG, request_metadata={"x": 1}
        )
    with client.session(metadata={}):
        client.chat.completions.create(
            model="m", messages=MSG, request_metadata={"x": 1}
        )
    assert [_metadata(r) for r in seen] == [{"tenant": "A", "x": 1}] * 3


def test_an_empty_request_metadata_adds_nothing() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, metadata={"tenant": "A"})
    client.chat.completions.create(model="m", messages=MSG, request_metadata={})
    _client(seen).chat.completions.create(model="m", messages=MSG, request_metadata={})
    assert [_metadata(r) for r in seen] == [{"tenant": "A"}, {}]


def test_a_request_metadata_that_is_not_a_dict_is_sent_as_given() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, metadata={"tenant": "A"})
    client.chat.completions.create(
        model="m", messages=MSG, request_metadata='{"raw":1}'
    )
    with client.session(metadata={"cart": "c1"}):
        client.chat.completions.create(
            model="m", messages=MSG, request_metadata='{"raw":2}'
        )
    assert [r.headers["x-agentcc-metadata"] for r in seen] == ['{"raw":1}', '{"raw":2}']


def test_an_explicit_header_wins_over_every_layer() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, metadata={"tenant": "A"})
    client.chat.completions.create(
        model="m",
        messages=MSG,
        request_metadata={"x": 1},
        extra_headers={"x-agentcc-metadata": '{"explicit":true}'},
    )
    assert _metadata(seen[0]) == {"explicit": True}


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_a_with_options_copy_s_metadata_is_its_client_layer() -> None:
    seen: list[httpx.Request] = []
    parent = _client(seen, metadata={"tenant": "A", "tier": "gold"})
    copy = parent.with_options(metadata={"tenant": "B"})
    copy.chat.completions.create(model="m", messages=MSG, request_metadata={"x": 1})
    parent.chat.completions.create(model="m", messages=MSG, request_metadata={"x": 2})
    assert [_metadata(r) for r in seen] == [
        {"tenant": "B", "x": 1},
        {"tenant": "A", "tier": "gold", "x": 2},
    ]


def test_streams_files_and_responses_follow_the_rule() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, metadata={"tenant": "A"})
    md = {"request_metadata": {"x": 1}}
    list(client.chat.completions.create(model="m", messages=MSG, stream=True, **md))
    with client.chat.completions.stream(model="m", messages=MSG, **md) as s:
        s.get_final_text()
    client.files.create(file=("a.jsonl", b"{}"), purpose="batch", **md)
    client.responses.create(model="m", input="x", **md)
    client.completions.create(model="m", prompt="p", **md)
    assert [_metadata(r) for r in seen] == [{"tenant": "A", "x": 1}] * 5


def test_the_transport_merges_the_request_layer_over_the_client_s() -> None:
    from fi.gateway._base_client import RequestOptions

    base = _client([], metadata={"tenant": "A"})._get_base_client()
    opts = RequestOptions(method="POST", url="/v1/x")
    headers, _ = base._build_headers(opts, {"request_metadata": {"x": 1}})
    assert json.loads(headers["x-agentcc-metadata"]) == {"tenant": "A", "x": 1}
    assert json.loads(base._build_headers(opts)[0]["x-agentcc-metadata"]) == {
        "tenant": "A"
    }


async def test_the_async_client_follows_the_rule() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _reply(request)

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        metadata_mode="merge",
        metadata=LAYERS["client"],
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    await client.chat.completions.create(
        model="m", messages=MSG, request_metadata=LAYERS["request"]
    )
    async with client.session(metadata=LAYERS["session"]):
        await client.chat.completions.create(
            model="m", messages=MSG, request_metadata=LAYERS["request"]
        )
        async for _ in await client.chat.completions.create(
            model="m", messages=MSG, stream=True
        ):
            pass
    assert [_metadata(r) for r in seen] == [
        _expected(("client", "request")),
        _expected(("client", "session", "request")),
        _expected(("client", "session")),
    ]
