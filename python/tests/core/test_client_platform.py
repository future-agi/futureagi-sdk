"""The client changes for the platform: the platform options
reach the origin, a bad platform setting never breaks a core namespace, and with_options returns a
copy that shares the pools. The status and connection mapping on core namespaces is
test_error_mapping.py."""

from __future__ import annotations

import asyncio

import httpx
import pytest

import fi.errors as errors
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi._core.platform_base import PlatformCore
from fi._core.transport import PlatformShared
from tests.core._support import OPS, respond

KEYS = {"api_key": "k-test-1234", "secret_key": "s-test-1234"}


def test_a_bad_platform_setting_never_breaks_a_core_namespace(monkeypatch):
    monkeypatch.setenv("FI_PLATFORM_BASE_URL", "https://evil.example/omega/api")
    client = FutureAGIClient(**KEYS, base_url="http://api.test", retries=0)  # constructing never raises
    client.generated_client._httpx_args["transport"]._wrapped = httpx.MockTransport(
        lambda r: httpx.Response(200, json={"ok": 1})
    )
    assert client.users.current() == {"ok": 1}
    client._platform.shared.table = OPS
    with pytest.raises(errors.HostNotAllowedError):
        client._platform.call("capabilities.get")


def test_the_client_passes_its_platform_options_through(monkeypatch):
    monkeypatch.delenv("FI_PLATFORM_BASE_URL")
    client = FutureAGIClient(
        **KEYS,
        base_url="https://fa.example.org",
        workspace_id="ws-2",
        platform_base_url="https://other.example/api",
        allow_custom_platform_url=False,
    )
    o = client._resolve_platform_origin()  # both from arguments: same source, accepted
    assert o.base == "https://other.example/api" and o.headers["X-Workspace-Id"] == "ws-2"


# -- with_options -----------------------------------------------------------------------------


def test_with_options_changes_timeout_and_retries_and_shares_the_pools():
    calls = []

    def handler(request):
        calls.append(request)
        return respond(503) if request.url.path.endswith("/conversations/c1") else respond(200, {"ok": 1})

    client = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://api.test", retries=2)
    inner = httpx.MockTransport(handler)
    client.generated_client._httpx_args["transport"]._wrapped = inner
    client.__dict__["_platform"] = PlatformCore(
        PlatformShared(client._resolve_platform_origin, retries=2, table=OPS, transport=inner, sleep=lambda s: None)
    )
    quick = client.with_options(timeout=3, retries=0)
    assert quick.generated_client.get_httpx_client().timeout.read == 3.0
    assert client.generated_client.get_httpx_client().timeout.read == 30.0
    assert quick.users.current() == {"ok": 1}  # through the original's pool
    with pytest.raises(errors.ServerError):
        quick._platform.call("runs.get", path={"id": "c1"})
    assert len([c for c in calls if c.url.path.endswith("/c1")]) == 1 and calls[-1].extensions["timeout"]["read"] == 3.0
    assert quick._platform.shared is client._platform.shared
    quick.close()  # a copy's close leaves the shared pool open
    assert client.users.current() == {"ok": 1}


def test_async_with_options():
    async def go():
        client = AsyncFutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://api.test")
        quick = client.with_options(timeout=2.5)
        out = (quick.generated_client.get_async_httpx_client().timeout.read, quick._platform.settings.timeout.read)
        await client.aclose()
        return out

    assert asyncio.run(go()) == (2.5, 2.5)
