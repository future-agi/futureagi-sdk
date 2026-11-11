"""FI_EXTRA_HEADERS on the environment connection (``Sandbox.create`` / ``connect`` / ``list`` /
``settings``, the handles they return, and the ``sandbox`` command line), exactly as
``FutureAGIClient`` sends it: on every request under OMEGA_BASE_URL and never to another host or a
path outside it, never over the SDK's own headers, read when each request is sent, a malformed
value refused before anything is sent, and a reflected value never in an error. No network (the
frozen-OpenAPI mock); every header value here is made up."""

from __future__ import annotations

import pytest
from fi._extra_headers import ExtraHeadersError
from fi.sandbox import AsyncSandbox, PermissionDeniedError, Sandbox, _connection
from fi.sandbox._connection import SandboxConnection

from ._sandbox_mock import (
    FAKE_KEY,
    FAKE_SECRET,
    MODES,
    ORIGIN,
    SBX,
    MockServer,
    error,
    resolve,
    run,
)

SETTING = "FI_EXTRA_HEADERS"
TOKEN = "fake-proxy-token-" + "y" * 12  # low entropy on purpose (never a real token)
PROXY = f"Bearer {TOKEN}"
ENV = ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
       "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID", "FI_ALLOW_INSECURE_HTTP", "FI_BASE_URL",
       "FI_PLATFORM_BASE_URL", "FI_PLATFORM_TOKEN", "FI_ALLOW_CUSTOM_PLATFORM_URL", SETTING)


@pytest.fixture(autouse=True)
def hosted(monkeypatch):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OMEGA_BASE_URL", ORIGIN)
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    monkeypatch.setenv(SETTING, f"Proxy-Authorization={PROXY};X-Team=env-team")


@pytest.fixture
def server(monkeypatch):
    mock = MockServer()
    monkeypatch.setattr(_connection, "default_transport", mock.transport)
    return mock


def cls(mode):
    return AsyncSandbox if mode == "async" else Sandbox


def carries(seen, team="env-team"):
    headers = seen.request.headers
    return headers.get("proxy-authorization") == PROXY and headers.get("x-team") == team


@pytest.mark.parametrize("mode", MODES)
def test_every_environment_call_carries_the_extra_headers(mode, server):
    async def go():
        sbx = await resolve(cls(mode).create(name="n"))
        await resolve(sbx.commands.run("ls"))
        await resolve(cls(mode).connect(SBX))
        await resolve(cls(mode).list())
        await resolve(cls(mode).settings())

    run(go())
    sent = {seen.name for seen in server.seen}
    assert sent >= {"sandboxes.create", "sandboxes.commands.run", "sandboxes.getInfo", "sandboxes.list",
                    "sandboxes.settings.get"}
    assert all(carries(seen) for seen in server.seen)
    for seen in server.seen:  # the SDK's own headers are its own, never the setting's
        assert seen.request.headers["x-api-key"] == FAKE_KEY
        assert str(seen.request.url).startswith(ORIGIN + "/")


@pytest.mark.parametrize("mode", MODES)
def test_the_setting_is_read_when_each_request_is_sent(mode, server, monkeypatch):
    async def go():
        sbx = await resolve(cls(mode).connect(SBX))
        monkeypatch.setenv(SETTING, f"Proxy-Authorization={PROXY};X-Team=refreshed")
        await resolve(sbx.refresh())

    run(go())
    assert carries(server.seen[0]) and carries(server.last, team="refreshed")


def test_the_headers_go_only_under_the_base_url():
    extra = SandboxConnection().core().shared.extra_headers
    assert extra.for_url(ORIGIN + f"/workspace/sandboxes/{SBX}")["Proxy-Authorization"] == PROXY
    for url in ("https://other.example.test/omega/api/workspace/sandboxes",
                "https://sbx.example.test:8443/omega/api/workspace/sandboxes",
                "http://sbx.example.test/omega/api/workspace/sandboxes",
                "https://sbx.example.test/elsewhere", "https://sbx.example.test/omega/apiary"):
        assert extra.for_url(url) == {}, url


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("value", [f"Proxy-Authorization {PROXY}", "Authorization=Bearer x-1234567"])
def test_a_malformed_or_reserved_setting_is_refused_before_anything_is_sent(mode, value, server, monkeypatch):
    monkeypatch.setenv(SETTING, value)
    with pytest.raises(ExtraHeadersError) as caught:
        run(resolve(cls(mode).list()))
    assert server.seen == [] and SETTING in str(caught.value)
    assert TOKEN not in str(caught.value) and "x-1234567" not in str(caught.value)


@pytest.mark.parametrize("mode", MODES)
def test_a_reflected_value_never_reaches_a_sandbox_error(mode, server):
    server.on("sandboxes.list", lambda request: error(403, "forbidden", message=f"proxy refused {PROXY}"))
    with pytest.raises(PermissionDeniedError) as caught:
        run(resolve(cls(mode).list()))
    assert carries(server.last) and "proxy refused" in str(caught.value)
    assert TOKEN not in str(caught.value) + repr(caught.value.payload) + repr(caught.value.detail)


def test_the_command_line_sends_them_too(server, monkeypatch, capsys):
    from fi._cli import main as cli_main
    from fi._cli import registry

    from ._sandbox_cli_support import _EP

    monkeypatch.setattr(registry, "entry_points", lambda: [_EP()])
    assert cli_main.main(["sandbox", "list", "--json"]) == 0
    assert carries(server.last)
    captured = capsys.readouterr()
    assert TOKEN not in captured.out + captured.err
