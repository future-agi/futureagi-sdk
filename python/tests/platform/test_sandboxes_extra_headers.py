"""FI_EXTRA_HEADERS on the environment connection (``Sandbox.create`` / ``connect`` / ``list`` /
``settings``, the handles they return, and the ``sandbox`` command line), exactly as
``FutureAGIClient`` sends it: on every request under OMEGA_BASE_URL and never to another host or a
path outside it, never over the SDK's own headers, read when each request is sent, a malformed
value refused before anything is sent, and a reflected value never in an error. A scope header of
either mode named there is dropped on every sandbox request, on this path and on
``client.sandboxes`` alike, with one line on stderr per name that names the header (never its
value), while the shared parser (and so every other client) still accepts it.
No network (the frozen-OpenAPI mock); every header value here is made up."""

from __future__ import annotations

import pytest
from fi import AsyncFutureAGIClient, FutureAGIClient, _extra_headers
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import SCOPE_HEADERS, PlatformCore
from fi._core.transport import PlatformShared
from fi._extra_headers import ExtraHeaders, ExtraHeadersError, drop_scope, parse
from fi.sandbox import (
    AsyncSandbox,
    AsyncSandboxes,
    PermissionDeniedError,
    Sandbox,
    Sandboxes,
    _connection,
)
from fi.sandbox._connection import OriginRule, SandboxConnection

from ._sandbox_mock import (
    FAKE_KEY,
    FAKE_SECRET,
    FAKE_TOKEN,
    HOSTED,
    MODES,
    ORIGIN,
    SBX,
    MockServer,
    error,
    origin,
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
    monkeypatch.setenv("OMEGA_BASE_URL", HOSTED)
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
        assert str(seen.request.url).startswith(HOSTED + "/")


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
    assert extra.for_url(HOSTED + f"/workspace/sandboxes/{SBX}")["Proxy-Authorization"] == PROXY
    for url in ("https://other.example.test/omega/api/workspace/sandboxes",
                "https://sbx.futureagi.com:8443/omega/api/workspace/sandboxes",
                "http://sbx.futureagi.com/omega/api/workspace/sandboxes",
                "https://sbx.futureagi.com/elsewhere", "https://sbx.futureagi.com/omega/apiary"):
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


SCOPE_NAMES = ("x-omega-workspace", "X-Omega-Org", "X-Workspace-Id", "x-organization-id")
SCOPE = frozenset(name.lower() for name in SCOPE_NAMES)
SCOPE_VALUE = "scope-from-the-setting"
SCOPE_SETTING = ";".join(f"{name}={SCOPE_VALUE}" for name in SCOPE_NAMES)
#: The selectors the SDK itself sends in each mode: workspace, then organization.
OWN = {"keys": ("x-workspace-id", "x-organization-id"), "bearer": ("x-omega-workspace", "x-omega-org")}
SITE = "https://sbx.futureagi.com"  # a client base_url HOSTED is under, so extras reach it


def scope_sent(seen):
    """The scope header names a request carried, lower case."""
    return SCOPE & {name.lower() for name in seen.request.headers.keys()}


@pytest.fixture
def notices(monkeypatch):
    """A fresh one-time budget: each test sees the dropped-header notice afresh."""
    monkeypatch.setattr(_extra_headers, "_dropped", set())


def notice_lines(err):
    return [line for line in err.splitlines() if line.startswith("futureagi: ") and SETTING in line]


def bearer_env(monkeypatch):
    """The self-host token on loopback instead of the autouse key pair."""
    monkeypatch.delenv("FI_API_KEY")
    monkeypatch.delenv("FI_SECRET_KEY")
    monkeypatch.setenv("OMEGA_BASE_URL", "http://127.0.0.1:8787")
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", FAKE_TOKEN)


def test_the_executor_drops_exactly_the_scope_selectors_of_both_modes():
    assert SCOPE_HEADERS == SCOPE == {name.lower() for names in OWN.values() for name in names}


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("auth", ["keys", "bearer"])
def test_a_scope_header_in_the_setting_is_dropped_on_every_call(mode, auth, server, monkeypatch):
    if auth == "bearer":
        bearer_env(monkeypatch)
    monkeypatch.setenv(SETTING, f"Proxy-Authorization={PROXY};X-Team=env-team;{SCOPE_SETTING}")

    async def go():
        sbx = await resolve(cls(mode).connect(SBX))
        await resolve(sbx.commands.run("ls"))
        await resolve(sbx.files.download("a.bin"))
        await resolve(cls(mode).list())

    run(go())
    sent = {seen.name for seen in server.seen}
    assert sent >= {"sandboxes.getInfo", "sandboxes.commands.run", "sandboxes.files.download", "sandboxes.list"}
    for seen in server.seen:  # sent, with every other extra header, and no scope header at all
        assert carries(seen) and scope_sent(seen) == set(), seen.name
        assert SCOPE_VALUE not in seen.request.headers.values()


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("auth", ["keys", "bearer"])
def test_the_sdks_own_scope_is_the_only_scope_sent(mode, auth, server, monkeypatch):
    if auth == "bearer":
        bearer_env(monkeypatch)
    monkeypatch.setenv("FI_WORKSPACE_ID", "ws_own")
    monkeypatch.setenv(SETTING, f"X-Team=env-team;{SCOPE_SETTING}")
    run(resolve(cls(mode).list()))
    headers = server.last.request.headers
    workspace, _ = OWN[auth]
    assert headers.get_list(workspace) == ["ws_own"] and headers["x-team"] == "env-team"
    assert scope_sent(server.last) == {workspace}


def test_a_dropped_scope_header_is_named_once_on_stderr(notices, capsys):
    headers = {"X-Team": "t1", "X-Workspace-Id": SCOPE_VALUE, "x-omega-org": SCOPE_VALUE}
    assert drop_scope(headers, SCOPE_HEADERS) == {"X-Team": "t1"}
    assert drop_scope(headers, SCOPE_HEADERS) == {"X-Team": "t1"}  # dropped again, said once
    err = capsys.readouterr().err
    lines = notice_lines(err)
    assert len(err.splitlines()) == len(lines) == 2
    assert [line.split()[1] for line in lines] == ["X-Workspace-Id", "x-omega-org"]
    assert all("FI_WORKSPACE_ID" in line and "default workspace" in line for line in lines)
    assert SCOPE_VALUE not in err
    assert drop_scope({"X-Team": "t1"}, SCOPE_HEADERS) == {"X-Team": "t1"}
    assert capsys.readouterr().err == ""  # nothing dropped, nothing said


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("auth", ["keys", "bearer"])
def test_every_sandbox_call_drops_a_scope_header_with_one_notice_per_name(mode, auth, server, monkeypatch,
                                                                          notices, capsys):
    if auth == "bearer":
        bearer_env(monkeypatch)
    monkeypatch.setenv(SETTING, f"X-Team=env-team;{SCOPE_SETTING}")

    async def go():
        await resolve(cls(mode).list())
        sbx = await resolve(cls(mode).connect(SBX))
        await resolve(sbx.files.download("a.bin"))

    run(go())
    assert {seen.name for seen in server.seen} >= {"sandboxes.list", "sandboxes.getInfo", "sandboxes.files.download"}
    assert all(scope_sent(seen) == set() for seen in server.seen)
    err = capsys.readouterr().err
    lines = notice_lines(err)
    assert sorted(line.split()[1] for line in lines) == sorted(SCOPE_NAMES)
    assert SCOPE_VALUE not in err


@pytest.mark.parametrize("name", SCOPE_NAMES)
def test_the_shared_parser_still_accepts_a_scope_name_for_every_other_client(name):
    extra = ExtraHeaders(HOSTED, {name: "org-from-the-argument", "X-Team": "argument-team"})
    assert extra.for_url(HOSTED + "/workspace/sandboxes")[name] == "org-from-the-argument"
    assert parse(f"{name.upper()}=org-from-the-text") == {name.upper(): "org-from-the-text"}


@pytest.mark.parametrize("mode", MODES)
def test_a_client_built_with_a_scope_header_drops_it_on_client_sandboxes(mode, monkeypatch, tmp_path):
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "no-login.json"))
    for name in ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY"):
        monkeypatch.delenv(name)
    server = MockServer()
    extra = {"X-Omega-Workspace": "ws-from-the-argument", "X-Organization-Id": "org-from-the-argument",
             "X-Team": "argument-team"}
    client = (AsyncFutureAGIClient if mode == "async" else FutureAGIClient)(
        api_key=FAKE_KEY, secret_key=FAKE_SECRET, base_url=SITE, platform_base_url=HOSTED, retries=0,
        workspace_id="ws_own", extra_headers=extra,
    )
    shared = client._platform.shared
    shared._recorder._inner = shared._recorder._inner_async = server.transport()

    async def go():
        try:
            await resolve(client.sandboxes.list())
        finally:
            await resolve(client.aclose() if mode == "async" else client.close())

    run(go())
    headers = server.last.request.headers
    assert server.last.name == "sandboxes.list" and carries(server.last, team="argument-team")
    assert headers.get_list("x-workspace-id") == ["ws_own"] and scope_sent(server.last) == {"x-workspace-id"}
    assert headers["x-api-key"] == FAKE_KEY


