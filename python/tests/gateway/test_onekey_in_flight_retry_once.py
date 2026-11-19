"""An in-flight credit refusal is retried at most once (gateway contract), within lower configured limits.

A 402 ``managed_credits_insufficient`` refusal whose ``error.metadata`` has
``limit_source == "agentcc_in_flight"`` and ``remedy_hint == "retry"`` is retried once
after ``Retry-After``; generous ``max_retries`` / ``RetryPolicy`` / ``with_options``
never add more attempts, and ``max_retries=0`` / a zero policy still opt out.
Offline (respx); sleeps are recorded, not slept.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
import respx

import fi.gateway as gw
from fi.gateway._retry_policy import RetryPolicy
from fi.gateway._transport import _async as async_transport
from fi.gateway._transport import _sync as sync_transport

BASE = "https://gateway.test"
URL = f"{BASE}/v1/chat/completions"
KEY = "sk-agentcc-TEST"
MODEL = "openai/gpt-4o-mini"
MESSAGES = [{"role": "user", "content": "Hi"}]
IN_FLIGHT = {"limit_source": "agentcc_in_flight", "remedy_hint": "retry", "required_usd": 0.02}


def _refusal() -> httpx.Response:
    error = {"message": "refused", "type": "payment_required", "code": "managed_credits_insufficient",
             "metadata": IN_FLIGHT}
    return httpx.Response(402, json={"error": error},
                          headers={"retry-after": "2", "x-agentcc-request-id": "req-refused"})


def _always(response: httpx.Response) -> Any:
    def reply(request: httpx.Request) -> httpx.Response:
        return httpx.Response(response.status_code, headers=response.headers, content=response.content)

    return reply


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    slept: list[float] = []

    async def asleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr(sync_transport, "time", SimpleNamespace(sleep=slept.append))
    monkeypatch.setattr(async_transport, "anyio", SimpleNamespace(sleep=asleep))
    return slept


@pytest.mark.parametrize(
    ("options", "attempts"),
    [
        ({"max_retries": 0}, 1),
        ({"max_retries": 1}, 2),
        ({"max_retries": 5}, 2),
        ({"retry_policy": RetryPolicy(RateLimitErrorRetries=1)}, 2),
        ({"retry_policy": RetryPolicy(RateLimitErrorRetries=5)}, 2),
        ({"retry_policy": RetryPolicy(RateLimitErrorRetries=0)}, 1),
    ],
    ids=["max_retries=0", "max_retries=1", "max_retries=5", "policy-1", "policy-5", "policy-0"],
)
def test_in_flight_retries_at_most_once_within_the_configured_retries(options, attempts, sleeps) -> None:
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_always(_refusal()))
        with gw.AgentCC(api_key=KEY, base_url=BASE, **options) as client:
            with pytest.raises(gw.InsufficientCreditsError):
                client.chat.completions.create(model=MODEL, messages=MESSAGES)
    assert route.call_count == attempts


@pytest.mark.anyio
async def test_in_flight_retries_at_most_once_async_with_a_generous_policy(sleeps) -> None:
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_always(_refusal()))
        policy = RetryPolicy(RateLimitErrorRetries=5)
        async with gw.AsyncAgentCC(api_key=KEY, base_url=BASE, retry_policy=policy) as client:
            with pytest.raises(gw.InsufficientCreditsError):
                await client.chat.completions.create(model=MODEL, messages=MESSAGES)
    assert route.call_count == 2 and sleeps == [2.0]


def test_in_flight_retries_at_most_once_through_with_options(sleeps) -> None:
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_always(_refusal()))
        with gw.AgentCC(api_key=KEY, base_url=BASE) as client:
            generous = client.with_options(max_retries=5)
            with pytest.raises(gw.InsufficientCreditsError):
                generous.chat.completions.create(model=MODEL, messages=MESSAGES)
    assert route.call_count == 2 and sleeps == [2.0]
