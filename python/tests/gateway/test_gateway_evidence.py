"""Final response evidence is an immutable header snapshot, never body inference."""
from dataclasses import FrozenInstanceError
import json
import pickle
from types import SimpleNamespace

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._retry_policy import no_code_outcome_unknown
from fi.gateway._streaming import Stream, AsyncStream, ResponseStream, AsyncResponseStream
from fi.gateway._transport import _sync, _async
from fi.gateway._transport._base import RequestOptions

ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
HEADERS = [("X-AgentCC-Request-ID", ULID), ("X-AgentCC-Client-Request-ID", "client-correlation"),
           ("X-AgentCC-Dispatched", "false")]


def error(headers, body=None):
    return gw.APIStatusError.from_response(httpx.Response(503, headers=headers,
        json=body or {"error": {"message": "refused", "metadata": {"dispatched": False, "request_id": ULID}}}))


def evidence(value):
    result = getattr(value, "gateway_evidence", None)
    assert result is not None, "missing typed gateway evidence"
    return result


@pytest.mark.parametrize("values,expected", [
    ([], "unknown"), (["true"], True), (["false"], False), ([" \tfalse\t "], False),
    (["TRUE"], "unknown"), (["False"], "unknown"), ([""], "unknown"), (["0"], "unknown"),
    (["false, false"], "unknown"), (["true, false"], "unknown"),
    (["false", "false"], "unknown"), (["true", "false"], "unknown"),
    ([b"\xc2\xa0false\xc2\xa0"], "unknown"), (["\nfalse"], "unknown"),
])
def test_dispatch_wire_grammar(values, expected):
    headers = [(b"X-AgentCC-Dispatched", v.encode() if isinstance(v, str) else v) for v in values]
    exc = error(headers)
    assert evidence(exc).dispatched == expected
    assert exc.dispatched == expected
    assert evidence(exc).gateway_request_id is None


@pytest.mark.parametrize("ids", [[], [""], ["provider-id"], [ULID.lower()], ["8" + ULID[1:]],
    [ULID[:-1]], [ULID + "0"], [ULID.replace("F", "I")], [ULID, ULID], [ULID + ", " + ULID], [" " + ULID]])
def test_invalid_gateway_identity_does_not_substitute(ids):
    headers = [("x-agentcc-request-id", v) for v in ids]
    headers += [("x-request-id", ULID), ("x-agentcc-client-request-id", ULID)]
    exc = error(headers)
    assert exc.request_id is None
    assert evidence(exc).gateway_request_id is None
    assert exc.client_request_id == ULID
    assert no_code_outcome_unknown(503, None, httpx.Headers(headers)) == bool(ids)


def test_header_identity_separation_and_safe_pickle():
    response = httpx.Response(400, headers=HEADERS,
        request=httpx.Request("POST", "https://gateway.test", headers={"Authorization": "fixture-sensitive"}),
        json={"error": {"code": "managed_model_ambiguous", "metadata": {"dispatched": True, "request_id": "body-id"}}})
    exc = gw.APIStatusError.from_response(response)
    snapshot = evidence(exc)
    assert snapshot.gateway_request_id == exc.request_id == exc.gateway_request_id == ULID
    assert snapshot.client_request_id == exc.client_request_id == "client-correlation"
    assert snapshot.dispatched is False
    response.headers["x-agentcc-dispatched"] = "true"
    assert exc.dispatched is False
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        snapshot.dispatched = True
    payload = pickle.dumps(exc)
    assert b"fixture-sensitive" not in payload
    restored = pickle.loads(payload)
    assert restored.response is None and evidence(restored) == snapshot


@pytest.mark.parametrize("present", [False, True])
@pytest.mark.parametrize("dispatch,blocked", [(None, True), ("true", True), ("false", False), ("FALSE", True), (" \tfalse ", False)])
def test_no_code_guard_uses_same_strict_parser(present, dispatch, blocked):
    headers = [("x-agentcc-request-id", "invalid-but-present")] if present else []
    if dispatch is not None:
        headers.append(("x-agentcc-dispatched", dispatch))
    assert no_code_outcome_unknown(503, None, httpx.Headers(headers)) == (present and blocked)


