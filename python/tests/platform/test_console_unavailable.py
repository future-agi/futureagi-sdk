"""Frozen FA/EE 404 bodies through public Console namespaces, with no preflight or egress."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

import fi
from fi import AsyncFutureAGIClient, FutureAGIClient, errors

FIXTURE = json.loads((Path(__file__).resolve().parents[3] / "tests/fixtures/server-contracts/console-404.json").read_text())
SOURCES = ["derived", "env", "argument"]
NAMESPACES = ["agents.get", "agents.runs.get", "agents.schedules.get", "environments.get", "connectors.get", "credentials.get"]
EXPLICIT_URL = "https://console.futureagi.com:8443/private-origin-path"
HOSTED = "Hosted Future AGI does not support Console access through the SDK in this release"


def make_client(monkeypatch, asynchronous, source, response, *, api_key="fixture-api-key"):
    monkeypatch.delenv("FI_PLATFORM_BASE_URL", raising=False)
    if source == "env":
        monkeypatch.setenv("FI_PLATFORM_BASE_URL", EXPLICIT_URL)
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls(api_key=api_key, secret_key="fixture-secret-key", base_url="https://api.futureagi.com",
                 retries=0, **({"platform_base_url": EXPLICIT_URL} if source == "argument" else {}))
    calls = []

    def handler(request):
        calls.append(request)
        return response()

    mock = httpx.MockTransport(handler)
    client._platform.shared._recorder._inner = mock
    client._platform.shared._recorder._inner_async = mock
    return client, calls


def invoke(client, name):
    target = client
    for part in name.split("."):
        target = getattr(target, part)
    result = target("missing-id")
    return asyncio.run(result) if asyncio.iscoroutine(result) else result


def close(client):
    if isinstance(client, AsyncFutureAGIClient):
        asyncio.run(client.aclose())
    else:
        client.close()


def fa_response(status=404):
    return httpx.Response(status, content=FIXTURE["fa_unrouted"]["body"],
                          headers={"content-type": FIXTURE["fa_unrouted"]["content_type"], "x-request-id": "fa-request"})


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("namespace", NAMESPACES)
def test_fa_unrouted_404_is_console_unavailable(monkeypatch, asynchronous, source, namespace):
    client, calls = make_client(monkeypatch, asynchronous, source, fa_response)
    try:
        with pytest.raises(errors.NotFoundError) as caught:
            invoke(client, namespace)
        error = caught.value
        assert type(error).__name__ == "ConsoleUnavailableError"
        assert error.get_error_code() == "CONSOLE_UNAVAILABLE"
        assert error.status_code == 404 and error.code == "http_404"
        assert error.request_id == "fa-request"
        host = "api.futureagi.com" if source == "derived" else "console.futureagi.com:8443"
        message = str(error)
        assert message.startswith(f"The Console API is not available at {host}.")
        assert HOSTED in message
        if source == "derived":
            assert "for self-hosted Enterprise, set FI_PLATFORM_BASE_URL to your Console API origin" in message
        else:
            assert "check" in message.lower() and "FI_PLATFORM_BASE_URL" in message
            assert "set FI_PLATFORM_BASE_URL" not in message
        for forbidden in ("fixture-api-key", "fixture-secret-key", "private-origin-path", "missing-id", "<html", "https://"):
            assert forbidden not in message
        assert len(calls) == 1
        assert calls[0].url.host == host.split(":")[0]
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("case", FIXTURE["ee"], ids=lambda case: case["id"])
def test_ee_404_keeps_existing_class(monkeypatch, asynchronous, source, case):
    client, calls = make_client(monkeypatch, asynchronous, source,
                                lambda: httpx.Response(404, json=case["body"], headers={"x-request-id": "fa-request"}))
    try:
        with pytest.raises(errors.NotFoundError) as caught:
            invoke(client, "agents.get")
        assert type(caught.value).__name__ == case["class"]
        assert caught.value.code == case["code"]
        assert "Console API is not available" not in str(caught.value)
        assert len(calls) == 1
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_envelope_detection_precedes_secret_scrubbing(monkeypatch, asynchronous):
    case = FIXTURE["ee"][0]
    client, calls = make_client(monkeypatch, asynchronous, "derived",
                                lambda: httpx.Response(404, json=case["body"]), api_key="not_found")
    try:
        with pytest.raises(errors.NotFoundError) as caught:
            invoke(client, "agents.get")
        assert type(caught.value) is errors.NotFoundError
        assert "not_found" not in str(caught.value)
        assert len(calls) == 1
    finally:
        close(client)


@pytest.mark.parametrize("status,expected", [(403, errors.PermissionDeniedError), (500, errors.ServerError)])
def test_non_404_is_unchanged(monkeypatch, status, expected):
    client, calls = make_client(monkeypatch, False, "derived", lambda: fa_response(status))
    try:
        with pytest.raises(expected):
            invoke(client, "agents.get")
        assert len(calls) == 1
    finally:
        close(client)


def test_fa_management_404_is_not_console_unavailable(monkeypatch):
    from fi._core.platform_base import PlatformCore
    from fi._core.policy import OperationSpec
    from fi._core.transport import PlatformShared

    client, _ = make_client(monkeypatch, False, "derived", fa_response)
    op = OperationSpec(name="gateway.keys.get", family="gateway", method="GET", path="/agentcc/keys/missing/")
    core = PlatformCore(PlatformShared(client._resolve_platform_origin, table={op.name: op}, transport=httpx.MockTransport(lambda _: fa_response())))
    try:
        with pytest.raises(errors.NotFoundError) as caught:
            core.call(op.name)
        assert type(caught.value) is errors.NotFoundError
    finally:
        core.shared.close()
        close(client)


class ErrorStream(httpx.SyncByteStream, httpx.AsyncByteStream):
    """Replay a recorded error in bounded chunks, optionally breaking mid-body."""

    def __init__(self, raw, chunk_size, interrupted):
        self.raw, self.chunk_size, self.interrupted = raw, chunk_size, interrupted
        self.chunks_read, self.closed = 0, False

    def __iter__(self):
        for offset in range(0, len(self.raw), self.chunk_size):
            self.chunks_read += 1
            yield self.raw[offset:offset + self.chunk_size]
        if self.interrupted:
            raise httpx.ReadError("fixture stream interrupted")

    async def __aiter__(self):
        for chunk in self:
            yield chunk

    def close(self):
        self.closed = True

    async def aclose(self):
        self.close()


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("case", [FIXTURE["ee"][0], FIXTURE["ee"][5]], ids=lambda case: case["id"])
@pytest.mark.parametrize("read_kind", ["capped", "interrupted", "empty-interrupted"])
def test_incomplete_ee_404_is_status_only(monkeypatch, asynchronous, source, case, read_kind):
    # OmegaEeError.detail is unbounded: extend the frozen body to exercise the SDK cap.
    body = {**case["body"], "detail": {"context": "x" * (70 * 1024)}}
    raw = json.dumps(body).encode()
    if read_kind != "capped":
        raw = raw[:80] if read_kind == "interrupted" else b""
    stream = ErrorStream(raw, 8192, read_kind != "capped")
    client, calls = make_client(monkeypatch, asynchronous, source,
                               lambda: httpx.Response(404, stream=stream, headers={"x-request-id": "ee-request"}))
    try:
        with pytest.raises(errors.NotFoundError) as caught:
            invoke(client, "agents.get")
        assert type(caught.value) is errors.NotFoundError
        assert caught.value.code == "http_404"
        assert caught.value.request_id == "ee-request"
        assert "Console API is not available" not in str(caught.value)
        assert len(calls) == 1 and stream.closed
        assert stream.chunks_read <= 8  # stop at the cap; no unbounded buffering
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_oversized_single_chunk_ee_404_is_not_unavailable(monkeypatch, asynchronous):
    body = {**FIXTURE["ee"][0]["body"], "detail": {"context": "x" * (70 * 1024)}}
    client, calls = make_client(monkeypatch, asynchronous, "derived", lambda: httpx.Response(404, json=body))
    try:
        with pytest.raises(errors.NotFoundError) as caught:
            invoke(client, "agents.get")
        assert type(caught.value) is errors.NotFoundError
        assert len(calls) == 1
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("source", SOURCES)
def test_oversized_html_404_is_conservatively_status_only(monkeypatch, asynchronous, source):
    # Even non-EE HTML cannot establish absence of an envelope without a complete read.
    raw = FIXTURE["fa_unrouted"]["body"].encode() * 512
    stream = ErrorStream(raw, 8192, False)
    client, calls = make_client(monkeypatch, asynchronous, source,
                               lambda: httpx.Response(404, stream=stream, headers={"content-type": "text/html"}))
    try:
        with pytest.raises(errors.NotFoundError) as caught:
            invoke(client, "agents.get")
        assert type(caught.value) is errors.NotFoundError
        assert caught.value.code == "http_404"
        assert len(calls) == 1 and stream.closed
        assert stream.chunks_read <= 8
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_saved_login_origin_hint_names_the_saved_login(monkeypatch, tmp_path, asynchronous):
    login_file = tmp_path / "login.json"
    login_file.write_text(json.dumps({"base_url": "https://api.futureagi.com", "platform_base_url": EXPLICIT_URL,
                                    "api_key": "fixture-api-key", "secret_key": "fixture-secret-key"}))
    monkeypatch.setenv("FI_LOGIN_FILE", str(login_file))
    monkeypatch.delenv("FI_PLATFORM_BASE_URL", raising=False)
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls(base_url="https://api.futureagi.com", retries=0)
    calls = []
    mock = httpx.MockTransport(lambda request: calls.append(request) or fa_response())
    client._platform.shared._recorder._inner = mock
    client._platform.shared._recorder._inner_async = mock
    try:
        assert client._platform.shared.origin().source == "login"
        with pytest.raises(errors.ConsoleUnavailableError) as caught:
            invoke(client, "agents.get")
        message = str(caught.value)
        assert "check the Console API URL in your saved login" in message
        assert HOSTED in message and "console.futureagi.com:8443" in message
        for forbidden in ("FI_PLATFORM_BASE_URL", "platform_base_url", "fixture-api-key", "private-origin-path"):
            assert forbidden not in message
        assert len(calls) == 1
    finally:
        close(client)


def test_console_unavailable_public_exports():
    assert "ConsoleUnavailableError" in errors.__all__
    assert "ConsoleUnavailableError" in fi.__all__
    assert fi.ConsoleUnavailableError is errors.ConsoleUnavailableError
    assert issubclass(errors.ConsoleUnavailableError, errors.NotFoundError)
