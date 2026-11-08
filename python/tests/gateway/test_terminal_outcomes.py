"""Offline coverage for terminal body failures and ambiguous dispatch outcomes."""
import json
import pickle
from types import SimpleNamespace

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._transport import _async, _sync

UID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
HEADERS = {"x-agentcc-request-id": UID, "x-agentcc-client-request-id": "client-token",
           "content-type": "application/json"}
SECRET = "synthetic-credential-only"


def assert_safe(error):
    """Check stored state and exception chains, not interpreter stack frames."""
    seen = set()

    def visit(value):
        if id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, httpx.Request):
            assert not any(name in value.headers for name in
                           ("authorization", "x-api-key", "x-agentcc-config", "x-agentcc-session-id"))
        if isinstance(value, (str, bytes)):
            assert SECRET not in (value.decode(errors="replace") if isinstance(value, bytes) else value)
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                visit(item)
        elif isinstance(value, BaseException):
            visit(vars(value))
            visit(value.args)
            visit(value.__cause__)
            visit(value.__context__)
        elif isinstance(value, httpx.Response):
            visit(vars(value))
    visit(error)
    assert SECRET.encode() not in pickle.dumps(error)


async def exercise(monkeypatch, *, async_mode=False, mode="json", policy=False,
                   status=200, dispatch="true", error_cls=httpx.ReadTimeout,
                   hook=False, auth=False, malformed=None, close_failure=False,
                   request_id=UID, code=None, constructor_failure=False):
    attempts, responses, errors, retries, sleeps, hook_order = [], [], [], [], [], []
    monkeypatch.setattr(_sync.time, "sleep", sleeps.append)

    async def no_sleep(seconds):
        sleeps.append(seconds)
    monkeypatch.setattr(_async.anyio, "sleep", no_sleep)

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            if malformed:
                yield b"invalid JSON and gzip"
            elif error_cls is None:
                yield json.dumps({"error": {"code": code, "message": "fixture refusal"}}).encode()
            else:
                yield b"{"
                raise error_cls("synthetic body failure", request=attempts[-1])

        async def __aiter__(self):
            for part in self:
                yield part

        def close(self):
            if close_failure:
                raise httpx.ReadError("synthetic cleanup failure", request=attempts[-1])

        async def aclose(self):
            self.close()

    def handler(request):
        attempts.append(request)
        if status is None:
            raise error_cls("synthetic send failure", request=request)
        headers = dict(HEADERS)
        if request_id is None:
            headers.pop("x-agentcc-request-id")
        else:
            headers["x-agentcc-request-id"] = request_id
        if dispatch is not None:
            headers["x-agentcc-dispatched"] = dispatch
        if malformed == "gzip":
            headers["content-encoding"] = "gzip"
        response = httpx.Response(status, headers=headers, stream=Body())
        responses.append(response)
        return response

    def sync_hook(response):
        hook_order.append("first")
        response.read()

    async def async_hook(response):
        hook_order.append("first")
        await response.aread()

    def sync_last(response):
        hook_order.append("last")

    async def async_last(response):
        hook_order.append("last")

    class ReadAuth(httpx.Auth):
        requires_response_body = True
        def auth_flow(self, request):
            yield request

    if constructor_failure:
        import fi.gateway._streaming as streaming
        def fail_construction(*args, **kwargs):
            raise httpx.ReadTimeout("synthetic constructor failure", request=attempts[-1])
        monkeypatch.setattr(streaming, "AsyncStream", fail_construction)
        monkeypatch.setattr(streaming, "AsyncResponseStream", fail_construction)

    kwargs = dict(api_key=SECRET, base_url="https://gateway.test", max_retries=2,
                  session_id=SECRET, default_headers={"x-api-key": SECRET, "x-agentcc-config": SECRET},
                  callbacks=[SimpleNamespace(on_error=lambda request, error: errors.append(error),
                                             on_retry=lambda *args: retries.append(args))])
    if policy:
        kwargs["retry_policy"] = gw.RetryPolicy(TimeoutRetries=2, ConnectionErrorRetries=2,
                                               ServiceUnavailableRetries=2, GatewayTimeoutRetries=2)
    hooks = {"response": [async_hook, async_last] if async_mode else [sync_hook, sync_last]} if hook else {}
    http_cls = httpx.AsyncClient if async_mode else httpx.Client
    http = http_cls(transport=httpx.MockTransport(handler), event_hooks=hooks,
                    auth=ReadAuth() if auth else None)
    original_hooks = {name: list(values) for name, values in http.event_hooks.items()}
    caught = None
    try:
        if async_mode:
            async with gw.AsyncAgentCC(http_client=http, **kwargs) as client:
                if mode == "binary":
                    await client.audio.speech.create(model="fixture", input="hi", voice="alloy")
                elif mode == "responses":
                    result = await client.responses.create(model="fixture", input="hi", stream=True)
                    async for _ in result:
                        pass
                else:
                    result = await client.chat.completions.create(model="fixture", messages=[], stream=mode == "stream")
                    if mode == "stream":
                        async for _ in result:
                            pass
        else:
            with gw.AgentCC(http_client=http, **kwargs) as client:
                if mode == "binary":
                    client.audio.speech.create(model="fixture", input="hi", voice="alloy")
                elif mode == "responses":
                    list(client.responses.create(model="fixture", input="hi", stream=True))
                else:
                    result = client.chat.completions.create(model="fixture", messages=[], stream=mode == "stream")
                    if mode == "stream":
                        list(result)
    except Exception as exc:
        caught = exc
    finally:
        assert http.event_hooks == original_hooks
        if async_mode:
            await http.aclose()
        else:
            http.close()
    assert caught is not None
    return SimpleNamespace(error=caught, attempts=attempts, responses=responses,
                           errors=errors, retries=retries, sleeps=sleeps, hook_order=hook_order)