def test_unobservable_headers_are_not_proven_absent():
    exc = gw.APIStatusError.from_response(SimpleNamespace(status_code=503, json=lambda: {"error": {}}))
    assert evidence(exc).dispatched == "unknown"
    assert no_code_outcome_unknown(503, None, None)


def test_evidence_captured_before_factory_body_decode():
    class Response:
        status_code = 400
        headers = httpx.Headers(HEADERS)
        extensions = {}

        def json(self):
            assert "fi.gateway_evidence" in self.extensions
            self.headers["x-agentcc-dispatched"] = "true"
            return {"error": {"code": "managed_model_ambiguous"}}

    assert error(HEADERS).request_id == ULID
    assert evidence(gw.APIStatusError.from_response(Response())).dispatched is False


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary", "stream"])
@pytest.mark.parametrize("status", [200, 403])
async def test_transport_captures_before_first_byte(async_mode, mode, status):
    responses = []
    callbacks = []
    body = {"error": {"code": "managed_model_unpriced"}} if status == 403 else {"ok": True}

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            assert "fi.gateway_evidence" in responses[-1].extensions
            yield json.dumps(body).encode()

        async def __aiter__(self):
            for chunk in self:
                yield chunk

    def handler(request):
        response = httpx.Response(status, headers=HEADERS, stream=Body())
        responses.append(response)
        return response

    options = RequestOptions("POST", "/v1/test")
    cb = SimpleNamespace(on_request_end=lambda request, result: callbacks.append(result.agentcc),
                         on_error=lambda request, exc: callbacks.append(exc))
    common = dict(api_key="fixture-only", base_url="https://gateway.test", max_retries=0, callbacks=[cb])
    if async_mode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = _async.AsyncBaseClient(http_client=http, **common)
            try:
                if mode == "stream":
                    response = await client._stream_request(options)
                    await response.aread()
                    await response.aclose()
                elif mode == "binary":
                    await client._request_raw_with_retry(options)
                else:
                    await client._request_with_retry(options, dict)
            except gw.APIStatusError as exc:
                assert status == 403 and evidence(exc).dispatched is False
    else:
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            client = _sync.SyncBaseClient(http_client=http, **common)
            try:
                if mode == "stream":
                    response = client._stream_request(options)
                    response.read()
                    response.close()
                elif mode == "binary":
                    client._request_raw_with_retry(options)
                else:
                    client._request_with_retry(options, dict)
            except gw.APIStatusError as exc:
                assert status == 403 and evidence(exc).dispatched is False
    assert responses[0].extensions["fi.gateway_evidence"].gateway_request_id == ULID
    if mode != "stream":
        assert evidence(callbacks[0]).gateway_request_id == ULID


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("native", [False, True], ids=["chat", "responses"])
async def test_stream_retains_initial_evidence_after_body_error(async_mode, native):
    frame = {"type": "error", "code": "provider_error", "message": "failed", "metadata": {"dispatched": False, "request_id": "forged"}}
    payload = frame if native else {"error": frame}
    response = httpx.Response(200, headers={**dict(HEADERS), "content-type": "text/event-stream"},
        content=("event: error\ndata: " + json.dumps(payload) + "\n\n").encode())
    cls = (AsyncResponseStream if native else AsyncStream) if async_mode else (ResponseStream if native else Stream)
    stream = cls(response)
    snapshot = evidence(stream.agentcc)
    response.headers["x-agentcc-dispatched"] = "true"
    with pytest.raises(gw.StreamError) as caught:
        if async_mode:
            async for _ in stream:
                pass
        else:
            list(stream)
    assert evidence(caught.value) == snapshot
    assert snapshot.dispatched is False and caught.value.request_id == ULID
    assert caught.value.body == frame
    assert response.is_closed


def test_public_evidence_exports():
    assert getattr(gw, "GatewayEvidence", None) is not None
    assert getattr(gw, "DispatchState", None) is not None
