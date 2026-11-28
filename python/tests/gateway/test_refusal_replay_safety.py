"""Offline request-scoped ceilings and strict Retry-After admission."""
from types import SimpleNamespace

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._retry_policy import RetryPolicy
from fi.gateway._transport import _async, _sync

IN_FLIGHT = {"limit_source": "agentcc_in_flight", "remedy_hint": "retry"}


@pytest.fixture
def sleeps(monkeypatch):
    delays = []

    async def asleep(delay):
        delays.append(delay)

    monkeypatch.setattr(_sync, "time", SimpleNamespace(sleep=delays.append))
    monkeypatch.setattr(_async, "anyio", SimpleNamespace(sleep=asleep))
    return delays


def refusal(status, code, metadata=None, after="2"):
    return httpx.Response(status, json={"error": {
        "code": code, "message": "refused", "metadata": metadata,
    }}, headers={} if after is None else {"Retry-After": after})


async def invoke(async_mode, raw, handler, options):
    transport = httpx.MockTransport(handler)
    common = dict(api_key="fixture-only", base_url="https://gateway.test", **options)
    if async_mode:
        async with httpx.AsyncClient(transport=transport) as http:
            async with gw.AsyncAgentCC(http_client=http, **common) as client:
                if raw:
                    return await client.audio.speech.create(model="fixture", input="hi", voice="alloy")
                return await client.chat.completions.create(model="fixture", messages=[])
    with httpx.Client(transport=transport) as http:
        with gw.AgentCC(http_client=http, **common) as client:
            if raw:
                return client.audio.speech.create(model="fixture", input="hi", voice="alloy")
            return client.chat.completions.create(model="fixture", messages=[])


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("raw", [False, True], ids=["json", "binary"])
@pytest.mark.parametrize("policy", [False, True], ids=["flat-budget", "status-budget"])
@pytest.mark.parametrize("second", ["billing", "rate", "connection", "timeout"])
async def test_in_flight_ceiling_survives_changed_error(async_mode, raw, policy, second, sleeps):
    attempts = []

    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            return refusal(402, "managed_credits_insufficient", IN_FLIGHT)
        if second == "connection":
            raise httpx.ConnectError("offline fixture", request=request)
        if second == "timeout":
            raise httpx.ReadTimeout("offline fixture", request=request)
        return refusal(503 if second == "billing" else 429,
                       "managed_billing_unavailable" if second == "billing" else "rate_limit_exceeded")

    options = {"max_retries": 5}
    if policy:
        options["retry_policy"] = RetryPolicy(
            RateLimitErrorRetries=5, ServiceUnavailableRetries=5,
            ConnectionErrorRetries=5, TimeoutRetries=5,
        )
    with pytest.raises((gw.APIStatusError, gw.APIConnectionError)):
        await invoke(async_mode, raw, handler, options)
    assert len(attempts) == 2
    assert sleeps == [2.0]


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("raw", [False, True], ids=["json", "binary"])
@pytest.mark.parametrize("after", [".5", "+2", "2.0", "2e0", "1_0", "-2", "0", "NaN", "inf", "2, 2", "\t2\n", "9" * 400, None])
async def test_malformed_header_never_authorizes_in_flight_replay(async_mode, raw, after, sleeps):
    attempts = []

    def handler(request):
        attempts.append(request)
        return refusal(402, "managed_credits_insufficient", IN_FLIGHT, after)

    with pytest.raises(gw.InsufficientCreditsError):
        await invoke(async_mode, raw, handler, {"max_retries": 5})
    assert len(attempts) == 1
    assert sleeps == []


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("raw", [False, True], ids=["json", "binary"])
@pytest.mark.parametrize("status,code", [
    (429, "rate_limit_exceeded"), (429, "token_rate_limit_exceeded"),
    (503, "managed_billing_unavailable"), (503, "budget_state_unavailable"),
    (503, "key_list_not_loaded"),
])
async def test_long_contract_retry_after_is_not_shortened(async_mode, raw, status, code, sleeps):
    attempts = []

    def handler(request):
        attempts.append(request)
        return refusal(status, code, after="120")

    with pytest.raises(gw.APIStatusError):
        await invoke(async_mode, raw, handler, {"max_retries": 1})
    assert len(attempts) == 2
    assert sleeps == [120.0]
