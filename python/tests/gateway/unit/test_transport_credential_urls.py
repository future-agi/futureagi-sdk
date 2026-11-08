"""Credential headers stay on the wire, not retained requests or request URLs."""
import inspect
import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._exceptions import AgentCCError
from fi.gateway.callbacks.base import CallbackHandler

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]
ORIGIN = "https://gateway.example.test"
MASK = "[REDACTED]"
WIDER_HEADERS = ("x-auth-token", "x-access-token", "x-api-token", "x-agentcc-api-key", "x-secret-key")
QUERY_NAMES = ("key", "api_key", "token", "access_token")
CHAT = {"id": "reply", "object": "chat.completion", "created": 0, "model": "test", "choices": []}


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


async def invoke(client, path, async_mode, **params):
    if path == "raw":
        return await resolve(client.audio.speech.create(model="test", input="speak", voice="alloy", **params))
    if path == "form":
        return await resolve(client.files.create(file=("input.dat", b"sample"), purpose="assistants", **params))
    result = await resolve(client.chat.completions.create(model="test", messages=[], stream=path == "stream", **params))
    if path == "stream":
        if async_mode:
            async for _ in result:
                pass
        else:
            list(result)
    return result


def reply(path):
    if path == "raw":
        return httpx.Response(200, content=b"audio")
    if path == "stream":
        return httpx.Response(200, text="data: [DONE]\n\n", headers={"content-type": "text/event-stream"})
    if path == "form":
        return httpx.Response(200, json={"id": "file-test", "object": "file", "bytes": 6,
            "created_at": 0, "filename": "input.dat", "purpose": "assistants"})
    return httpx.Response(200, json=CHAT)


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("path", ["parsed", "raw", "form", "stream"])
@pytest.mark.parametrize("outcome", ["success", "connection"])
async def test_wider_headers_scrubbed_after_every_send(async_mode, redact, path, outcome):
    requests, wire = [], []
    headers = {name.swapcase(): "synthetic-" + name for name in WIDER_HEADERS}
    original = dict(headers)

    def serve(request):
        requests.append(request)
        wire.append(dict(request.headers))
        if outcome == "connection":
            raise httpx.ConnectError("synthetic failure", request=request)
        return reply(path)

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-sdk-key", base_url=ORIGIN, http_client=http, default_headers=headers,
        redact_messages=redact, max_retries=0,
    )
    try:
        if outcome == "connection":
            with pytest.raises(AgentCCError):
                await invoke(client, path, async_mode)
        else:
            await invoke(client, path, async_mode)
        assert len(wire) == 1
        for name, value in headers.items():
            assert wire[0][name.lower()] == value
            assert requests[0].headers[name] == MASK
        assert headers == original
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
async def test_stream_request_is_scrubbed_before_deferred_body_read(async_mode, redact):
    responses, wire, during_read, callbacks = [], [], [], []

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            during_read.append(dict(responses[0].request.headers))
            yield b"data: [DONE]\n\n"

        async def __aiter__(self):
            for part in self:
                yield part

    class Observe(CallbackHandler):
        def on_stream_start(self, request, info):
            callbacks.append((responses[0].is_stream_consumed, dict(responses[0].request.headers)))

    def serve(request):
        wire.append(dict(request.headers))
        response = httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Body())
        responses.append(response)
        return response

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-sdk-key", base_url=ORIGIN, http_client=http, callbacks=[Observe()],
        redact_messages=redact, max_retries=0,
    )
    try:
        stream = await resolve(client.chat.completions.create(model="test", messages=[], stream=True))
        assert wire[0]["authorization"] == "Bearer synthetic-sdk-key"
        assert callbacks and callbacks[0][0] is False
        assert callbacks[0][1]["authorization"] == MASK
        assert not responses[0].is_stream_consumed and during_read == []
        assert responses[0].request.headers["authorization"] == MASK
        if async_mode:
            async for _ in stream:
                pass
        else:
            list(stream)
        assert during_read[0]["authorization"] == MASK
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("path", ["parsed", "raw", "form", "stream"])
@pytest.mark.parametrize("name", QUERY_NAMES)
@pytest.mark.parametrize("source", ["default_query", "callback_url", "base_url", "http_client", "extra_query"])
async def test_credential_query_parameters_refused_before_send(async_mode, path, name, source):
    sent = []
    marker = "synthetic-query-credential"

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            if source == "callback_url":
                # Encoded names and mixed case must not bypass URL validation.
                request.url += "?%" + format(ord(name[0].upper()), "02x") + name[1:] + "=" + marker

    def serve(request):
        sent.append(request)
        return reply(path)

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(serve),
        params={name: marker} if source == "http_client" else None,
    )
    try:
        with pytest.raises(AgentCCError) as caught:
            client = (AsyncAgentCC if async_mode else AgentCC)(
                api_key="synthetic-sdk-key", http_client=http, callbacks=[Edit()], max_retries=0,
                base_url=ORIGIN + ("?" + name + "=" + marker if source == "base_url" else ""),
                default_query={name.upper(): marker} if source == "default_query" else {"page": "1"},
            )
            if source == "extra_query":
                client = client.with_options(extra_query={name: marker})
            await invoke(client, path, async_mode)
        assert sent == []
        assert marker not in str(caught.value)
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("path", ["parsed", "raw", "form", "stream"])
@pytest.mark.parametrize("source", ["base_url", "callback_url"])
async def test_userinfo_refused_before_send(async_mode, path, source):
    sent = []
    unsafe = "https://synthetic-user:synthetic-password@gateway.example.test"

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            if source == "callback_url":
                request.url = unsafe + request.url

    def serve(request):
        sent.append(request)
        return reply(path)

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    try:
        with pytest.raises(AgentCCError):
            client = (AsyncAgentCC if async_mode else AgentCC)(
                api_key="synthetic-sdk-key", base_url=unsafe if source == "base_url" else ORIGIN,
                http_client=http, callbacks=[Edit()], max_retries=0,
            )
            await invoke(client, path, async_mode)
        assert sent == []
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("path", ["parsed", "raw", "form", "stream"])
async def test_default_query_and_agentcc_params_do_not_leak_into_url(async_mode, path):
    wire = []
    metadata = {name: "synthetic-metadata-" + name for name in QUERY_NAMES}

    def serve(request):
        wire.append((request.url, dict(request.headers)))
        return reply(path)

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-sdk-key", base_url=ORIGIN, http_client=http,
        default_query={"page": "1", "label": "safe&token=not-a-query-parameter"}, max_retries=0,
    )
    try:
        await invoke(client, path, async_mode, session_id="synthetic-session", request_metadata=metadata)
        url, headers = wire[0]
        assert not url.username and not url.password
        assert not set(QUERY_NAMES).intersection(key.lower() for key in url.params)
        assert dict(url.params) == {"page": "1", "label": "safe&token=not-a-query-parameter"}
        assert headers["authorization"] == "Bearer synthetic-sdk-key"
        assert headers["x-agentcc-session-id"] == "synthetic-session"
        assert json.loads(headers["x-agentcc-metadata"]) == metadata
        assert all(value not in str(url) for value in metadata.values())
    finally:
        await resolve(http.aclose() if async_mode else http.close())
