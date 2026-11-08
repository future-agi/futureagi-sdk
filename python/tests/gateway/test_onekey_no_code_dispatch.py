"""No-code HTTP refusals require header evidence before status-based replay.

MockTransport only; generous retry limits and recorded sleeps exercise both
transports. Stream opening has no retry loop and must stay single-attempt.
"""
from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from fi.gateway import APIConnectionError, APIStatusError, APITimeoutError, RetryPolicy
from fi.gateway._transport import _async, _sync
from fi.gateway._transport._base import RequestOptions

REMEDY = (
    "The gateway did not confirm whether the request was applied; "
    "check whether it was applied before sending it again."
)
PATHS = ["sync-json", "async-json", "sync-raw", "async-raw", "sync-stream", "async-stream"]
HEADERS = [
    pytest.param({}, False, id="no-request-id"),
    pytest.param({"X-AgentCC-Request-ID": "fixture", "X-AgentCC-Dispatched": "false"}, False,
                 id="not-dispatched-mixed-case"),
    pytest.param({"x-agentcc-request-id": "fixture", "x-agentcc-dispatched": "true"}, True,
                 id="dispatched"),
    pytest.param({"x-agentcc-request-id": "fixture"}, True, id="unknown-dispatch"),
    pytest.param({"x-agentcc-request-id": "fixture", "x-agentcc-dispatched": "unparseable"}, True,
                 id="invalid-dispatch"),
]
BODIES = [
    pytest.param({"error": {"message": "refused"}}, id="missing-code"),
    pytest.param({"error": {"code": None}}, id="null-code"),
    pytest.param(b"<html>unavailable</html>", id="non-json"),
    pytest.param({"code": "provider_busy", "message": "not-a-flat-r1-code"}, id="unrecognized-flat"),
]


@pytest.fixture
def sleeps(monkeypatch):
    recorded = []

    async def asleep(delay):
        recorded.append(delay)

    monkeypatch.setattr(_sync, "time", SimpleNamespace(sleep=recorded.append))
    monkeypatch.setattr(_async, "anyio", SimpleNamespace(sleep=asleep))
    return recorded


def settings(kind, retries=5):
    if kind == "max":
        return {"max_retries": retries}
    return {"max_retries": retries, "retry_policy": RetryPolicy(**{
        name: retries for name in RetryPolicy.__dataclass_fields__
    })}


async def invoke(path, handler, config, request_retries=None):
    options = RequestOptions(method="POST", url="/v1/chat/completions",
                             body={"model": "fixture-model"}, max_retries=request_retries)
    kwargs = {"api_key": "fixture-only", "base_url": "https://gateway.test", **config}
    if path.startswith("async-"):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = _async.AsyncBaseClient(http_client=http, **kwargs)
            if path.endswith("json"):
                return await client._request_with_retry(options, dict)
            if path.endswith("raw"):
                return await client._request_raw_with_retry(options)
            return await client._open_stream(options, None, dict)
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        client = _sync.SyncBaseClient(http_client=http, **kwargs)
        if path.endswith("json"):
            return client._request_with_retry(options, dict)
        if path.endswith("raw"):
            return client._request_raw_with_retry(options)
        return client._open_stream(options, None, dict)


