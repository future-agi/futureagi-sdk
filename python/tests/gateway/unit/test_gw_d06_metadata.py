"""Explicit merge mode sends session metadata in one JSON header.

Published replacement and per-key session defaults are covered separately.
"""

from __future__ import annotations

import pytest

import json

import httpx
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

from ._published_helpers import wire_snapshot
from fi.gateway import AgentCC, AsyncAgentCC, Session, create_headers

GW = "http://127.0.0.1:8090"
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}


def _client(seen: list[httpx.Request], **kwargs: object) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(wire_snapshot(request))
        if request.url.path == "/v1/audio/speech":
            return httpx.Response(200, content=b"mp3")
        return httpx.Response(200, json=COMPLETION)

    return AgentCC(
        api_key="k",
        base_url=GW,
        metadata_mode="merge",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        **kwargs,
    )


def _metadata(request: httpx.Request) -> object:
    assert not [
        k for k in request.headers if k.lower().startswith("x-agentcc-metadata-")
    ]
    raw = request.headers.get("x-agentcc-metadata")
    return None if raw is None else json.loads(raw)


def test_session_to_headers_is_compact_json_and_keeps_types() -> None:
    session = Session(session_id="s1", metadata={"team": "a", "n": 2, "ok": True}, metadata_mode="merge")
    headers = session.to_headers()
    assert headers == {
        "x-agentcc-session-id": "s1",
        "x-agentcc-metadata": '{"team":"a","n":2,"ok":true}',
    }


def test_a_session_without_metadata_sends_no_metadata_header() -> None:
    assert "x-agentcc-metadata" not in Session(session_id="s1").to_headers()


def test_session_metadata_reaches_the_wire() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen)
    with client.session(name="checkout", metadata={"team": "a"}) as sess:
        sess.step("pay")
        client.chat.completions.create(model="m", messages=[])
    headers = seen[0].headers
    assert headers["x-agentcc-session-name"] == "checkout"
    assert headers["x-agentcc-session-path"] == "/pay"
    assert _metadata(seen[0]) == {"team": "a"}


def test_request_metadata_wins_key_by_key_over_session_metadata() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen)
    with client.session(metadata={"team": "a", "env": "dev"}):
        client.chat.completions.create(
            model="m", messages=[], request_metadata={"env": "prod"}
        )
    assert _metadata(seen[0]) == {"team": "a", "env": "prod"}


def test_outside_a_session_request_metadata_merges_over_client_metadata() -> None:
    """D-06b: agentcc 1.x replaced the client's metadata with the request's here."""
    seen: list[httpx.Request] = []
    client = _client(seen, metadata={"tier": "gold"})
    client.chat.completions.create(model="m", messages=[])
    client.chat.completions.create(model="m", messages=[], request_metadata={"x": 1})
    with client.session(name="no-metadata"):
        client.chat.completions.create(
            model="m", messages=[], request_metadata={"y": 2}
        )
    assert [_metadata(r) for r in seen] == [
        {"tier": "gold"},
        {"tier": "gold", "x": 1},
        {"tier": "gold", "y": 2},
    ]


def test_inside_a_session_client_metadata_stays_under_the_session_metadata() -> None:
    """agentcc 1.0 sent the client's JSON header plus per-key session headers; the
    gateway kept the client's keys. One header with the session's keys alone lost them."""
    seen: list[httpx.Request] = []
    client = _client(seen, metadata={"tenant": "A", "tier": "gold"})
    client.chat.completions.create(model="m", messages=[])
    with client.session(name="s", metadata={"cart": "c1", "tier": "silver"}):
        client.chat.completions.create(model="m", messages=[])
        client.chat.completions.create(
            model="m", messages=[], request_metadata={"cart": "c2", "step": "pay"}
        )
    client.chat.completions.create(model="m", messages=[])
    assert [_metadata(r) for r in seen] == [
        {"tenant": "A", "tier": "gold"},
        {"tenant": "A", "tier": "silver", "cart": "c1"},
        {"tenant": "A", "tier": "silver", "cart": "c2", "step": "pay"},
        {"tenant": "A", "tier": "gold"},
    ]


