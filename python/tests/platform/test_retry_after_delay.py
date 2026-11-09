"""Retry-After is a server minimum, not a capped exponential backoff."""

from __future__ import annotations

import asyncio
from email.utils import formatdate

import httpx
import pytest

from fi import _http
from fi.platform import AsyncClient, Client
from fi.platform import _transport as platform_transport


class Clock:
    def __init__(self, header):
        self.elapsed = 0.0
        self.header = header
        self.attempts = []
        self.sleeps = []

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.elapsed += seconds

    async def asleep(self, seconds):
        self.sleep(seconds)

    def handle(self, request):
        self.attempts.append(self.elapsed)
        if self.elapsed < 120:
            return httpx.Response(429, headers={"Retry-After": self.header}, json={"detail": "wait"})
        return httpx.Response(200, json={"ok": True})


@pytest.mark.parametrize("family", ["facade", "generated-client", "platform"])
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("header_kind", ["seconds", "http-date"])
def test_server_window_is_not_shortened(monkeypatch, family, asynchronous, header_kind):
    now = 1_700_000_000
    header = "120" if header_kind == "seconds" else formatdate(now + 120, usegmt=True)
    clock = Clock(header)
    monkeypatch.setattr(_http.time, "time", lambda: now + clock.elapsed)
    mock = httpx.MockTransport(clock.handle)
    if family == "platform":
        monkeypatch.setattr(platform_transport.time, "sleep", clock.sleep)
        monkeypatch.setattr(platform_transport.asyncio, "sleep", clock.asleep)
        transport = mock
    elif family == "generated-client":
        transport = _http.ClientRetryingTransport(wrapped=mock, wrapped_async=mock)
        transport._sync_transport()._sleep = clock.sleep
        transport._async_transport()._sleep = clock.asleep
    else:
        transport = (
            _http.AsyncRetryingTransport(mock, sleep=clock.asleep)
            if asynchronous else _http.RetryingTransport(mock, sleep=clock.sleep)
        )

    async def run_async():
        async with httpx.AsyncClient(transport=transport) as http:
            if family == "platform":
                async with AsyncClient(
                    api_key="test-key", secret_key="test-secret",
                    base_url="https://api.example.test", http_client=http,
                ) as client:
                    return await client.request("GET", "/retry-test")
            response = await http.get("https://api.example.test/retry-test")
            assert response.status_code == 200
            return response.json()

    def run_sync():
        with httpx.Client(transport=transport) as http:
            if family == "platform":
                with Client(
                    api_key="test-key", secret_key="test-secret",
                    base_url="https://api.example.test", http_client=http,
                ) as client:
                    return client.request("GET", "/retry-test")
            response = http.get("https://api.example.test/retry-test")
            assert response.status_code == 200
            return response.json()

    assert (asyncio.run(run_async()) if asynchronous else run_sync()) == {"ok": True}
    assert clock.attempts == [0.0, 120.0]
    assert clock.sleeps == [120.0]


@pytest.mark.parametrize("value", ["0", "2", "30", "31", "120", "120.5"])
def test_numeric_server_hint_is_used_without_jitter_or_cap(value):
    response = httpx.Response(429, headers={"Retry-After": value})
    assert _http.backoff_s(10, response, 0.5) == float(value)
    assert platform_transport._backoff(10, response) == float(value)


@pytest.mark.parametrize("value", [None, "", "not-a-delay", "nan", "inf", "-inf", "1e999"])
def test_invalid_hint_uses_the_existing_bounded_backoff(monkeypatch, value):
    response = httpx.Response(429, headers={} if value is None else {"Retry-After": value})
    monkeypatch.setattr(platform_transport.random, "random", lambda: 0.5)
    assert _http.backoff_s(0, response, 0.5) == 0.5
    assert _http.backoff_s(10, response, 0.5) == 30.0
    assert platform_transport._backoff(0, response) == 0.5
    assert platform_transport._backoff(10, response) == 8.0


def test_negative_and_expired_hints_do_not_sleep_a_negative_duration(monkeypatch):
    monkeypatch.setattr(_http.time, "time", lambda: 1_700_000_000)
    for value in ["-1", formatdate(1_699_999_999, usegmt=True)]:
        response = httpx.Response(429, headers={"Retry-After": value})
        assert _http.backoff_s(0, response, 0.5) == 0
        assert platform_transport._backoff(0, response) == 0


def test_no_response_uses_the_existing_bounded_backoff(monkeypatch):
    monkeypatch.setattr(platform_transport.random, "random", lambda: 0.5)
    assert _http.backoff_s(10, None, 0.5) == 30.0
    assert platform_transport._backoff(10, None) == 8.0
