"""Gateway regressions adapted from the public catalog SDK's smoke suites.

Only mock transports are used. The root client, environment names, callbacks and
removed compatibility aliases retain this SDK's contract.
"""
import asyncio
import io
import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._exceptions import APIStatusError, BadGatewayError, GuardrailWarning, RateLimitError
from fi.gateway._streaming import AsyncSSEParser, SSEParser

BASE = "http://localhost:9011"
COMPLETION = {
    "id": "chat-1", "object": "chat.completion", "created": 1, "model": "mock",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
}
MSG = [{"role": "user", "content": "hi"}]


def gw(handler, async_=False, **kwargs):
    http = (httpx.AsyncClient if async_ else httpx.Client)(transport=httpx.MockTransport(handler))
    return (AsyncAgentCC if async_ else AgentCC)(api_key="fixture-gateway", base_url=BASE,
                                               http_client=http, max_retries=kwargs.pop("max_retries", 0), **kwargs)


@pytest.mark.parametrize("async_", [False, True])
def test_sse_network_boundaries_and_utf8(async_):
    raw = 'data: {"content":"café"}\r\n\r\ndata: [DONE]\r\n\r\n'.encode()
    # Every byte is a separate network chunk, including CR/LF and UTF-8 pairs.
    chunks = [raw[i:i+1] for i in range(len(raw))]
    async def run():
        async def source():
            for chunk in chunks:
                yield chunk
        return [event.data async for event in AsyncSSEParser(source())]
    result = asyncio.run(run()) if async_ else [event.data for event in SSEParser(iter(chunks))]
    assert result == ['{"content":"café"}', "[DONE]"]


def test_sse_trailing_line():
    assert [e.data for e in SSEParser(iter([b"data: a\r\n\r\ndata: b"]))] == ["a", "b"]


@pytest.mark.parametrize("error", ["unavailable", None, [], 3])
def test_non_object_error_envelope(error):
    response = httpx.Response(502, json={"error": error})
    exc = APIStatusError.from_response(response)
    assert isinstance(exc, BadGatewayError)
    if isinstance(error, str):
        assert exc.message == error


@pytest.mark.parametrize("async_", [False, True])
@pytest.mark.parametrize("status,error", [(429, RateLimitError), (246, GuardrailWarning)])
def test_stream_status_closes_response(async_, status, error):
    responses = []
    def handler(request):
        response = httpx.Response(status, stream=httpx.ByteStream(b'{"error":{"message":"stop"}}'))
        responses.append(response)
        return response
    client = gw(handler, async_)
    async def run():
        with pytest.raises(error):
            await client.chat.completions.create(model="mock", messages=MSG, stream=True)
    if async_:
        asyncio.run(run())
    else:
        with pytest.raises(error):
            client.chat.completions.create(model="mock", messages=MSG, stream=True)
    assert responses[0].is_closed


@pytest.mark.parametrize("async_", [False, True])
def test_streamed_json_cache_hit(async_):
    client = gw(lambda r: httpx.Response(200, stream=httpx.ByteStream(json.dumps(COMPLETION).encode()),
                                        headers={"content-type": "application/json"}), async_)
    async def run():
        stream = await client.chat.completions.create(model="mock", messages=MSG, stream=True)
        return [chunk async for chunk in stream]
    chunks = asyncio.run(run()) if async_ else list(client.chat.completions.create(model="mock", messages=MSG, stream=True))
    assert chunks[0].choices[0].delta.content == "hi"


@pytest.mark.parametrize("async_", [False, True])
def test_embeddings_usage_without_completion_tokens(async_):
    body = {"object": "list", "model": "mock", "data": [], "usage": {"prompt_tokens": 2, "total_tokens": 2}}
    client = gw(lambda r: httpx.Response(200, json=body), async_)
    result = client.embeddings.create(model="mock", input="hi")
    if async_:
        result = asyncio.run(result)
    assert result.usage.total_tokens == 2
    assert result.usage.completion_tokens == 0


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
@pytest.mark.parametrize("async_", [False, True])
@pytest.mark.parametrize("method", ["files.create", "files.content", "responses.delete"])
def test_resource_paths_share_retries_and_callbacks(async_, method):
    seen, callbacks = [], []
    class Callback:
        def on_request_end(self, request, result):
            callbacks.append(result)
    def handler(request):
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(503, json={"error": {"message": "busy"}}, headers={"retry-after": "0"})
        if method == "files.create":
            assert request.headers["content-type"].startswith("multipart/form-data")
            assert b'filename="sample.jsonl"' in request.content
            assert b'name="purpose"' in request.content
            return httpx.Response(200, json={"id": "f1", "object": "file", "bytes": 3, "created_at": 1,
                                           "filename": "sample.jsonl", "purpose": "assistants"})
        return httpx.Response(200, content=b"file" if method == "files.content" else b"")
    client = gw(handler, async_, max_retries=1, callbacks=[Callback()])
    if method == "files.create":
        result = client.files.create(file=("sample.jsonl", io.BytesIO(b"{}\n")), purpose="assistants")
    elif method == "files.content":
        result = client.files.content("f1")
    else:
        result = client.responses.delete("r1")
    if async_:
        result = asyncio.run(result)
    assert len(seen) == 2
    assert len(callbacks) == 1
    if method == "files.content":
        assert result == b"file"
    if method == "responses.delete":
        assert result is None


@pytest.mark.parametrize("async_", [False, True])
def test_session_tracks_successful_requests(async_):
    client = gw(lambda r: httpx.Response(200, json=COMPLETION, headers={"x-agentcc-cost": "0.0025"}), async_)
    async def run():
        with client.session(name="checkout", session_id="s1") as session:
            await client.chat.completions.create(model="mock", messages=MSG)
            await client.chat.completions.create(model="mock", messages=MSG)
        await client.chat.completions.create(model="mock", messages=MSG)
        return session
    if async_:
        session = asyncio.run(run())
    else:
        with client.session(name="checkout", session_id="s1") as session:
            client.chat.completions.create(model="mock", messages=MSG)
            client.chat.completions.create(model="mock", messages=MSG)
        client.chat.completions.create(model="mock", messages=MSG)
    assert session.request_count == 2
    assert session.total_tokens == 10
    assert session.total_cost == pytest.approx(0.005)


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
@pytest.mark.parametrize("async_", [False, True])
def test_a_copy_made_inside_a_session_is_outside_it(async_):
    # The session belongs to the client it was opened on. A with_options() copy is a new
    # client: it neither sends the session headers nor counts toward the session, so the
    # session's totals always match the requests that carried its id.
    seen = []
    retained = []
    def handle(request):
        retained.append(request)
        seen.append(httpx.Request(request.method, request.url, headers=list(request.headers.raw)))
        return httpx.Response(200, json=COMPLETION)
    client = gw(handle, async_)
    async def run():
        async with client.session(name="checkout", session_id="s1") as session:
            await client.chat.completions.create(model="mock", messages=MSG)
            await client.with_options(timeout=5).chat.completions.create(model="mock", messages=MSG)
        return session
    if async_:
        session = asyncio.run(run())
    else:
        with client.session(name="checkout", session_id="s1") as session:
            client.chat.completions.create(model="mock", messages=MSG)
            client.with_options(timeout=5).chat.completions.create(model="mock", messages=MSG)
    assert [r.headers.get("x-agentcc-session-id") for r in seen] == ["s1", None]
    assert [r.headers.get("x-agentcc-session-id") for r in retained] == ["[REDACTED]", None]
    assert session.request_count == 1
    assert session.total_tokens == 5
