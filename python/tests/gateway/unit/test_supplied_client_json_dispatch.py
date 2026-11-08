"""A supplied client's request() sees ``json=`` for ordinary JSON sends, as released.

The released transport called ``client.request(method=, url=, headers=, timeout=, json=)``.
A subclass that edits ``kwargs["json"]`` therefore changed the wire body, and the
supplied client's own default headers (Accept, Accept-Encoding) still applied because
the SDK sent only its own header dict. Uploads pass ``data=``/``files=``; streaming
keeps ``build_request`` plus ``send`` and never calls ``request()``.

This module is self-contained so the same cases can run against the released export.
"""
import inspect
import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]
ORIGIN = "https://gateway.example.test"
CHAT = {"id": "reply", "object": "chat.completion", "created": 0, "model": "fixture", "choices": []}
EDITED = "supplied-client-policy"


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def policy(kwargs):
    if isinstance(kwargs.get("json"), dict):
        kwargs["json"] = {**kwargs["json"], "model": EDITED}
    if isinstance(kwargs.get("data"), dict):
        kwargs["data"] = {**kwargs["data"], "model": EDITED}


def custom_client(async_mode, serve, calls, **client_options):
    def record(kwargs):
        calls.append(kwargs.copy())
        policy(kwargs)

    if async_mode:
        class Custom(httpx.AsyncClient):
            async def request(self, *args, **kwargs):
                record(kwargs)
                return await super().request(*args, **kwargs)
    else:
        class Custom(httpx.Client):
            def request(self, *args, **kwargs):
                record(kwargs)
                return super().request(*args, **kwargs)
    return Custom(transport=httpx.MockTransport(serve), trust_env=False, **client_options)


def reply(resource):
    if resource == "speech":
        return httpx.Response(200, content=b"audio")
    if resource == "form":
        return httpx.Response(200, json={"text": "ok"})
    if resource == "stream":
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=b"data: [DONE]\n\n")
    return httpx.Response(200, json=CHAT)


async def send(client, resource, async_mode):
    if resource == "form":
        return await resolve(client.audio.transcriptions.create(model="fixture", file=("test.wav", b"audio")))
    if resource == "speech":
        return await resolve(client.audio.speech.create(model="fixture", input="speak", voice="alloy"))
    result = await resolve(client.chat.completions.create(
        model="fixture", messages=[{"role": "user", "content": "hi"}], stream=resource == "stream"))
    if resource == "stream":
        if async_mode:
            async for _ in result:
                pass
        else:
            list(result)
    return result


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("resource", ["chat", "speech", "form", "stream"])
async def test_request_override_edits_reach_the_wire_as_released(async_mode, resource):
    calls, bodies = [], []

    def serve(request):
        bodies.append(request.content)
        return reply(resource)

    http = custom_client(async_mode, serve, calls)
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-policy-key", base_url=ORIGIN, http_client=http, max_retries=0)
    try:
        await send(client, resource, async_mode)
        if resource == "stream":
            assert calls == []
            assert json.loads(bodies[0])["model"] == "fixture"
            return
        assert len(calls) == 1
        if resource == "form":
            assert "data" in calls[0] and "files" in calls[0] and "json" not in calls[0]
            assert EDITED.encode() in bodies[0]
        else:
            assert isinstance(calls[0].get("json"), dict) and "content" not in calls[0]
            assert json.loads(bodies[0])["model"] == EDITED
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
async def test_supplied_client_default_headers_still_apply(async_mode):
    seen, calls = [], []

    def serve(request):
        seen.append(request)
        return reply("chat")

    http = custom_client(async_mode, serve, calls,
                         headers={"Accept": "application/x-supplied", "Accept-Encoding": "identity"})
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-policy-key", base_url=ORIGIN, http_client=http, max_retries=0)
    try:
        await send(client, "chat", async_mode)
        assert seen[0].headers["accept"] == "application/x-supplied"
        assert seen[0].headers["accept-encoding"] == "identity"
        assert seen[0].headers["content-type"] == "application/json"
        assert "content" not in calls[0]
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
async def test_a_request_without_a_body_passes_json_none(async_mode):
    calls = []

    def serve(request):
        return httpx.Response(200, json={"object": "list", "data": []})

    http = custom_client(async_mode, serve, calls)
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-policy-key", base_url=ORIGIN, http_client=http, max_retries=0)
    try:
        await resolve(client.models.list())
        assert len(calls) == 1 and calls[0].get("json") is None and "content" not in calls[0]
        assert calls[0]["method"] == "GET"
    finally:
        await resolve(http.aclose() if async_mode else http.close())