def assert_terminal(result, dispatch="true", has_headers=True):
    assert len(result.attempts) == 1
    assert result.retries == result.sleeps == []
    assert result.errors == [result.error]
    evidence = result.error.gateway_evidence
    assert evidence.dispatched == ("unknown" if dispatch not in ("true", "false") else dispatch == "true")
    if has_headers:
        assert evidence is result.responses[0].extensions["fi.gateway_evidence"]
        assert evidence.gateway_request_id == UID
        assert evidence.client_request_id == "client-token"
        assert result.responses[0].is_closed
    assert_safe(result.error)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary", "stream"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("malformed", [None, "gzip", "json"])
async def test_completion_warning_body_failure_is_terminal(monkeypatch, async_mode, mode, policy, malformed):
    result = await exercise(monkeypatch, async_mode=async_mode, mode=mode, policy=policy,
                            status=246, dispatch=None, malformed=malformed)
    assert_terminal(result, None)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("dispatch", ["true", None])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("consumer", ["hook", "auth"])
@pytest.mark.parametrize("mode", ["json", "binary", "stream"])
async def test_headers_captured_before_caller_body_consumers(monkeypatch, async_mode, dispatch, policy, consumer, mode):
    result = await exercise(monkeypatch, async_mode=async_mode, dispatch=dispatch, policy=policy,
                            mode=mode, hook=consumer == "hook", auth=consumer == "auth")
    assert_terminal(result, dispatch)
    assert isinstance(result.error, gw.APITimeoutError)
    if consumer == "hook":
        assert result.hook_order == ["first"]


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary", "stream", "responses"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("dispatch", ["true", None])
async def test_gzip_decode_errors_are_safe_and_keep_evidence(monkeypatch, async_mode, mode, policy, dispatch):
    result = await exercise(monkeypatch, async_mode=async_mode, mode=mode, policy=policy,
                            dispatch=dispatch, malformed="gzip")
    assert_terminal(result, dispatch)
    assert isinstance(result.error, (httpx.DecodingError, gw.StreamError))


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["stream", "responses"])
@pytest.mark.parametrize("malformed", [None, "gzip"])
async def test_failed_cleanup_preserves_original_error(monkeypatch, async_mode, mode, malformed):
    result = await exercise(monkeypatch, async_mode=async_mode, mode=mode, close_failure=True, malformed=malformed)
    assert_terminal(result)
    # Async cache bodies stay lazy and retain their released StreamError class.
    expected = gw.StreamError if async_mode else httpx.DecodingError if malformed else gw.APITimeoutError
    assert isinstance(result.error, expected)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary", "stream"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("error_cls", [httpx.ReadTimeout, httpx.WriteTimeout, httpx.ReadError,
    httpx.WriteError, httpx.RemoteProtocolError, httpx.CloseError, httpx.TransportError, httpx.TimeoutException])
async def test_may_have_sent_failure_never_replays(monkeypatch, async_mode, mode, policy, error_cls):
    result = await exercise(monkeypatch, async_mode=async_mode, mode=mode, policy=policy,
                            status=None, dispatch=None, error_cls=error_cls)
    assert_terminal(result, None, has_headers=False)
    expected = gw.APITimeoutError if issubclass(error_cls, httpx.TimeoutException) else gw.APIConnectionError
    assert isinstance(result.error, expected)
    assert "check whether" in str(result.error).lower()
    assert "before" in str(result.error).lower()


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary", "stream"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("error_cls", [httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout])
async def test_provably_pre_send_failures_keep_retry_budget(monkeypatch, async_mode, mode, policy, error_cls):
    result = await exercise(monkeypatch, async_mode=async_mode, mode=mode, policy=policy,
                            status=None, dispatch=None, error_cls=error_cls)
    # Stream opening has never replayed, including failures before the first byte.
    expected = 1 if mode == "stream" else 3
    assert len(result.attempts) == expected
    assert len(result.retries) == len(result.sleeps) == expected - 1
    assert result.errors == [result.error]
    assert_safe(result.error)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary", "stream"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("dispatch", [None, "TRUE", "false, true"])
