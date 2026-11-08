"""Final-header evidence survives failed reads and validates success identity."""
import json
import pickle
from types import SimpleNamespace

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._transport import _async, _sync
from fi.gateway.types.agentcc_metadata import AgentCCMetadata

ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
OTHER_ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
HEADERS = {
    "x-agentcc-dispatched": "true",
    "x-agentcc-request-id": ULID,
    "x-agentcc-client-request-id": "client-token",
}
ERRORS = [httpx.ReadTimeout, httpx.ReadError, httpx.RemoteProtocolError, httpx.ConnectError]


async def call(handler, async_mode, mode, callbacks, max_retries=0, *, expanded=False):
    kwargs = dict(
        api_key="fixture-only", base_url="https://gateway.test",
        max_retries=max_retries, callbacks=callbacks, expanded_callback_events=expanded,
    )
    if async_mode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            async with gw.AsyncAgentCC(http_client=http, **kwargs) as client:
                if mode == "binary":
                    return await client.audio.speech.create(model="fixture", input="hi", voice="alloy")
                return await client.chat.completions.create(model="fixture", messages=[], stream=mode == "stream")
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with gw.AgentCC(http_client=http, **kwargs) as client:
            if mode == "binary":
                return client.audio.speech.create(model="fixture", input="hi", voice="alloy")
            return client.chat.completions.create(model="fixture", messages=[], stream=mode == "stream")


def broken_response(request, responses, error_cls, status=200, request_id=ULID):
    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            response = responses[-1]
            assert "fi.gateway_evidence" in response.extensions
            response.headers["x-agentcc-request-id"] = "invalid-after-capture"
            response.headers["x-agentcc-dispatched"] = "false"
            yield b"{"
            raise error_cls("offline body failure", request=request)

        async def __aiter__(self):
            for part in self:
                yield part

    response = httpx.Response(status, stream=Body(), headers={**HEADERS, "x-agentcc-request-id": request_id})
    responses.append(response)
    return response


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode,status", [("json", 200), ("binary", 200), ("json", 403),
    ("binary", 503), ("stream", 403), ("stream", 503)])
@pytest.mark.parametrize("error_cls", ERRORS)
async def test_body_failure_retains_already_captured_final_headers(async_mode, mode, status, error_cls):
    callbacks, responses = [], []

    def handler(request):
        return broken_response(request, responses, error_cls, status)

    expected_error = gw.APITimeoutError if issubclass(error_cls, httpx.TimeoutException) else gw.APIConnectionError
    with pytest.raises(expected_error) as caught:
        await call(handler, async_mode, mode, [SimpleNamespace(on_error=lambda request, error: callbacks.append(error))])
    assert len(responses) == 1 and len(callbacks) == 1
    snapshot = responses[0].extensions["fi.gateway_evidence"]
    assert snapshot.gateway_request_id == ULID and snapshot.dispatched is True
    assert caught.value.gateway_evidence is snapshot
    assert callbacks[0] is caught.value
    assert callbacks[0].gateway_evidence is snapshot
    assert caught.value.gateway_request_id == ULID
    assert caught.value.client_request_id == "client-token"
    assert caught.value.request is None
    assert not any(isinstance(value, (httpx.Request, httpx.Response)) for value in vars(caught.value).values())
    assert responses[0].is_closed
    payload = pickle.dumps(caught.value)
    assert b"fixture-only" not in payload
    restored = pickle.loads(payload)
    assert restored.gateway_evidence == snapshot and restored.request is None


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary", "stream"])
@pytest.mark.parametrize("error_cls", ERRORS)
async def test_response_less_failure_has_unknown_evidence(async_mode, mode, error_cls):
    callbacks = []

    def handler(request):
        raise error_cls("offline send failure", request=request)

    expected_error = gw.APITimeoutError if issubclass(error_cls, httpx.TimeoutException) else gw.APIConnectionError
    with pytest.raises(expected_error) as caught:
        await call(handler, async_mode, mode, [SimpleNamespace(on_error=lambda request, error: callbacks.append(error))])
    assert len(callbacks) == 1 and callbacks[0] is caught.value
    assert caught.value.gateway_evidence == gw.GatewayEvidence()
    assert caught.value.request is None


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary"])
@pytest.mark.parametrize("final_response", [False, True], ids=["no-final-headers", "new-final-headers"])
async def test_retry_evidence_belongs_only_to_the_final_attempt(monkeypatch, async_mode, mode, final_response):
    responses, callbacks, attempts = [], [], []
    monkeypatch.setattr(_sync.time, "sleep", lambda seconds: None)

    async def no_sleep(seconds):
        pass

    monkeypatch.setattr(_async.anyio, "sleep", no_sleep)

    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            # A complete retryable refusal can replay; a successful body failure cannot.
            response = httpx.Response(503, headers={**HEADERS, "x-agentcc-dispatched": "false"},
                                      json={"error": {"message": "retryable fixture refusal"}})
            responses.append(response)
            return response
        if not final_response:
            raise httpx.ReadTimeout("offline send failure", request=request)
        return broken_response(request, responses, httpx.ReadTimeout, request_id=OTHER_ULID)

    with pytest.raises(gw.APITimeoutError) as caught:
        await call(handler, async_mode, mode, [SimpleNamespace(on_error=lambda request, error: callbacks.append(error))], max_retries=1)
    assert len(attempts) == 2 and len(callbacks) == 1
    expected = responses[-1].extensions["fi.gateway_evidence"] if final_response else gw.GatewayEvidence()
    assert caught.value.gateway_evidence == expected
    assert callbacks[0].gateway_evidence == expected
    assert caught.value.gateway_request_id == (OTHER_ULID if final_response else None)
    assert all(response.is_closed for response in responses)


