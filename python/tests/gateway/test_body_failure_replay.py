"""Post-header body failures preserve evidence without adding automatic replays."""
import pickle
from types import SimpleNamespace

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._transport import _async, _sync

ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
HEADERS = {
    "x-agentcc-dispatched": "true",
    "x-agentcc-request-id": ULID,
    "x-agentcc-client-request-id": "client-token",
}


def body_response(request, responses, error_cls, content_type, status=200, headers=None):
    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            assert "fi.gateway_evidence" in responses[-1].extensions
            yield b"{"
            raise error_cls("offline post-header failure", request=request)

        async def __aiter__(self):
            for chunk in self:
                yield chunk

    response = httpx.Response(
        status, headers={**(HEADERS if headers is None else headers), "content-type": content_type},
        stream=Body(),
    )
    responses.append(response)
    return response


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("resource", ["chat", "responses"])
@pytest.mark.parametrize("content_type", ["application/json", "text/event-stream"], ids=["cache-json", "sse"])
@pytest.mark.parametrize("error_cls", [httpx.ReadTimeout, httpx.ReadError])
async def test_success_stream_read_failure_exposes_captured_evidence(async_mode, resource, content_type, error_cls):
    callbacks, responses = [], []

    def handler(request):
        return body_response(request, responses, error_cls, content_type)

    kwargs = dict(api_key="fixture-only", base_url="https://gateway.test", max_retries=2,
                  # Published async Responses streams do not emit lifecycle events.
                  expanded_callback_events=async_mode and resource == "responses",
                  callbacks=[SimpleNamespace(on_error=lambda request, error: callbacks.append(error))])
    caught = None
    if async_mode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            async with gw.AsyncAgentCC(http_client=http, **kwargs) as client:
                try:
                    if resource == "chat":
                        stream = await client.chat.completions.create(model="fixture", messages=[], stream=True)
                    else:
                        stream = await client.responses.create(model="fixture", input="hi", stream=True)
                    async for _ in stream:
                        pass
                except Exception as exc:
                    caught = exc
    else:
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            with gw.AgentCC(http_client=http, **kwargs) as client:
                try:
                    if resource == "chat":
                        stream = client.chat.completions.create(model="fixture", messages=[], stream=True)
                    else:
                        stream = client.responses.create(model="fixture", input="hi", stream=True)
                    list(stream)
                except Exception as exc:
                    caught = exc
    assert caught is not None
    assert len(callbacks) == 1 and callbacks[0] is caught
    assert len(responses) == 1
    assert all(response.is_closed for response in responses)
    assert isinstance(caught, gw.AgentCCError), f"{type(caught).__name__} escaped with no SDK evidence"
    assert caught.gateway_evidence is responses[0].extensions["fi.gateway_evidence"]
    assert caught.dispatched is True and caught.gateway_request_id == ULID
    assert caught.client_request_id == "client-token"
    assert not any(isinstance(value, (httpx.Request, httpx.Response)) for value in vars(caught).values())
    assert b"fixture-only" not in pickle.dumps(caught)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("raw", [False, True], ids=["json", "binary"])
@pytest.mark.parametrize("error_cls", [httpx.ReadError, httpx.RemoteProtocolError])
async def test_post_header_non_timeout_transport_does_not_add_replays(monkeypatch, async_mode, raw, error_cls):
    callbacks, responses, attempts = [], [], []
    monkeypatch.setattr(_sync.time, "sleep", lambda seconds: None)

    async def no_sleep(seconds):
        pass

    monkeypatch.setattr(_async.anyio, "sleep", no_sleep)

    def handler(request):
        attempts.append(request)
        return body_response(request, responses, error_cls, "application/json")

    kwargs = dict(api_key="fixture-only", base_url="https://gateway.test", max_retries=2,
                  callbacks=[SimpleNamespace(on_error=lambda request, error: callbacks.append(error))])
    if async_mode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            async with gw.AsyncAgentCC(http_client=http, **kwargs) as client:
                with pytest.raises(Exception):
                    if raw:
                        await client.audio.speech.create(model="fixture", input="hi", voice="alloy")
                    else:
                        await client.chat.completions.create(model="fixture", messages=[])
    else:
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            with gw.AgentCC(http_client=http, **kwargs) as client:
                with pytest.raises(Exception):
                    if raw:
                        client.audio.speech.create(model="fixture", input="hi", voice="alloy")
                    else:
                        client.chat.completions.create(model="fixture", messages=[])
    assert len(attempts) == 1, f"previously terminal {error_cls.__name__} replayed {len(attempts) - 1} times"


