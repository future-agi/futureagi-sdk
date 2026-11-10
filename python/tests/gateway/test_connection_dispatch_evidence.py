"""Public dispatch evidence without changing transport retry budgets."""
from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from fi.gateway import APIConnectionError, APITimeoutError, AgentCC, AsyncAgentCC
from fi.gateway._transport import _async, _sync

REQUEST = {"model": "example/model", "messages": [{"role": "user", "content": "Hello"}]}
PRE_SEND = [httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout]
UNKNOWN = [httpx.ReadError, httpx.ReadTimeout, httpx.WriteError, httpx.WriteTimeout,
           httpx.RemoteProtocolError]


@pytest.fixture
def sleeps(monkeypatch):
    recorded = []

    async def asleep(delay):
        recorded.append(delay)

    monkeypatch.setattr(_sync, "time", SimpleNamespace(sleep=recorded.append))
    monkeypatch.setattr(_async, "anyio", SimpleNamespace(sleep=asleep))
    return recorded


async def invoke(asynchronous, streaming, handler, retries):
    options = {"api_key": "synthetic-key", "base_url": "https://gateway.test",
               "max_retries": retries}
    if asynchronous:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = AsyncAgentCC(http_client=http, **options)
            response = await client.chat.completions.create(**REQUEST, stream=streaming)
            return [chunk async for chunk in response] if streaming else response
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        client = AgentCC(http_client=http, **options)
        response = client.chat.completions.create(**REQUEST, stream=streaming)
        return list(response) if streaming else response


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("streaming", [False, True], ids=["json", "stream"])
@pytest.mark.parametrize("error_type", PRE_SEND + UNKNOWN)
async def test_connection_error_exposes_dispatch_evidence(asynchronous, streaming, error_type, sleeps):
    calls = []

    def handler(request):
        calls.append(request)
        raise error_type("synthetic transport failure", request=request)

    # Non-streaming exhausts its existing budget; streaming still tries only once.
    with pytest.raises(APIConnectionError) as caught:
        await invoke(asynchronous, streaming, handler, retries=2)
    expected_attempts = 3 if error_type in PRE_SEND and not streaming else 1
    assert len(calls) == expected_attempts
    assert len(sleeps) == expected_attempts - 1
    error = caught.value
    assert isinstance(error, APITimeoutError) == issubclass(error_type, httpx.TimeoutException)
    assert error.gateway_evidence.gateway_request_id is None
    assert error.gateway_evidence.client_request_id is None
    assert error.request_not_sent is (error_type in PRE_SEND)
    # Response-header evidence retains its published meaning when no response exists.
    assert error.gateway_evidence.dispatched == "unknown"
    assert error.dispatched == "unknown"


class BrokenBody(httpx.SyncByteStream, httpx.AsyncByteStream):
    def __iter__(self):
        raise httpx.ConnectError("synthetic failure after response headers")
        yield b""  # pragma: no cover

    async def __aiter__(self):
        raise httpx.ConnectError("synthetic failure after response headers")
        yield b""  # pragma: no cover


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("streaming", [False, True], ids=["json", "stream"])
@pytest.mark.parametrize("dispatch", ["true", None, "invalid"])
async def test_connection_class_after_headers_does_not_prove_pre_dispatch(
    asynchronous, streaming, dispatch, sleeps,
):
    calls = []

    def handler(request):
        calls.append(request)
        headers = {"x-agentcc-request-id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"}
        if dispatch is not None:
            headers["x-agentcc-dispatched"] = dispatch
        # Error responses are consumed while opening even a streaming request.
        return httpx.Response(503, headers=headers, stream=BrokenBody())

    with pytest.raises(APIConnectionError) as caught:
        await invoke(asynchronous, streaming, handler, retries=2)
    assert len(calls) == 1
    assert sleeps == []
    assert caught.value.gateway_evidence.dispatched == (True if dispatch == "true" else "unknown")
    assert caught.value.dispatched is not False
    assert caught.value.request_not_sent is False
    assert caught.value.gateway_request_id == "01ARZ3NDEKTSV4RRFFQ69G5FAV"


def success(streaming):
    if streaming:
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
                              content=b"data: [DONE]\n\n")
    return httpx.Response(200, json={
        "id": "synthetic-completion", "object": "chat.completion", "created": 0,
        "model": "example/model", "choices": [{"index": 0, "finish_reason": "stop",
                                                "message": {"role": "assistant", "content": "ok"}}],
    })


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("streaming", [False, True], ids=["json", "stream"])
async def test_available_second_attempt_does_not_change_stream_policy(asynchronous, streaming, sleeps):
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            raise httpx.ConnectError("synthetic pre-dispatch failure", request=request)
        return success(streaming)

    if streaming:
        with pytest.raises(APIConnectionError) as caught:
            await invoke(asynchronous, streaming, handler, retries=2)
        assert len(calls) == 1
        assert sleeps == []
        assert caught.value.request_not_sent is True
    else:
        response = await invoke(asynchronous, streaming, handler, retries=2)
        assert response.choices[0].message.content == "ok"
        assert len(calls) == 2
        assert len(sleeps) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("error_type", [httpx.ConnectError, httpx.ReadTimeout])
async def test_caller_retries_once_only_with_negative_dispatch_evidence(asynchronous, error_type, sleeps):
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            raise error_type("synthetic transport failure", request=request)
        return success(streaming=True)

    async def caller():
        try:
            return await invoke(asynchronous, True, handler, retries=0)
        except APIConnectionError as error:
            if error.request_not_sent is not True:
                raise
        return await invoke(asynchronous, True, handler, retries=0)

    if error_type is httpx.ConnectError:
        assert await caller() == []
        assert len(calls) == 2
    else:
        with pytest.raises(APITimeoutError):
            await caller()
        assert len(calls) == 1
    assert sleeps == []


@pytest.mark.parametrize("error_type", [APIConnectionError, APITimeoutError])
def test_constructed_connection_error_without_transport_evidence_is_unknown(error_type):
    error = error_type("synthetic failure")
    assert error.gateway_evidence.dispatched == "unknown"
    assert error.request_not_sent is False
