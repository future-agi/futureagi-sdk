"""Management envelopes use the sent request's header credentials, not refreshed settings."""
import asyncio
import os

import httpx
import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.errors import BadRequestError


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("status", [200, 400])
@pytest.mark.parametrize("source", ["argument", "environment"])
@pytest.mark.parametrize("raw", [False, True])
@pytest.mark.parametrize("copy", [False, True])
def test_error_envelopes_scrub_captured_headers(monkeypatch, asynchronous, status, source, raw, copy):
    token = "proxy-identity-fixture-value"
    value = "Bearer " + token
    refreshed = "refreshed-fixture-value"
    extra = {"Proxy-Authorization": value, "X-Diagnostic": "diagnostic"}
    monkeypatch.setenv("FI_EXTRA_HEADERS", "")
    if source == "environment":
        monkeypatch.setenv("FI_EXTRA_HEADERS", f"Proxy-Authorization={value};X-Diagnostic=diagnostic")
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls(api_key="api-fixture", secret_key="secret-fixture", base_url="http://localhost:9012",
                 retries=0, extra_headers=extra if source == "argument" else None)
    calls = []

    def handler(request):
        calls.append(request)
        assert request.headers["proxy-authorization"] == value
        assert request.headers["x-diagnostic"] == "diagnostic"
        # The next request may use new credentials. This response belongs to the old ones.
        monkeypatch.setenv("FI_EXTRA_HEADERS", "Proxy-Authorization=Bearer " + refreshed)
        message = " | ".join((value, token, "diagnostic", refreshed))
        return httpx.Response(status, json={"status": False, "result": {
            "error_code": "validation_failed", "message": message, "diagnostic": message,
            "details": [{token: token}],
        }}, headers={"X-Request-Id": "trace-fixture-id", "Retry-After": "9"})

    client._management.shared._recorder._inner = httpx.MockTransport(handler)
    target = client.with_options(retries=0) if copy else client
    resource = target.gateway.config.with_raw_response if raw else target.gateway.config

    async def execute():
        try:
            await resource.get_active()
        finally:
            await client.aclose()

    with pytest.raises(BadRequestError) as caught:
        if asynchronous:
            asyncio.run(execute())
        else:
            try:
                resource.get_active()
            finally:
                client.close()
    error = caught.value
    assert len(calls) == 1
    safe = "[redacted] | [redacted] | [redacted] | " + refreshed
    assert error.payload == {"status": False, "result": {
        "error_code": "validation_failed", "message": safe, "diagnostic": safe,
        "details": [{token: "[redacted]"}],
    }}
    assert token not in str(error)
    assert error.request_id == "trace-fixture-id"
    assert error.retry_after == 9
    assert error.code == "validation_failed"
    assert error.status_code == 400


def test_overlapping_envelopes_keep_request_scoped_headers(monkeypatch):
    monkeypatch.setenv("FI_EXTRA_HEADERS", "")

    async def execute():
        first_sent, second_sent = asyncio.Event(), asyncio.Event()
        first = "first-proxy-fixture"
        second = "second-proxy-fixture"
        calls = []

        async def handler(request):
            token = request.headers["proxy-authorization"].split(" ", 1)[1]
            calls.append(token)
            if token == first:
                first_sent.set()
                await second_sent.wait()
            else:
                second_sent.set()
            return httpx.Response(200, json={"status": False, "result": {
                "error_code": "validation_failed", "message": token, "diagnostic": token,
            }})

        client = AsyncFutureAGIClient(api_key="api-fixture", secret_key="secret-fixture",
                                     base_url="http://localhost:9012", retries=0)
        client._management.shared._recorder._inner = httpx.MockTransport(handler)
        try:
            os.environ["FI_EXTRA_HEADERS"] = "Proxy-Authorization=Bearer " + first
            pending = asyncio.create_task(client.gateway.config.get_active())
            await first_sent.wait()
            os.environ["FI_EXTRA_HEADERS"] = "Proxy-Authorization=Bearer " + second
            errors = await asyncio.gather(pending, client.with_options(retries=0).gateway.config.get_active(),
                                          return_exceptions=True)
            assert calls == [first, second]
            for error in errors:
                assert isinstance(error, BadRequestError)
                assert error.payload["result"]["diagnostic"] == "[redacted]"
        finally:
            await client.aclose()

    asyncio.run(execute())