async def call(handler, async_mode, raw, callbacks, policy):
    kwargs = dict(
        api_key="fixture-only", base_url="https://gateway.test", max_retries=2,
        retry_policy=gw.RetryPolicy(TimeoutRetries=2, ConnectionErrorRetries=2) if policy else None,
        callbacks=callbacks,
    )
    if async_mode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            async with gw.AsyncAgentCC(http_client=http, **kwargs) as client:
                if raw:
                    return await client.audio.speech.create(model="fixture", input="hi", voice="alloy")
                return await client.chat.completions.create(model="fixture", messages=[])
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with gw.AgentCC(http_client=http, **kwargs) as client:
            if raw:
                return client.audio.speech.create(model="fixture", input="hi", voice="alloy")
            return client.chat.completions.create(model="fixture", messages=[])


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("raw", [False, True], ids=["json", "binary"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("error_cls", [httpx.ReadTimeout, httpx.ReadError, httpx.RemoteProtocolError, httpx.ConnectError])
@pytest.mark.parametrize("status,dispatched", [
    (None, None), (200, None), (200, "false"), (200, "true"),
    (503, None), (503, "false"), (503, "true"),
], ids=["no-headers", "success-unknown", "success-not-dispatched", "success-dispatched",
        "refusal-unknown", "refusal-not-dispatched", "refusal-dispatched"])
async def test_translation_preserves_original_retry_eligibility(
    monkeypatch, async_mode, raw, policy, error_cls, status, dispatched,
):
    responses, attempts, callbacks, retries, sleeps = [], [], [], [], []
    monkeypatch.setattr(_sync.time, "sleep", sleeps.append)

    async def no_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(_async.anyio, "sleep", no_sleep)
    headers = {key: value for key, value in HEADERS.items() if key != "x-agentcc-dispatched"}
    if dispatched is not None:
        headers["x-agentcc-dispatched"] = dispatched

    def handler(request):
        attempts.append(request)
        if status is None:
            raise error_cls("offline send failure", request=request)
        return body_response(request, responses, error_cls, "application/json", status, headers)

    expected_error = gw.APITimeoutError if issubclass(error_cls, httpx.TimeoutException) else gw.APIConnectionError
    callback = SimpleNamespace(
        on_error=lambda request, error: callbacks.append(error),
        on_retry=lambda *args: retries.append(args),
    )
    with pytest.raises(expected_error) as caught:
        await call(handler, async_mode, raw, [callback], policy)
    # A may-have-sent failure is terminal; unreadable refusals use status budgets, not timeout budgets.
    if status is None:
        expected_attempts = 3 if error_cls is httpx.ConnectError else 1
    elif status == 503 and dispatched == "false":
        expected_attempts = 2 if policy else 3
    else:
        expected_attempts = 1
    assert len(attempts) == expected_attempts
    assert len(retries) == len(sleeps) == expected_attempts - 1
    assert callbacks == [caught.value]
    assert caught.value.request is None
    assert not any(isinstance(value, (httpx.Request, httpx.Response)) for value in vars(caught.value).values())
    if responses:
        assert caught.value.gateway_evidence is responses[-1].extensions["fi.gateway_evidence"]
        assert caught.value.dispatched == ("unknown" if dispatched is None else dispatched == "true")
        assert caught.value.gateway_request_id == ULID
        assert caught.value.client_request_id == "client-token"
        assert all(response.is_closed for response in responses)
    else:
        assert caught.value.gateway_evidence == gw.GatewayEvidence()
    payload = pickle.dumps(caught.value)
    assert b"fixture-only" not in payload
    assert pickle.loads(payload).gateway_evidence == caught.value.gateway_evidence


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("decode_kind", ["json", "content-encoding"])
async def test_success_body_decode_failure_is_terminal(monkeypatch, async_mode, policy, decode_kind):
    responses, sleeps = [], []
    monkeypatch.setattr(_sync.time, "sleep", sleeps.append)

    async def no_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(_async.anyio, "sleep", no_sleep)

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            yield b"not valid JSON or gzip"

        async def __aiter__(self):
            for part in self:
                yield part

    def handler(request):
        headers = dict(HEADERS)
        if decode_kind == "content-encoding":
            headers["content-encoding"] = "gzip"
        response = httpx.Response(200, headers=headers, stream=Body())
        responses.append(response)
        return response

    expected = ValueError if decode_kind == "json" else httpx.DecodingError
    with pytest.raises(expected):
        await call(handler, async_mode, decode_kind == "content-encoding", [], policy)
    assert len(responses) == 1 and responses[0].is_closed
    assert sleeps == []
