"""Offline controls for auth exchanges and caller-owned HTTPX client state."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._transport import _async, _sync
from test_terminal_outcomes import assert_safe

UID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
HEADERS = {"x-agentcc-request-id": UID, "x-agentcc-dispatched": "false"}
GOOD_CHAT = {"id": "fixture", "object": "chat.completion", "created": 0,
             "model": "fixture", "choices": []}


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    monkeypatch.setattr(_sync.time, "sleep", lambda _: None)

    async def no_sleep(_):
        pass
    monkeypatch.setattr(_async.anyio, "sleep", no_sleep)


async def auth_exchange(async_mode, policy, challenge, error_cls, fresh_request):
    requests, responses, errors, retries, hooks = [], [], [], [], []

    class ExchangeAuth(httpx.Auth):
        def auth_flow(self, request):
            response = yield request
            if response.status_code == challenge:
                if fresh_request:
                    request = httpx.Request(request.method, request.url,
                                            headers=request.headers, content=request.content)
                yield request

    def handler(request):
        requests.append(request)
        if len(requests) % 2:
            response = httpx.Response(challenge, headers=HEADERS,
                                      json={"error": {"message": "fixture auth challenge"}})
            responses.append(response)
            return response
        assert request.content
        raise error_cls("fixture follow-up failure", request=request)

    def first(response):
        hooks.append("first")

    def last(response):
        hooks.append("last")

    async def afirst(response):
        first(response)

    async def alast(response):
        last(response)

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(handler), auth=ExchangeAuth(), trust_env=False,
        event_hooks={"response": [afirst, alast] if async_mode else [first, last]},
    )
    original_hooks = http.event_hooks
    original_lists = dict(original_hooks)
    kwargs = dict(api_key="synthetic-credential-only", base_url="https://gateway.test",
                  http_client=http, max_retries=2,
                  callbacks=[SimpleNamespace(on_error=lambda request, error: errors.append(error),
                                             on_retry=lambda *args: retries.append(args))])
    if policy:
        kwargs["retry_policy"] = gw.RetryPolicy(TimeoutRetries=3, ConnectionErrorRetries=3,
                                               ServiceUnavailableRetries=3)
    caught = None
    try:
        if async_mode:
            async with gw.AsyncAgentCC(**kwargs) as client:
                await client.chat.completions.create(model="fixture", messages=[])
        else:
            with gw.AgentCC(**kwargs) as client:
                client.chat.completions.create(model="fixture", messages=[])
    except Exception as exc:
        caught = exc
    finally:
        assert http.event_hooks is original_hooks
        assert all(http.event_hooks[name] is values for name, values in original_lists.items())
        assert not http.is_closed
        if async_mode:
            await http.aclose()
        else:
            http.close()
    return SimpleNamespace(error=caught, requests=requests, responses=responses,
                           errors=errors, retries=retries, hooks=hooks)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("challenge", [401, 503])
@pytest.mark.parametrize("fresh_request", [False, True], ids=["reused-request", "new-request"])
@pytest.mark.parametrize("error_cls", [httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError])
async def test_auth_follow_up_never_inherits_earlier_retry_permission(
    async_mode, policy, challenge, fresh_request, error_cls,
):
    result = await auth_exchange(async_mode, policy, challenge, error_cls, fresh_request)
    assert isinstance(result.error, gw.APIConnectionError)
    assert len(result.requests) == 2
    assert result.retries == []
    assert result.errors == [result.error]
    assert result.error.dispatched == "unknown"
    assert result.error.gateway_request_id is None
    assert result.error.client_request_id is None
    assert getattr(result.error, "_status_error", None) is None
    assert "check whether" in str(result.error).lower()
    assert result.hooks == ["first", "last"]
    assert all(response.is_closed for response in result.responses)
    assert_safe(result.error)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("policy", [False, True], ids=["default", "per-error"])
@pytest.mark.parametrize("error_cls", [httpx.ConnectTimeout, httpx.PoolTimeout, httpx.ConnectError])
async def test_auth_follow_up_pre_send_failures_keep_their_own_retry_budget(async_mode, policy, error_cls):
    result = await auth_exchange(async_mode, policy, 401, error_cls, True)
    attempts = 4 if policy else 3
    assert len(result.requests) == attempts * 2
    assert len(result.retries) == attempts - 1
    assert result.errors == [result.error]
    assert result.error.gateway_request_id is None
    assert getattr(result.error, "_status_error", None) is None
    assert_safe(result.error)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
async def test_supplied_client_enforces_its_own_send_budget(async_mode):
    attempts = []

    def handler(request):
        attempts.append(request)
        return httpx.Response(200, json=GOOD_CHAT)

    if async_mode:
        class Limited(httpx.AsyncClient):
            async def send(self, *args, **kwargs):
                self.send_calls += 1
                if self.remaining <= 0:
                    raise RuntimeError("fixture send budget exhausted")
                self.remaining -= 1
                return await super().send(*args, **kwargs)
    else:
        class Limited(httpx.Client):
            def send(self, *args, **kwargs):
                self.send_calls += 1
                if self.remaining <= 0:
                    raise RuntimeError("fixture send budget exhausted")
                self.remaining -= 1
                return super().send(*args, **kwargs)

    http = Limited(transport=httpx.MockTransport(handler), trust_env=False)
    http.send_calls, http.remaining = 0, 1
    original_hooks = http.event_hooks
    client = (gw.AsyncAgentCC if async_mode else gw.AgentCC)(
        api_key="synthetic-credential-only", base_url="https://gateway.test", http_client=http,
    )
    try:
        if async_mode:
            await client.chat.completions.create(model="fixture", messages=[])
            with pytest.raises(RuntimeError, match="send budget exhausted"):
                await client.chat.completions.create(model="fixture", messages=[])
        else:
            client.chat.completions.create(model="fixture", messages=[])
            with pytest.raises(RuntimeError, match="send budget exhausted"):
                client.chat.completions.create(model="fixture", messages=[])
        assert len(attempts) == 1
        assert http.send_calls == 2
        assert http.remaining == 0
        assert http.event_hooks is original_hooks
    finally:
        if async_mode:
            await client.aclose()
            assert not http.is_closed
            await http.aclose()
        else:
            client.close()
            assert not http.is_closed
            http.close()


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
async def test_overlapping_requests_keep_independent_evidence(async_mode):
    barrier = Barrier(2, timeout=5)
    arrived = asyncio.Event()
    count = 0

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            raise httpx.ReadTimeout("fixture body failure")
            yield b""  # pragma: no cover

        async def __aiter__(self):
            for chunk in self:
                yield chunk

    def response(request):
        return httpx.Response(200, headers={**HEADERS, "x-agentcc-dispatched": "true",
                              "x-agentcc-client-request-id": request.headers["x-fixture-request"]},
                              stream=Body())

    def handler(request):
        barrier.wait()
        return response(request)

    async def ahandler(request):
        nonlocal count
        count += 1
        if count == 2:
            arrived.set()
        await asyncio.wait_for(arrived.wait(), timeout=5)
        return response(request)

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(ahandler if async_mode else handler), trust_env=False,
    )
    client = (gw.AsyncAgentCC if async_mode else gw.AgentCC)(
        api_key="synthetic-credential-only", base_url="https://gateway.test", http_client=http,
    )
    # Distinct headers distinguish captures on the same pooled client.
    async def acall(name):
        with pytest.raises(gw.APITimeoutError) as caught:
            await client.with_options(extra_headers={"x-fixture-request": name}).chat.completions.create(
                model="fixture", messages=[],
            )
        return caught.value

    def call(name):
        with pytest.raises(gw.APITimeoutError) as caught:
            client.with_options(extra_headers={"x-fixture-request": name}).chat.completions.create(
                model="fixture", messages=[],
            )
        return caught.value

    try:
        if async_mode:
            errors = await asyncio.gather(acall("first"), acall("second"))
        else:
            with ThreadPoolExecutor(max_workers=2) as executor:
                errors = list(executor.map(call, ["first", "second"]))
        assert len({id(error.gateway_evidence) for error in errors}) == 2
        assert all(error.dispatched is True for error in errors)
        assert [error.client_request_id for error in errors] == ["first", "second"]
        for error in errors:
            assert_safe(error)
    finally:
        if async_mode:
            await client.aclose()
            await http.aclose()
        else:
            client.close()
            http.close()
