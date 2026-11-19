"""Known exchanges remain private even when optional graph discovery cannot finish."""
import inspect
import logging

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._transport import _scrub
from fi.gateway.callbacks.logging import LoggingCallback

ORIGIN = "https://gateway.example.test"
KEY = "synthetic-fail-closed-key"
PRIVATE = "synthetic-client-header"
MASK = "[REDACTED]"
CHAT = {"id": "reply", "object": "chat.completion", "created": 0, "model": "fixture", "choices": []}


@pytest.fixture
def anyio_backend():
    return "asyncio"


def limit(monkeypatch, cap):
    if cap == "error":
        def broken(*args, **kwargs):
            raise RuntimeError("synthetic walker failure")
        monkeypatch.setattr(_scrub._Walk, "run", broken)
    else:
        monkeypatch.setattr(_scrub, cap, 0 if cap != "DEPTH_CAP" else -1)


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.mark.parametrize("cap", ["TEXT_NODE_CAP", "TEXT_DEPTH_CAP"])
def test_diagnostic_budget_failure_masks_log_record_payload(monkeypatch, cap):
    payload = [{"diagnostic": {KEY, PRIVATE}}, bytearray(KEY.encode())]
    error = ValueError(payload)
    monkeypatch.setattr(_scrub, cap, 0)
    _scrub.scrub_error_text(error, (KEY.encode(), PRIVATE.encode()))
    record = logging.makeLogRecord({"msg": "Failure: %s", "args": (error,),
                                   "diagnostic": error, "exc_info": (type(error), error, None)})
    assert KEY not in record.getMessage() and PRIVATE not in record.getMessage()
    assert KEY not in repr(vars(record)) and PRIVATE not in repr(vars(record))
    assert MASK in str(error)
    assert payload[0]["diagnostic"] == {KEY, PRIVATE}


def test_diagnostic_scrub_never_calls_exception_attribute_hooks():
    calls = []

    class DiagnosticError(Exception):
        def __getattribute__(self, name):
            calls.append(("get", name))
            raise AssertionError("caller hook")

        def __setattr__(self, name, value):
            calls.append(("set", name))
            raise AssertionError("caller hook")

    error = DiagnosticError(KEY)
    _scrub.scrub_error_text(error, (KEY.encode(),))
    assert calls == []
    assert BaseException.__dict__["args"].__get__(error) == (MASK,)


def test_diagnostic_scrub_never_rehashes_caller_dictionary_keys():
    calls = []

    class Key:
        def __hash__(self):
            calls.append(True)
            return 1

    payload = {Key(): KEY}
    error = ValueError(payload)
    calls.clear()
    _scrub.scrub_error_text(error, (KEY.encode(),))
    assert calls == []
    assert KEY not in str(error)


@pytest.mark.parametrize("cap", ["NODE_CAP", "SCAN_CAP", "DEPTH_CAP", "error"])
def test_known_exchange_headers_do_not_depend_on_discovery(monkeypatch, cap):
    request = httpx.Request("GET", ORIGIN, headers={"Authorization": KEY, "X-Private": PRIVATE})
    response = httpx.Response(503, request=request, headers={"Set-Cookie": KEY, "X-Private": "gateway-value"})
    error = httpx.ReadTimeout("offline", request=request)
    limit(monkeypatch, cap)
    _scrub.scrub_sent_request(request, response, error, frozenset({"x-private"}))
    assert request.headers["authorization"] == MASK
    assert request.headers["x-private"] == MASK
    assert response.headers["set-cookie"] == MASK
    assert response.headers["x-private"] == "gateway-value"
    assert error.request is request


@pytest.mark.parametrize("cap", ["NODE_CAP", "SCAN_CAP", "DEPTH_CAP", "error"])
@pytest.mark.parametrize("kind", ["request", "status"])
def test_known_http_error_request_is_masked_without_discovery(monkeypatch, cap, kind):
    request = httpx.Request("GET", ORIGIN, headers={"Authorization": KEY, "X-Private": PRIVATE})
    error = (httpx.ReadTimeout("offline", request=request) if kind == "request" else
             httpx.HTTPStatusError("offline", request=request, response=httpx.Response(400, request=request)))
    limit(monkeypatch, cap)
    _scrub.scrub_sent_request(None, None, error, frozenset({"x-private"}))
    assert error.request is request
    assert request.headers["authorization"] == request.headers["x-private"] == MASK


