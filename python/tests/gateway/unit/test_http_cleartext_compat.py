"""Plain HTTP through the opt-in notes once per process and does not change destination isolation."""
from __future__ import annotations

import socket
import warnings

import httpx
import pytest

from fi._core import http_security
from fi.gateway import AgentCC, AsyncAgentCC, AgentCCError
from fi.gateway._http_security import validate_destination
from tests._judged_mock_transport import JudgedMockTransport


@pytest.fixture(autouse=True)
def _fresh_notice(monkeypatch):
    monkeypatch.setattr(http_security, "_warned", set())


@pytest.mark.parametrize("origin", ["http://gateway.test", "http://192.0.2.8:8080", "http://[2001:db8::1]:8080"])
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_opted_in_plain_http_sends_and_notes_once_per_process(origin, asynchronous, monkeypatch, capsys):
    def no_dns(*args, **kwargs):
        raise AssertionError("Destination validation must not resolve DNS")

    monkeypatch.setattr(socket, "getaddrinfo", no_dns)
    requests = []
    wire_headers = []

    def handle(request):
        wire_headers.append(dict(request.headers))
        requests.append(request)
        return httpx.Response(200, json={"object": "list", "data": []})

    for _ in range(2):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            if asynchronous:
                async with httpx.AsyncClient(transport=JudgedMockTransport(handle)) as http:
                    async with AsyncAgentCC(api_key="synthetic-key", base_url=origin, http_client=http) as client:
                        await client.models.list()
                        await client.models.list()
            else:
                with httpx.Client(transport=JudgedMockTransport(handle)) as http:
                    with AgentCC(api_key="synthetic-key", base_url=origin, http_client=http) as client:
                        client.models.list()
                        client.models.list()
        assert [w for w in caught if "FI_ALLOW_INSECURE_HTTP" in str(w.message)] == []
    notice = capsys.readouterr().err
    assert notice.count("FI_ALLOW_INSECURE_HTTP") == 1 and origin.split("//")[1] in notice
    assert "synthetic-key" not in notice
    assert len(requests) == 4
    assert all(headers["authorization"] == "Bearer synthetic-key" for headers in wire_headers)
    assert all(request.headers["authorization"] == "[REDACTED]" for request in requests)


@pytest.mark.parametrize("origin", ["https://gateway.test", "http://localhost:8000", "http://127.0.0.2", "http://[::1]"])
def test_secure_and_loopback_origins_do_not_note(origin, capsys):
    validate_destination(origin, origin)
    assert capsys.readouterr().err == ""


def test_concurrent_requests_note_once_for_the_public_client(capsys):
    from concurrent.futures import ThreadPoolExecutor

    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"object": "list", "data": []})

    with httpx.Client(transport=JudgedMockTransport(handle)) as http:
        client = AgentCC(api_key="synthetic-key", base_url="http://gateway.test", http_client=http)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: client.models.list(), range(16)))
        client.close()
    assert len(results) == len(seen) == 16
    assert capsys.readouterr().err.count("FI_ALLOW_INSECURE_HTTP") == 1


def test_one_notice_covers_every_origin(capsys):
    validate_destination("http://GATEWAY.test", "http://gateway.test:80/a")
    validate_destination("http://gateway.test", "http://gateway.test/b")
    validate_destination("http://gateway.test:8080", "http://gateway.test:8080/b")
    assert capsys.readouterr().err.count("FI_ALLOW_INSECURE_HTTP") == 1


@pytest.mark.parametrize("url", ["https://other.test", "http://gateway.test:81", "http://user:password@gateway.test", "http://gateway.test/#fragment", "http://gateway.test/\\other", "http://gateway.test/\n"])
def test_destination_rejection_remains_fail_closed(url, capsys):
    with pytest.raises(AgentCCError):
        validate_destination("http://gateway.test", url)
    assert capsys.readouterr().err == ""