async def refusal(path, status, headers, body, config, request_retries=None):
    calls = []

    def handler(request):
        calls.append(request)
        payload = {"content": body} if isinstance(body, bytes) else {"json": body}
        return httpx.Response(status, headers={"retry-after": "2", **headers}, **payload)

    with pytest.raises(APIStatusError) as caught:
        await invoke(path, handler, config, request_retries)
    return caught.value, len(calls)


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("status", [429, 503, 504])
@pytest.mark.parametrize("headers,terminal", HEADERS)
@pytest.mark.parametrize("body", BODIES)
@pytest.mark.parametrize("kind", ["max", "policy"])
async def test_no_code_dispatch_matrix(path, status, headers, terminal, body, kind, sleeps):
    exc, attempts = await refusal(path, status, headers, body, settings(kind))
    assert attempts == (1 if terminal or path.endswith("stream") else 6)
    assert exc.code is None
    assert exc.category == "generic"
    assert exc.remedy == (REMEDY if terminal else None)
    assert sleeps == [2.0] * (attempts - 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("status", [408, 500, 502])
@pytest.mark.parametrize("headers,terminal", HEADERS)
async def test_other_retryable_statuses(path, status, headers, terminal, sleeps):
    exc, attempts = await refusal(path, status, headers, {}, settings("max"))
    assert attempts == (1 if terminal or path.endswith("stream") else 6)
    assert exc.category == "generic"
    assert exc.remedy == (REMEDY if terminal else None)
    assert len(sleeps) == attempts - 1


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("dispatched,body_dispatched,terminal", [
    ("true", False, True), ("false", True, False), (None, False, True),
])
async def test_headers_override_conflicting_body(path, dispatched, body_dispatched, terminal, sleeps):
    headers = {"x-agentcc-request-id": "fixture"}
    if dispatched is not None:
        headers["x-agentcc-dispatched"] = dispatched
    body = {"dispatched": body_dispatched, "error": {"code": None,
            "dispatched": body_dispatched, "metadata": {"dispatched": body_dispatched}}}
    exc, attempts = await refusal(path, 504, headers, body, settings("policy"))
    assert attempts == (1 if terminal or path.endswith("stream") else 6)
    assert exc.category == "generic"
    assert exc.remedy == (REMEDY if terminal else None)


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("headers", [
    {"x-agentcc-dispatched": "true"},
    {"x-agentcc-request-id": "", "x-agentcc-dispatched": ""},
    {"x-agentcc-request-id": "fixture", "x-agentcc-dispatched": "false, true"},
    {"x-agentcc-request-id": "fixture", "x-agentcc-dispatched": "0"},
])
async def test_header_presence_and_unparseable_values(path, headers, sleeps):
    terminal = "x-agentcc-request-id" in headers
    exc, attempts = await refusal(path, 503, headers, [], settings("max"))
    # Positive dispatch forbids replay even when the correlation header is absent.
    assert attempts == (1 if terminal or headers.get("x-agentcc-dispatched") == "true" or path.endswith("stream") else 6)
    assert exc.remedy == (REMEDY if terminal else None)


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("headers", [{}, {"x-agentcc-request-id": "fixture", "x-agentcc-dispatched": "false"}])
@pytest.mark.parametrize("kind,limit,request_limit", [("max", 0, None), ("max", 5, 0), ("policy", 0, None)])
async def test_safe_fallback_honors_disabled_retries(path, headers, kind, limit, request_limit, sleeps):
    exc, attempts = await refusal(path, 503, headers, {}, settings(kind, limit), request_limit)
    assert attempts == 1 and sleeps == []
    assert exc.remedy is None


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("headers,unused", HEADERS)
@pytest.mark.parametrize("status,code,category,retry", [
    (429, "rate_limit_exceeded", "rate_limit", True),
    (503, "managed_billing_unavailable", "billing_unavailable", True),
    (504, "gateway_timeout", "generic", False),
    (429, "budget_exceeded", "budget_limit", False),
    (503, "future_unknown_code", "generic", False),
])
async def test_coded_refusals_keep_contract_rules(path, headers, unused, status, code, category, retry, sleeps):
    exc, attempts = await refusal(path, status, headers, {"error": {"code": code}}, settings("policy"))
    assert attempts == (6 if retry and not path.endswith("stream") else 1)
    assert exc.code == code and exc.category == category
    assert exc.remedy != REMEDY


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("error,expected", [(httpx.ConnectError, APIConnectionError),
                                           (httpx.ReadTimeout, APITimeoutError)])
async def test_no_http_response_retains_retry(path, error, expected, sleeps):
    calls = []

    def handler(request):
        calls.append(request)
        raise error("offline simulated failure", request=request)

    with pytest.raises(expected):
        await invoke(path, handler, settings("policy"))
    # ReadTimeout may follow a completed send: only provably pre-send failures can replay.
    assert len(calls) == (1 if path.endswith("stream") or error is httpx.ReadTimeout else 6)
    assert len(sleeps) == len(calls) - 1
