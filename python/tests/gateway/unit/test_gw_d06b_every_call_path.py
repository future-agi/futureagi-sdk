"""D-06b on every call path: one metadata rule for every request that takes ``request_metadata``.

``test_gw_d06b_metadata_layers.py`` pins the rule (the client's ``metadata=``, then the
active session's metadata, then the request's ``request_metadata``, merged key by key,
the later layer winning) on chat. This file runs all 8 combinations of the three layers
on every resource method that takes ``request_metadata``, sync and async, streamed and
not, and fails when a method that takes it is missing from the table: the methods are
found by walking both clients, so a new one cannot skip the rule unnoticed. (agentcc
1.x and the first port of ``audio.speech`` wrote the gateway parameters as extra
headers, so outside a session ``request_metadata`` replaced the client's metadata
there.)
"""

from __future__ import annotations

import inspect
import itertools
import json
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC

GW = "http://127.0.0.1:8090"
MSG = [{"role": "user", "content": "hi"}]
LAYERS = {
    "client": {"tenant": "A", "tier": "gold", "who": "client"},
    "session": {"cart": "c1", "tier": "silver", "who": "session"},
    "request": {"step": "pay", "who": "request"},
}
COMBINATIONS = [
    combo
    for n in range(4)
    for combo in itertools.combinations(("client", "session", "request"), n)
]
CHAT_SSE = (
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
    '"choices":[{"index":0,"delta":{"content":"hi"},"finish_reason":"stop"}]}\n\n'
    "data: [DONE]\n\n"
)
TEXT_SSE = (
    'data: {"id":"t","object":"text_completion","created":1,"model":"m",'
    '"choices":[{"index":0,"text":"hi","finish_reason":"stop"}]}\n\n'
    "data: [DONE]\n\n"
)
RESPONSES_SSE = (
    "event: response.completed\n"
    'data: {"type":"response.completed","sequence_number":0,'
    '"response":{"id":"r","status":"completed"}}\n\n'
)
JSON_REPLIES: dict[str, Any] = {
    "/v1/chat/completions": {
        "id": "c",
        "object": "chat.completion",
        "created": 1,
        "model": "m",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
    },
    "/v1/completions": {
        "id": "t",
        "object": "text_completion",
        "created": 1,
        "model": "m",
        "choices": [{"index": 0, "text": "hi", "finish_reason": "stop"}],
    },
    "/v1/responses": {"id": "r", "object": "response", "status": "completed"},
    "/v1/files": {
        "id": "f",
        "object": "file",
        "bytes": 1,
        "created_at": 1,
        "filename": "a.jsonl",
        "purpose": "batch",
    },
    "/v1/audio/transcriptions": {"text": "hi"},
    "/v1/audio/translations": {"text": "hi"},
}
STREAMS = {
    "/v1/chat/completions": CHAT_SSE,
    "/v1/completions": TEXT_SSE,
    "/v1/responses": RESPONSES_SSE,
}


def _reply(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/v1/audio/speech":
        return httpx.Response(200, content=b"ID3")
    if path in STREAMS and b'"stream":true' in request.content:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=STREAMS[path].encode(),
        )
    return httpx.Response(200, json=JSON_REPLIES[path])


def _chat_stream(c: Any, **md: Any) -> Any:
    with c.chat.completions.stream(model="m", messages=MSG, **md) as s:
        return s.get_final_text()


async def _achat_stream(c: Any, **md: Any) -> Any:
    manager = await c.chat.completions.stream(model="m", messages=MSG, **md)
    async with manager as s:
        return await s.get_final_completion()


async def _drain(stream: Any) -> None:
    async for _ in stream:
        pass


SpeechArgs = {"model": "tts-1", "input": "hi", "voice": "alloy"}
UploadArgs = {"file": b"RIFF", "model": "whisper-1"}
FileArgs = {"file": ("a.jsonl", b"{}"), "purpose": "batch"}

# call path -> (method it calls, sync call, async call)
CALLS: dict[str, tuple[str, Callable[..., Any], Callable[..., Awaitable[Any]]]] = {
    "chat.completions.create": (
        "chat.completions.create",
        lambda c, **md: c.chat.completions.create(model="m", messages=MSG, **md),
        lambda c, **md: c.chat.completions.create(model="m", messages=MSG, **md),
    ),
    "chat.completions.create(stream=True)": (
        "chat.completions.create",
        lambda c, **md: list(
            c.chat.completions.create(model="m", messages=MSG, stream=True, **md)
        ),
        lambda c, **md: _adrain(
            c.chat.completions.create(model="m", messages=MSG, stream=True, **md)
        ),
    ),
    "chat.completions.stream": ("chat.completions.stream", _chat_stream, _achat_stream),
    "completions.create": (
        "completions.create",
        lambda c, **md: c.completions.create(model="m", prompt="p", **md),
        lambda c, **md: c.completions.create(model="m", prompt="p", **md),
    ),
    "completions.create(stream=True)": (
        "completions.create",
        lambda c, **md: list(
            c.completions.create(model="m", prompt="p", stream=True, **md)
        ),
        lambda c, **md: _adrain(
            c.completions.create(model="m", prompt="p", stream=True, **md)
        ),
    ),
    "responses.create": (
        "responses.create",
        lambda c, **md: c.responses.create(model="m", input="x", **md),
        lambda c, **md: c.responses.create(model="m", input="x", **md),
    ),
    "responses.create(stream=True)": (
        "responses.create",
        lambda c, **md: list(
            c.responses.create(model="m", input="x", stream=True, **md)
        ),
        lambda c, **md: _adrain(
            c.responses.create(model="m", input="x", stream=True, **md)
        ),
    ),
    "files.create": (
        "files.create",
        lambda c, **md: c.files.create(**FileArgs, **md),
        lambda c, **md: c.files.create(**FileArgs, **md),
    ),
    "audio.speech.create": (
        "audio.speech.create",
        lambda c, **md: c.audio.speech.create(**SpeechArgs, **md),
        lambda c, **md: c.audio.speech.create(**SpeechArgs, **md),
    ),
    "audio.transcriptions.create": (
        "audio.transcriptions.create",
        lambda c, **md: c.audio.transcriptions.create(**UploadArgs, **md),
        lambda c, **md: c.audio.transcriptions.create(**UploadArgs, **md),
    ),
    "audio.translations.create": (
        "audio.translations.create",
        lambda c, **md: c.audio.translations.create(**UploadArgs, **md),
        lambda c, **md: c.audio.translations.create(**UploadArgs, **md),
    ),
}