@pytest.mark.parametrize("body_failure", [False, True])
@pytest.mark.parametrize("code", [None, "unrecognized"])
async def test_gateway_unknown_dispatch_is_terminal(monkeypatch, async_mode, mode, policy, dispatch, body_failure, code):
    result = await exercise(monkeypatch, async_mode=async_mode, mode=mode, policy=policy,
                            status=503, dispatch=dispatch, code=code,
                            error_cls=httpx.ReadTimeout if body_failure else None)
    assert_terminal(result, dispatch)
    guidance = str(result.error) + " " + str(getattr(result.error, "remedy", ""))
    assert "check whether" in guidance.lower()


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("mode", ["json", "binary"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("status,dispatch,request_id,attempts", [
    (503, "false", UID, 3), (503, None, None, 3), (403, "false", UID, 1),
])
@pytest.mark.parametrize("malformed", [None, "gzip"])
async def test_unreadable_refusal_keeps_status_retry_rules(monkeypatch, async_mode, mode, policy,
                                                         status, dispatch, request_id, attempts, malformed):
    result = await exercise(monkeypatch, async_mode=async_mode, mode=mode, policy=policy,
                            status=status, dispatch=dispatch, request_id=request_id, malformed=malformed)
    assert len(result.attempts) == attempts
    assert len(result.retries) == len(result.sleeps) == attempts - 1
    assert result.errors == [result.error]
    assert_safe(result.error)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("consumer", ["hook", "auth"])
@pytest.mark.parametrize("malformed", ["gzip", "json"])
async def test_hook_decode_failure_keeps_safe_evidence(monkeypatch, async_mode, consumer, malformed):
    result = await exercise(monkeypatch, async_mode=async_mode, malformed=malformed,
                            hook=consumer == "hook", auth=consumer == "auth")
    assert_terminal(result)
    assert isinstance(result.error, httpx.DecodingError if malformed == "gzip" else ValueError)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
async def test_capture_keeps_caller_hook_order_and_http_client_lifecycle(async_mode):
    order, responses = [], []

    def handler(request):
        response = httpx.Response(200, headers=HEADERS, json={"choices": [], "id": "fixture",
            "model": "fixture", "object": "chat.completion", "created": 0})
        responses.append(response)
        return response

    def first(response):
        order.append("first")
        response.headers["x-agentcc-request-id"] = "mutated-by-hook"

    def last(response):
        order.append("last")

    async def afirst(response):
        first(response)

    async def alast(response):
        last(response)

    http_cls = httpx.AsyncClient if async_mode else httpx.Client
    http = http_cls(transport=httpx.MockTransport(handler),
                    event_hooks={"response": [afirst, alast] if async_mode else [first, last]})
    hooks = http.event_hooks
    response_hooks = hooks["response"]
    kwargs = dict(api_key=SECRET, base_url="https://gateway.test", http_client=http)
    try:
        if async_mode:
            async with gw.AsyncAgentCC(**kwargs) as client:
                result = await client.chat.completions.create(model="fixture", messages=[])
            with pytest.raises(RuntimeError):
                await http.__aenter__()
        else:
            with gw.AgentCC(**kwargs) as client:
                result = client.chat.completions.create(model="fixture", messages=[])
            with pytest.raises(RuntimeError):
                http.__enter__()
        assert result.agentcc.gateway_request_id == UID
        assert order == ["first", "last"]
        assert http.event_hooks is hooks and hooks["response"] is response_hooks
        assert not http.is_closed
    finally:
        if async_mode:
            await http.aclose()
        else:
            http.close()


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
async def test_partial_sse_failure_stays_terminal_and_safe(monkeypatch, async_mode):
    errors, attempts = [], []

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            yield b'data: {"id":"fixture","object":"chat.completion.chunk","created":0,"model":"fixture","choices":[]}\n\n'
            raise httpx.ReadTimeout(SECRET, request=attempts[-1])
        async def __aiter__(self):
            for part in self:
                yield part
        def close(self):
            raise httpx.ReadError(SECRET, request=attempts[-1])
        async def aclose(self):
            self.close()

    def handler(request):
        attempts.append(request)
        return httpx.Response(200, headers={**HEADERS, "content-type": "text/event-stream"}, stream=Body())

    kwargs = dict(api_key=SECRET, base_url="https://gateway.test", max_retries=5,
                  callbacks=[SimpleNamespace(on_error=lambda request, error: errors.append(error))])
    if async_mode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            async with gw.AsyncAgentCC(http_client=http, **kwargs) as client:
                stream = await client.chat.completions.create(model="fixture", messages=[], stream=True)
                await stream.__anext__()
                with pytest.raises(gw.StreamError) as caught:
                    await stream.__anext__()
    else:
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            with gw.AgentCC(http_client=http, **kwargs) as client:
                stream = client.chat.completions.create(model="fixture", messages=[], stream=True)
                next(stream)
                with pytest.raises(gw.StreamError) as caught:
                    next(stream)
    assert len(attempts) == 1
    assert errors == [caught.value]
    assert caught.value.gateway_request_id == UID
    assert "check whether" in str(caught.value)
    assert_safe(caught.value)


@pytest.mark.parametrize("mode", ["stream", "responses"])
async def test_async_construction_cleanup_is_best_effort(monkeypatch, mode):
    result = await exercise(monkeypatch, async_mode=True, mode=mode,
                            constructor_failure=True, close_failure=True)
    assert_terminal(result)
    assert isinstance(result.error, gw.APITimeoutError)
