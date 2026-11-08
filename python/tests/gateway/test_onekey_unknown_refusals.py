"""Unknown codes fail closed; absent codes retry only when not dispatched.

Run the same wire bodies through JSON, binary and stream-open paths, with both
flat and per-status retry limits. All traffic uses httpx.MockTransport.
"""

from types import SimpleNamespace

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._retry_policy import RetryPolicy
from fi.gateway._transport import _async as async_transport
from fi.gateway._transport import _sync as sync_transport


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def sleeps(monkeypatch):
    recorded = []

    async def asleep(delay):
        recorded.append(delay)

    monkeypatch.setattr(sync_transport, "time", SimpleNamespace(sleep=recorded.append))
    monkeypatch.setattr(async_transport, "anyio", SimpleNamespace(sleep=asleep))
    return recorded


def settings(policy):
    return {
        "api_key": "unit-placeholder",
        "base_url": "https://gateway.example.test",
        "max_retries": 5,
        "retry_policy": RetryPolicy(
            RateLimitErrorRetries=5, ServiceUnavailableRetries=5,
            InternalServerErrorRetries=5, BadGatewayRetries=5, GatewayTimeoutRetries=5,
        ) if policy else None,
    }


def response(status, wire, *, dispatched=None):
    headers = {"retry-after": "0", "x-agentcc-request-id": "req-onekey-parity"}
    if dispatched is not None:
        headers["x-agentcc-dispatched"] = dispatched
    if isinstance(wire, bytes):
        return httpx.Response(status, content=wire, headers=headers)
    return httpx.Response(status, json=wire, headers=headers)


def invoke(client, path):
    if path == "binary":
        return client.audio.speech.create(model="test-model", input="hi", voice="test")
    return client.chat.completions.create(
        model="test-model", messages=[], stream=path == "stream",
    )


UNKNOWN = [
    (429, "new_refusal"), (503, "new_refusal"),
    (503, "rate_limit_exceeded"), (429, "managed_billing_unavailable"),
    (429, "managed_credits_insufficient"), (503, "budget_exceeded"),
    (400, "new_refusal"), (401, "key_scope_denied"),
    (402, "new_refusal"), (403, "invalid_api_key"),
    (500, "new_refusal"), (502, "new_refusal"), (504, "new_refusal"),
    (429, ""), (503, 0), (429, []), (503, {}),
]
STATUS_CLASSES = {
    400: gw.BadRequestError, 401: gw.AuthenticationError, 402: gw.APIStatusError,
    403: gw.PermissionDeniedError, 429: gw.RateLimitError,
    500: gw.InternalServerError, 502: gw.BadGatewayError,
    503: gw.ServiceUnavailableError, 504: gw.GatewayTimeoutError,
}


@pytest.mark.parametrize("status,code", UNKNOWN)
@pytest.mark.parametrize("policy", [False, True], ids=["max-retries-5", "policy-5"])
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
def test_unknown_or_mismatched_code_is_sent_once_sync(status, code, policy, path, sleeps):
    calls = []

    def handle(request):
        calls.append(request)
        return response(status, {"error": {"code": code, "type": "rate_limit_error"}})

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        with gw.AgentCC(http_client=http, **settings(policy)) as client:
            with pytest.raises(gw.APIStatusError) as caught:
                invoke(client, path)
    assert len(calls) == 1
    assert sleeps == []
    assert type(caught.value) is STATUS_CLASSES[status]
    assert caught.value.code == code
    assert getattr(caught.value, "category", None) == "generic"
    assert getattr(caught.value, "remedy", "missing") is None


@pytest.mark.parametrize("status,code", UNKNOWN)
@pytest.mark.parametrize("policy", [False, True], ids=["max-retries-5", "policy-5"])
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
@pytest.mark.anyio
async def test_unknown_or_mismatched_code_is_sent_once_async(status, code, policy, path, sleeps):
    calls = []

    def handle(request):
        calls.append(request)
        return response(status, {"error": {"code": code, "type": "rate_limit_error"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        async with gw.AsyncAgentCC(http_client=http, **settings(policy)) as client:
            with pytest.raises(gw.APIStatusError) as caught:
                await invoke(client, path)
    assert len(calls) == 1
    assert sleeps == []
    assert type(caught.value) is STATUS_CLASSES[status]
    assert caught.value.code == code
    assert getattr(caught.value, "category", None) == "generic"
    assert getattr(caught.value, "remedy", "missing") is None


ABSENT_CODE = [
    pytest.param({"error": {"code": None}}, id="null-code"),
    pytest.param({"error": {"message": "unavailable"}}, id="missing-code"),
    pytest.param(b"upstream unavailable", id="non-json"),
    pytest.param({"message": "unavailable"}, id="non-gateway-json"),
    pytest.param({"error": None}, id="null-error"),
    pytest.param(["unavailable"], id="json-list"),
]


@pytest.mark.parametrize("wire", ABSENT_CODE)
@pytest.mark.parametrize("status", [429, 503])
@pytest.mark.parametrize("policy", [False, True], ids=["max-retries-5", "policy-5"])
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
def test_no_code_preserves_status_retry_sync(wire, status, policy, path, sleeps):
    calls = []

    def handle(request):
        calls.append(request)
        # A gateway request ID now requires explicit evidence of no dispatch.
        return response(status, wire, dispatched="false")

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        with gw.AgentCC(http_client=http, **settings(policy)) as client:
            with pytest.raises(STATUS_CLASSES[status]):
                invoke(client, path)
    attempts = 1 if path == "stream" else 6
    assert len(calls) == attempts
    assert sleeps == [0.0] * (attempts - 1)


@pytest.mark.parametrize("wire", ABSENT_CODE)
@pytest.mark.parametrize("status", [429, 503])
@pytest.mark.parametrize("policy", [False, True], ids=["max-retries-5", "policy-5"])
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
@pytest.mark.anyio
async def test_no_code_preserves_status_retry_async(wire, status, policy, path, sleeps):
    calls = []

    def handle(request):
        calls.append(request)
        # A gateway request ID now requires explicit evidence of no dispatch.
        return response(status, wire, dispatched="false")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        async with gw.AsyncAgentCC(http_client=http, **settings(policy)) as client:
            with pytest.raises(STATUS_CLASSES[status]):
                await invoke(client, path)
    attempts = 1 if path == "stream" else 6
    assert len(calls) == attempts
    assert sleeps == [0.0] * (attempts - 1)