async def _adrain(pending: Awaitable[Any]) -> None:
    await _drain(await pending)


def _methods_taking_request_metadata(client: Any) -> set[str]:
    """Every public resource method under *client* with a ``request_metadata`` parameter."""
    found: set[str] = set()

    def walk(obj: Any, prefix: str, depth: int) -> None:
        for name in dir(type(obj)):
            if name.startswith("_"):
                continue
            attr = inspect.getattr_static(obj, name)
            if inspect.isfunction(attr):
                if "request_metadata" in inspect.signature(attr).parameters:
                    found.add(prefix + name)
            elif depth < 3:
                child = getattr(obj, name, None)
                if hasattr(child, "_client"):  # a resource: walk into it
                    walk(child, f"{prefix}{name}.", depth + 1)

    walk(client, "", 0)
    return found


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


def _sync(seen: list[httpx.Request], **kw: Any) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _reply(request)

    return AgentCC(
        api_key="k",
        base_url=GW,
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        **kw,
    )


def _async(seen: list[httpx.Request], **kw: Any) -> AsyncAgentCC:
    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _reply(request)

    return AsyncAgentCC(
        api_key="k",
        base_url=GW,
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        **kw,
    )


@pytest.mark.parametrize("cls", [AgentCC, AsyncAgentCC], ids=["sync", "async"])
def test_the_table_covers_every_method_that_takes_request_metadata(cls: type) -> None:
    client = cls(api_key="k", base_url=GW)
    found = _methods_taking_request_metadata(client)
    assert {method for method, _, _ in CALLS.values()} == found
    assert "audio.speech.create" in found and len(found) >= 8


def test_the_walk_finds_a_new_method_that_takes_request_metadata() -> None:
    class Extra:
        def __init__(self, client: Any) -> None:
            self._client = client

        def create(self, *, request_metadata: Any = None) -> None:
            pass

    class Wider(AgentCC):
        @property
        def extra(self) -> Extra:
            return Extra(self)

    found = _methods_taking_request_metadata(Wider(api_key="k", base_url=GW))
    assert "extra.create" in found


@pytest.mark.parametrize("names", COMBINATIONS, ids=lambda c: "+".join(c) or "none")
@pytest.mark.parametrize("path", list(CALLS))
def test_every_sync_call_path_follows_the_rule(
    path: str, names: tuple[str, ...]
) -> None:
    seen: list[httpx.Request] = []
    client = _sync(seen, metadata=LAYERS["client"] if "client" in names else None)
    md = {"request_metadata": LAYERS["request"]} if "request" in names else {}
    call = CALLS[path][1]
    if "session" in names:
        with client.session(metadata=LAYERS["session"]):
            call(client, **md)
    else:
        call(client, **md)
    assert len(seen) == 1
    assert _metadata(seen[0]) == _expected(names)


@pytest.mark.parametrize("names", COMBINATIONS, ids=lambda c: "+".join(c) or "none")
@pytest.mark.parametrize("path", list(CALLS))
async def test_every_async_call_path_follows_the_rule(
    path: str, names: tuple[str, ...]
) -> None:
    seen: list[httpx.Request] = []
    client = _async(seen, metadata=LAYERS["client"] if "client" in names else None)
    md = {"request_metadata": LAYERS["request"]} if "request" in names else {}
    call = CALLS[path][2]
    if "session" in names:
        async with client.session(metadata=LAYERS["session"]):
            await call(client, **md)
    else:
        await call(client, **md)
    assert len(seen) == 1
    assert _metadata(seen[0]) == _expected(names)


@pytest.mark.parametrize("path", list(CALLS))
def test_an_explicit_header_still_wins_on_every_call_path(path: str) -> None:
    seen: list[httpx.Request] = []
    client = _sync(seen, metadata={"tenant": "A"})
    CALLS[path][1](
        client,
        request_metadata={"x": 1},
        extra_headers={"x-agentcc-metadata": '{"explicit":true}'},
    )
    assert _metadata(seen[0]) == {"explicit": True}
