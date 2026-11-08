"""Cleartext compatibility warns without changing destination isolation."""
from __future__ import annotations

import socket
import warnings

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, AgentCCError
from fi.gateway._deprecation import AgentCCDeprecationWarning
from fi.gateway._http_security import validate_destination


@pytest.mark.parametrize("origin", ["http://gateway.test", "http://10.0.0.8:8080", "http://[2001:db8::1]:8080"])
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_cleartext_sends_and_warns_once_per_client(origin, asynchronous, monkeypatch):
    def no_dns(*args, **kwargs):
        raise AssertionError("Destination validation must not resolve DNS")

    monkeypatch.setattr(socket, "getaddrinfo", no_dns)
    requests = []
    wire_headers = []

    def handle(request):
        wire_headers.append(dict(request.headers))
        requests.append(request)
        return httpx.Response(200, json={"object": "list", "data": []})

    expected = (
        "futureagi: sending gateway credentials in cleartext over HTTP to "
        f"{origin}. Use HTTPS; plain HTTP outside loopback will be rejected "
        "in a future major release."
    )
    for _ in range(2):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            if asynchronous:
                async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
                    async with AsyncAgentCC(api_key="synthetic-key", base_url=origin, http_client=http) as client:
                        await client.models.list()
                        await client.models.list()
            else:
                with httpx.Client(transport=httpx.MockTransport(handle)) as http:
                    with AgentCC(api_key="synthetic-key", base_url=origin, http_client=http) as client:
                        client.models.list()
                        client.models.list()
        assert len(caught) == 1
        assert caught[0].category is AgentCCDeprecationWarning
        assert str(caught[0].message) == expected
    assert len(requests) == 4
    assert len(wire_headers) == 4
    assert all(headers["authorization"] == "Bearer synthetic-key" for headers in wire_headers)
    assert all(request.headers["authorization"] == "[REDACTED]" for request in requests)


@pytest.mark.parametrize("origin", ["https://gateway.test", "http://localhost:8000", "http://127.0.0.2", "http://[::1]"])
def test_secure_and_loopback_origins_do_not_warn(origin):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        validate_destination(origin, origin)
    assert caught == []


def test_concurrent_requests_warn_once_for_the_public_client():
    from concurrent.futures import ThreadPoolExecutor

    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"object": "list", "data": []})

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        client = AgentCC(api_key="synthetic-key", base_url="http://gateway.test", http_client=http)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(lambda _: client.models.list(), range(16)))
        client.close()
    assert len(results) == len(seen) == 16
    assert len(caught) == 1 and caught[0].category is AgentCCDeprecationWarning


def test_warning_deduplicates_canonical_origin_but_not_other_origins():
    seen = set()
    with pytest.warns(AgentCCDeprecationWarning) as caught:
        validate_destination("http://GATEWAY.test", "http://gateway.test:80/a", warned_origins=seen)
        validate_destination("http://gateway.test", "http://gateway.test/b", warned_origins=seen)
        validate_destination("http://gateway.test:8080", "http://gateway.test:8080/b", warned_origins=seen)
    assert len(caught) == 2


@pytest.mark.parametrize("url", ["https://other.test", "http://gateway.test:81", "http://user:password@gateway.test", "http://gateway.test/#fragment", "http://gateway.test/\\other", "http://gateway.test/\n"])
def test_destination_rejection_remains_fail_closed(url):
    with warnings.catch_warnings(record=True) as caught:
        with pytest.raises(AgentCCError):
            validate_destination("http://gateway.test", url)
    assert caught == []