ID_CASES = [[], ["invalid"], [ULID, ULID], [ULID]]
ID_LABELS = ["absent", "malformed", "duplicated", "valid"]


def assert_identity(metadata, ids):
    expected = ULID if ids == [ULID] else None
    assert metadata.gateway_request_id == expected
    assert metadata.request_id == expected
    assert metadata.model_dump()["request_id"] == expected
    assert json.loads(metadata.model_dump_json())["request_id"] == expected
    assert AgentCCMetadata.model_validate_json(metadata.model_dump_json()).request_id == expected


@pytest.mark.parametrize("ids", ID_CASES, ids=ID_LABELS)
def test_existing_success_request_id_alias_uses_canonical_validation(ids):
    headers = httpx.Headers([("x-agentcc-request-id", value) for value in ids])
    assert_identity(AgentCCMetadata.from_headers(headers), ids)


def test_metadata_default_identity_is_nullable():
    assert_identity(AgentCCMetadata(), [])


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary", "stream"])
@pytest.mark.parametrize("ids", ID_CASES, ids=ID_LABELS)
async def test_success_response_and_callback_share_validated_identity(async_mode, mode, ids):
    callbacks, responses = [], []

    def handler(request):
        headers = [("x-agentcc-request-id", value) for value in ids]
        if mode == "stream":
            response = httpx.Response(200, headers=headers + [("content-type", "text/event-stream")], content=b"data: [DONE]\n\n")
        else:
            response = httpx.Response(200, headers=headers, json={"id": "fixture", "object": "chat.completion", "created": 0, "model": "fixture", "choices": []})
        responses.append(response)
        return response

    callback = SimpleNamespace(
        on_request_end=lambda request, result: callbacks.append(result.agentcc),
        on_stream_start=lambda request, stream: callbacks.append(stream.agentcc),
    )
    result = await call(handler, async_mode, mode, [callback], expanded=mode == "binary")
    assert len(callbacks) == 1
    assert_identity(callbacks[0], ids)
    responses[0].headers["x-agentcc-request-id"] = OTHER_ULID
    assert_identity(AgentCCMetadata.from_headers(responses[0].headers, http_response=responses[0]), ids)
    if mode != "binary":
        assert_identity(result.agentcc, ids)
    if mode == "stream":
        if async_mode:
            await result.aclose()
        else:
            result.close()