def test_every_session_resource_layers_the_client_metadata() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, metadata={"tenant": "A"})
    with client.session(metadata={"cart": "c1"}):
        client.chat.completions.create(model="m", messages=[])
        with client.chat.completions.stream(model="m", messages=[]) as stream:
            stream.get_final_text()
        client.audio.speech.create(model="tts", input="hi", voice="v")
    assert [_metadata(r) for r in seen] == [{"tenant": "A", "cart": "c1"}] * 3


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_a_with_options_copy_layers_its_own_metadata() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, metadata={"tenant": "A"})
    copy = client.with_options(metadata={"tenant": "B"})
    with copy.session(metadata={"cart": "c1"}):
        copy.chat.completions.create(model="m", messages=[])
    with client.session(metadata={"cart": "c2"}):
        client.chat.completions.create(model="m", messages=[])
    assert [_metadata(r) for r in seen] == [
        {"tenant": "B", "cart": "c1"},
        {"tenant": "A", "cart": "c2"},
    ]


def test_merge_without_request_params_layers_the_header_too() -> None:
    """A caller that passes no gateway params still gets client < session in the header."""
    from fi.gateway._agentcc_params import merge_session_headers

    client = AgentCC(api_key="k", base_url=GW, metadata={"tenant": "A"}, metadata_mode="merge")
    with client.session(session_id="s1", metadata={"cart": "c1"}):
        merged = merge_session_headers(client, {"x-extra": "e"})
    assert json.loads(merged["x-agentcc-metadata"]) == {"tenant": "A", "cart": "c1"}
    assert merged["x-agentcc-session-id"] == "s1"
    assert merged["x-extra"] == "e"


def test_an_explicit_header_still_wins() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen)
    with client.session(metadata={"team": "a"}):
        client.chat.completions.create(
            model="m", messages=[], extra_headers={"x-agentcc-metadata": '{"raw":1}'}
        )
    assert _metadata(seen[0]) == {"raw": 1}


def test_speech_sends_metadata_as_json_too() -> None:
    """1.x speech put str(dict), a Python repr, in the header."""
    seen: list[httpx.Request] = []
    client = _client(seen)
    client.audio.speech.create(
        model="tts", input="hi", voice="v", request_metadata={"a": "b"}
    )
    with client.session(metadata={"team": "a"}):
        client.audio.speech.create(model="tts", input="hi", voice="v")
    assert [_metadata(r) for r in seen] == [{"a": "b"}, {"team": "a"}]


def test_text_completions_merge_the_same_way() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(wire_snapshot(request))
        body = {
            "id": "c",
            "object": "text_completion",
            "created": 1,
            "model": "m",
            "choices": [],
        }
        return httpx.Response(200, json=body)

    client = AgentCC(
        api_key="k",
        base_url=GW,
        metadata_mode="merge",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with client.session(metadata={"team": "a"}):
        client.completions.create(model="m", prompt="p", request_metadata={"b": 1})
    assert _metadata(seen[0]) == {"team": "a", "b": 1}


async def test_the_async_client_too() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(wire_snapshot(request))
        return httpx.Response(200, json=COMPLETION)

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        metadata_mode="merge",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    async with client.session(metadata={"team": "a"}):
        await client.chat.completions.create(model="m", messages=[])
    assert _metadata(seen[0]) == {"team": "a"}


async def test_the_async_client_layers_client_metadata_inside_a_session() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(wire_snapshot(request))
        return httpx.Response(200, json=COMPLETION)

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        metadata_mode="merge",
        metadata={"tenant": "A"},
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    async with client.session(metadata={"cart": "c1"}):
        await client.chat.completions.create(model="m", messages=[])
        await client.chat.completions.create(
            model="m", messages=[], request_metadata={"step": "pay"}
        )
    await client.chat.completions.create(
        model="m", messages=[], request_metadata={"x": 1}
    )
    assert [_metadata(r) for r in seen] == [
        {"tenant": "A", "cart": "c1"},
        {"tenant": "A", "cart": "c1", "step": "pay"},
        {"tenant": "A", "x": 1},
    ]


def test_create_headers_metadata_was_already_json() -> None:
    assert create_headers(metadata={"a": 1}) == {"x-agentcc-metadata": '{"a":1}'}