@pytest.mark.parametrize("utility", ["health", "key"])
@pytest.mark.parametrize("failure", [False, True])
@pytest.mark.parametrize("cap", ["NODE_CAP", "SCAN_CAP", "error"])
def test_utility_exchanges_fail_closed(monkeypatch, utility, failure, cap):
    import httpx._api as api
    from fi.gateway._utils import check_valid_key, health_check

    sent, wire = [], []
    original = httpx.Client

    def serve(request):
        sent.append(request)
        wire.append(request.headers["authorization"])
        if failure:
            raise httpx.ReadTimeout("diagnostic Bearer " + KEY, request=request)
        return httpx.Response(200)

    monkeypatch.setattr(api, "Client", lambda *args, **kwargs: original(
        *args, **{**kwargs, "transport": httpx.MockTransport(serve), "trust_env": False}))
    limit(monkeypatch, cap)
    result = health_check(api_key=KEY, base_url=ORIGIN) if utility == "health" else check_valid_key(KEY, ORIGIN)
    assert wire == ["Bearer " + KEY]
    assert sent[0].headers["authorization"] == MASK
    if utility == "health":
        assert result["status"] == ("error" if failure else "ok")
        assert KEY not in str(result)
    else:
        assert result is not failure


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("auth_kind", ["none", "basic", "digest", "function"])
@pytest.mark.parametrize("cap", ["NODE_CAP", "SCAN_CAP", "DEPTH_CAP", "error"])
async def test_builtin_auth_and_hooks_keep_wire_values_but_not_retained_values(monkeypatch, asynchronous, auth_kind, cap):
    sent, responses, wire, callback_headers = [], [], [], []

    def serve(request):
        sent.append(request)
        wire.append(dict(request.headers))
        if auth_kind == "digest" and len(sent) == 1:
            return httpx.Response(401, headers={"www-authenticate": 'Digest realm="fixture", nonce="synthetic-nonce", qop="auth"'})
        return httpx.Response(200, json=CHAT, headers={"Set-Cookie": "synthetic-cookie"})

    def response_hook(response):
        responses.append(response)

    async def async_response_hook(response):
        response_hook(response)

    class Capture:
        def on_request_end(self, request, response):
            callback_headers.append(dict(response.agentcc.http_response.request.headers))

    auth = {"none": None, "basic": httpx.BasicAuth("fixture", "synthetic-password"),
            "digest": httpx.DigestAuth("fixture", "synthetic-password"),
            "function": lambda request: request}[auth_kind]
    http = (httpx.AsyncClient if asynchronous else httpx.Client)(
        transport=httpx.MockTransport(serve), auth=auth, trust_env=False,
        event_hooks={"response": [async_response_hook if asynchronous else response_hook]})
    with pytest.warns(DeprecationWarning, match="Deprecated gateway compatibility options: callbacks"):
        sdk = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url=ORIGIN,
            http_client=http, default_headers={"X-Private": PRIVATE}, callbacks=[Capture()], max_retries=0)
    limit(monkeypatch, cap)
    try:
        await resolve(sdk.chat.completions.create(model="fixture", messages=[]))
        assert len(sent) == (2 if auth_kind == "digest" else 1)
        assert all(row["x-private"] == PRIVATE for row in wire)
        assert all(row["authorization"] != MASK for row in wire)
        assert callback_headers and callback_headers[0]["authorization"] == MASK
        assert callback_headers[0]["x-private"] == MASK
        for request in sent:
            assert request.headers["authorization"] == MASK
            assert request.headers["x-private"] == MASK
        assert responses[-1].headers["set-cookie"] == MASK
    finally:
        await resolve(http.aclose() if asynchronous else http.close())


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("outcome", ["retry", "redirect", "error"])
@pytest.mark.parametrize("cap", ["NODE_CAP", "SCAN_CAP", "DEPTH_CAP", "error"])
async def test_retry_redirect_and_sdk_log_records_are_private(monkeypatch, caplog, asynchronous, outcome, cap):
    sent, responses, wire = [], [], []

    def serve(request):
        sent.append(request)
        wire.append(dict(request.headers))
        if outcome == "error":
            raise httpx.ConnectError("offline", request=request)
        if outcome == "retry" and len(sent) == 1:
            response = httpx.Response(503, headers={"retry-after": "0", "x-agentcc-dispatched": "false"})
        elif outcome == "redirect":
            response = httpx.Response(307, headers={"location": ORIGIN + "/elsewhere"})
        else:
            response = httpx.Response(200, json=CHAT)
        responses.append(response)
        return response

    http = (httpx.AsyncClient if asynchronous else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    with pytest.warns(DeprecationWarning, match="Deprecated gateway compatibility options: callbacks"):
        sdk = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url=ORIGIN,
            http_client=http, default_headers={"X-Private": PRIVATE},
            callbacks=[LoggingCallback(logger_name="gateway.failclosed")], max_retries=1 if outcome == "retry" else 0)
    limit(monkeypatch, cap)
    caplog.set_level(logging.DEBUG, logger="gateway.failclosed")
    try:
        caught = None
        try:
            await resolve(sdk.chat.completions.create(model="fixture", messages=[]))
        except Exception as error:
            caught = error
        assert (caught is not None) == (outcome in {"error", "redirect"})
        assert len(sent) == (2 if outcome == "retry" else 1)
        assert all(row["authorization"] == "Bearer " + KEY for row in wire)
        for request in sent:
            assert request.headers["authorization"] == MASK
            assert request.headers["x-private"] == MASK
        for response in responses:
            if response.next_request is not None:
                assert response.next_request.headers["authorization"] == MASK
                assert response.next_request.headers["x-private"] == MASK
        assert caplog.records
        for record in caplog.records:
            assert KEY not in record.getMessage() and PRIVATE not in record.getMessage()
            assert KEY not in repr(vars(record)) and PRIVATE not in repr(vars(record))
            for arg in record.args if isinstance(record.args, tuple) else ():
                if isinstance(arg, BaseException) and isinstance(arg.__cause__, httpx.RequestError):
                    assert arg.__cause__.request.headers["authorization"] == MASK
    finally:
        await resolve(http.aclose() if asynchronous else http.close())
