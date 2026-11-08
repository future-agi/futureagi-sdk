"""Public error identity and opt-in callback evidence, using offline exchanges."""
import traceback
from types import SimpleNamespace

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._transport import _async, _sync
from fi.gateway._transport._base import RequestOptions

KEY = "synthetic-traceback-credential"
PRIVATE = "synthetic-private-default"
UID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
HEADERS = {"x-agentcc-request-id": UID, "x-agentcc-dispatched": "true"}


def assert_clean_chain(error):
    """Render a real traceback and inspect both exception links and HTTP headers."""
    rendered = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    assert KEY not in rendered and PRIVATE not in rendered
    pending, seen = [error], set()
    while pending:
        value = pending.pop()
        if value is None or id(value) in seen:
            continue
        seen.add(id(value))
        text = str(value) + repr(value)
        assert KEY not in text and PRIVATE not in text
        if isinstance(value, BaseException):
            pending.extend((value.__cause__, value.__context__, value.args))
            pending.extend(getattr(value, "exceptions", ()))
            for name in ("request", "response"):
                try:
                    pending.append(getattr(value, name, None))
                except RuntimeError:
                    pass
        elif isinstance(value, (httpx.Request, httpx.Response)):
            pending.append(dict(value.headers))
            if isinstance(value, httpx.Response):
                pending.extend((value._request, *value.history, value.next_request))
            for name in ("authorization", "x-private"):
                if name in value.headers:
                    assert value.headers[name] == "[REDACTED]"
        elif isinstance(value, dict):
            pending.extend(value)
            pending.extend(value.values())
        elif isinstance(value, (tuple, list)):
            pending.extend(value)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("failure", ["connection", "timeout", "status"])
async def test_failing_call_traceback_preserves_clean_originals(async_mode, failure):
    requests, responses, originals, callbacks = [], [], [], []

    def handler(request):
        requests.append(request)
        assert request.headers["authorization"] == "Bearer " + KEY
        assert request.headers["x-private"] == PRIVATE
        response = httpx.Response(400, request=request, headers=HEADERS,
                                  json={"error": {"message": "synthetic refusal"}})
        responses.append(response)
        if failure == "status":
            return response
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as inner:
            outer = (httpx.ReadTimeout if failure == "timeout" else httpx.ConnectError)(
                "synthetic transport failure", request=request)
            originals.extend((outer, inner))
            raise outer from inner

    callback = SimpleNamespace(on_error=lambda request, error: callbacks.append(error))
    kwargs = dict(api_key=KEY, base_url="https://gateway.test", max_retries=0,
                  default_headers={"x-private": PRIVATE}, callbacks=[callback])
    if async_mode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            async with gw.AsyncAgentCC(http_client=http, **kwargs) as client:
                with pytest.raises(gw.AgentCCError) as caught:
                    await client.chat.completions.create(model="fixture", messages=[])
    else:
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            with gw.AgentCC(http_client=http, **kwargs) as client:
                with pytest.raises(gw.AgentCCError) as caught:
                    client.chat.completions.create(model="fixture", messages=[])
    error = caught.value
    assert len(requests) == 1
    assert callbacks == [error] and callbacks[0] is error
    if failure == "status":
        assert error.response is responses[0]
    else:
        assert error.__cause__ is originals[0]
        assert originals[0].__cause__ is originals[1]
        assert originals[0].__context__ is originals[1]
    assert_clean_chain(error)
    for original in originals:
        assert_clean_chain(original)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary"])
@pytest.mark.parametrize("expanded", [False, True], ids=["published", "expanded"])
async def test_raw_callback_evidence_is_opt_in(async_mode, mode, expanded):
    responses, callbacks = [], []

    def handler(request):
        response = httpx.Response(200, headers=HEADERS, json={"ok": True})
        responses.append(response)
        return response

    callback = SimpleNamespace(on_request_end=lambda request, result: callbacks.append(result))
    kwargs = dict(api_key=KEY, base_url="https://gateway.test", max_retries=0,
                  callbacks=[callback], owner=SimpleNamespace(_expanded_callback_events=expanded))
    options = RequestOptions("POST", "/v1/test")
    if async_mode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = _async.AsyncBaseClient(http_client=http, **kwargs)
            if mode == "binary":
                result = await client._request_raw_with_retry(options)
            else:
                result = await client._request_with_retry(options, dict)
    else:
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            client = _sync.SyncBaseClient(http_client=http, **kwargs)
            if mode == "binary":
                result = client._request_raw_with_retry(options)
            else:
                result = client._request_with_retry(options, dict)
    assert len(callbacks) == len(responses) == 1
    observed = callbacks[0]
    assert observed._parsed is result
    assert observed.status_code == 200
    if expanded:
        assert observed.headers == dict(responses[0].headers)
        assert observed.agentcc.http_response is responses[0]
        assert observed.agentcc.gateway_evidence is responses[0].extensions["fi.gateway_evidence"]
        assert observed.agentcc.gateway_request_id == UID
        assert observed.agentcc.dispatched is True
    else:
        assert observed.agentcc is None
        assert observed.headers == {}