@pytest.mark.parametrize("mode", MODES)
def test_a_bearer_executor_never_gains_the_keys_selectors(mode, monkeypatch):
    monkeypatch.delenv(SETTING)
    server = MockServer()
    found = origin("bearer", workspace="ws_own")
    extra = ExtraHeaders(ORIGIN, {"X-Workspace-Id": "ws-extra", "x-omega-org": "org-extra", "X-Team": "t1"})
    shared = PlatformShared(lambda: found, transport=server.transport(), retries=0, extra_headers=extra)
    rule = OriginRule(allow_custom_base_url=True)
    if mode == "async":
        api = AsyncSandboxes(AsyncPlatformCore(shared), rule=rule)
    else:
        api = Sandboxes(PlatformCore(shared), rule=rule)
    run(resolve(api.list()))
    headers = server.last.request.headers
    assert headers["authorization"] == f"Bearer {FAKE_TOKEN}" and headers["x-team"] == "t1"
    assert headers.get_list("x-omega-workspace") == ["ws_own"] and scope_sent(server.last) == {"x-omega-workspace"}


def test_the_command_line_drops_a_scope_header_too(server, monkeypatch, capsys):
    from fi._cli import main as cli_main
    from fi._cli import registry

    from ._sandbox_cli_support import _EP

    monkeypatch.setattr(registry, "entry_points", lambda: [_EP()])
    monkeypatch.setenv(SETTING, f"Proxy-Authorization={PROXY};X-Team=env-team;{SCOPE_SETTING}")
    assert cli_main.main(["sandbox", "list"]) == 0
    assert carries(server.last) and scope_sent(server.last) == set()
    monkeypatch.setenv("FI_WORKSPACE_ID", "ws_own")
    assert cli_main.main(["sandbox", "list", "--json"]) == 0
    assert server.last.request.headers.get_list("x-workspace-id") == ["ws_own"]
    assert scope_sent(server.last) == {"x-workspace-id"}
    captured = capsys.readouterr()
    assert SCOPE_VALUE not in captured.out + captured.err and TOKEN not in captured.out + captured.err
