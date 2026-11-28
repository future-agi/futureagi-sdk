"""The handle's lifecycle beyond test_sandboxes_handle.py (sync and async): ``async with
AsyncSandbox.create()`` and ``.connect()`` used directly (contract section 3); a restored or listed
sandbox that remains usable after its source connection closes; failed deletes on exit reported
even without exception notes; no default host on the client path (contract section 2);
and connection errors that name the setting this path reads without suggesting a retry of a
call that may have run. Fake credentials only."""

from __future__ import annotations

import httpx
import pytest
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.sandbox import AsyncSandbox, ConfigurationError, Sandbox, _connection
from fi.sandbox import ConnectionError as SandboxConnectionError

from ._sandbox_mock import (
    FAKE_KEY,
    FAKE_SECRET,
    MODES,
    SBX,
    SNAP,
    MockServer,
    api,
    error,
    resolve,
    run,
)

OTHER = "sbx_" + "d" * 24
ENV = ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FUTUREAGI_OMEGA_API_KEY", "FI_WORKSPACE_ID",
       "FI_ORGANIZATION_ID", "FI_BASE_URL", "FI_PLATFORM_BASE_URL", "FI_PLATFORM_TOKEN",
       "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS")


@pytest.fixture(autouse=True)
def clean(monkeypatch, tmp_path):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "no-login.json"))


@pytest.fixture
def env(monkeypatch):
    """``Sandbox.create`` / ``connect`` / ``list`` / ``settings`` on a loopback EE, over the mock."""
    server = MockServer()
    monkeypatch.setenv("OMEGA_BASE_URL", "http://127.0.0.1:8787")
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", "fake-token-0009")
    monkeypatch.setattr(_connection, "default_transport", server.transport)
    return server


def cls(mode):
    return AsyncSandbox if mode == "async" else Sandbox


def names(server):
    return [seen.name for seen in server.seen]


def record(ident=SBX, state="active"):
    return {"schemaVersion": "omega-workspace-sandboxes/v1", "sandbox": {"id": ident, "state": state}}


def destroyed(request):
    """The kill answer for the sandbox the request names (the default answer names SBX)."""
    return httpx.Response(200, json=record(request.url.path.rsplit("/", 1)[-1], "destroyed"))


async def shut(sbx):
    await resolve(sbx.aclose() if isinstance(sbx, AsyncSandbox) else sbx.close())


def no_backoff(monkeypatch):
    import fi._http

    monkeypatch.setattr(fi._http, "backoff_s", lambda *args: 0)


@pytest.mark.parametrize("how", ["create", "connect"])
def test_async_with_takes_create_and_connect_directly(env, how):
    async def go():
        made = AsyncSandbox.create(name="n") if how == "create" else AsyncSandbox.connect(SBX)
        async with made as sbx:
            assert type(sbx) is AsyncSandbox and sbx.id == SBX and sbx._owns_pool
        return sbx

    run(go())
    assert names(env) == ["sandboxes.create" if how == "create" else "sandboxes.getInfo", "sandboxes.kill"]


def test_awaiting_create_gives_the_handle_and_the_sync_create_is_the_handle(env):
    async def go():
        sbx = await AsyncSandbox.create(name="n")
        await sbx.aclose()
        return sbx

    assert type(run(go())) is AsyncSandbox
    plain = Sandbox.create(name="n")
    assert type(plain) is Sandbox and plain._owns_pool
    plain.close()
    assert names(env) == ["sandboxes.create", "sandboxes.create"]


@pytest.mark.parametrize("mode", MODES)
def test_a_restored_sandbox_outlives_the_with_block_of_its_source(env, mode):
    env.on("sandboxes.snapshots.restore", lambda request: httpx.Response(201, json=record(OTHER)))
    env.on("sandboxes.kill", destroyed)

    async def go():
        if mode == "async":
            async with AsyncSandbox.create() as source:
                restored = await source.snapshots.restore(SNAP)
        else:
            with Sandbox.create() as source:
                restored = source.snapshots.restore(SNAP)
        await resolve(restored.commands.run("ls"))
        await resolve(restored.delete())
        await shut(restored)
        return restored

    assert run(go()).id == OTHER
    assert names(env) == ["sandboxes.create", "sandboxes.snapshots.restore", "sandboxes.kill",
                          "sandboxes.commands.run", "sandboxes.kill"]
    assert env.last.request.url.path.endswith("/" + OTHER)


@pytest.mark.parametrize("mode", MODES)
def test_list_and_settings_close_their_pool_and_a_listed_handle_reopens_it(env, mode, monkeypatch):
    closed = []
    real_close, real_aclose = _connection.ReopeningShared.close, _connection.ReopeningShared.aclose

    def close(self):
        closed.append("close")
        real_close(self)

    async def aclose(self):
        closed.append("aclose")
        await real_aclose(self)

    monkeypatch.setattr(_connection.ReopeningShared, "close", close)
    monkeypatch.setattr(_connection.ReopeningShared, "aclose", aclose)
    body = {"schemaVersion": "omega-workspace-sandboxes/v1", "caps": {}, "sandboxes": [{"id": SBX}]}
    env.on("sandboxes.list", lambda request: httpx.Response(200, json=body))

    async def go():
        listed = (await resolve(cls(mode).list())).sandboxes[0]
        await resolve(listed.refresh())
        await shut(listed)
        return await resolve(cls(mode).settings())

    assert "caps" in run(go())
    assert names(env) == ["sandboxes.list", "sandboxes.getInfo", "sandboxes.settings.get"]
    assert closed == ["aclose" if mode == "async" else "close"] * 3


class _NoNotes(Exception):
    """An exception without ``add_note`` (as on Python 3.10)."""

    def __getattribute__(self, name):
        if name == "add_note":
            raise AttributeError(name)
        return super().__getattribute__(name)


@pytest.mark.parametrize("mode", MODES)
def test_a_failed_delete_on_exit_warns_where_exceptions_have_no_notes(mode):
    server = MockServer()
    server.on("sandboxes.kill", lambda request: error(503, "unavailable"))
    sbx = cls(mode)(api(server, mode, retries=0), {"id": SBX, "state": "active"})

    async def go():
        if mode == "async":
            async with sbx:
                raise _NoNotes("body")
        with sbx:
            raise _NoNotes("body")

    with pytest.warns(RuntimeWarning, match=f"deleting sandbox {SBX} on exit failed"):
        with pytest.raises(_NoNotes):
            run(go())


def client_over(server, mode, **options):
    """A real FutureAGIClient / AsyncFutureAGIClient whose platform HTTP boundary is the mock."""
    client = (AsyncFutureAGIClient if mode == "async" else FutureAGIClient)(retries=0, **options)
    shared = client._platform.shared
    shared._recorder._inner = shared._recorder._inner_async = httpx.MockTransport(server.handler)
    return client


def list_over(client):
    async def go():
        try:
            return await resolve(client.sandboxes.list())
        finally:
            await resolve(client.aclose() if isinstance(client, AsyncFutureAGIClient) else client.close())

    return run(go())


@pytest.mark.parametrize("mode", MODES)
def test_the_client_path_has_no_default_host(mode):
    server = MockServer()
    with pytest.raises(ConfigurationError) as caught:
        list_over(client_over(server, mode, api_key=FAKE_KEY, secret_key=FAKE_SECRET))
    assert caught.value.code == "missing_base_url" and server.seen == []
    assert "platform_base_url" in str(caught.value) and "OMEGA_BASE_URL" in str(caught.value)
    assert caught.value.__cause__ is None and caught.value.__context__ is None


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("given", ["base_url", "platform_base_url", "FI_BASE_URL"])
def test_a_base_url_given_to_the_client_is_a_chosen_host(mode, given, monkeypatch):
    server = MockServer()
    options = {"api_key": FAKE_KEY, "secret_key": FAKE_SECRET}
    if given == "base_url":
        options["base_url"] = "https://gw.example.test"
    elif given == "platform_base_url":
        options["platform_base_url"] = "https://gw.example.test/omega/api"
    else:
        monkeypatch.setenv("FI_BASE_URL", "https://gw.example.test")
    list_over(client_over(server, mode, **options))
    assert str(server.last.request.url) == "https://gw.example.test/omega/api/workspace/sandboxes"


def refused(request):
    raise httpx.ConnectError("refused", request=request)


@pytest.mark.parametrize("mode", MODES)
def test_an_unreachable_environment_origin_names_omega_base_url_on_every_path(env, mode, monkeypatch):
    no_backoff(monkeypatch)
    sbx = run(resolve(cls(mode).connect(SBX)))
    for name in ("sandboxes.list", "sandboxes.commands.run", "sandboxes.files.download"):
        env.on(name, refused)
    for call in (lambda: cls(mode).list(), lambda: sbx.commands.run("ls"), lambda: sbx.files.download("a")):
        with pytest.raises(SandboxConnectionError) as caught:
            run(resolve(call()))
        assert "check OMEGA_BASE_URL" in str(caught.value), str(caught.value)
        assert "FI_PLATFORM_BASE_URL" not in str(caught.value)
    run(shut(sbx))


@pytest.mark.parametrize("mode", MODES)
def test_an_unreachable_client_origin_names_the_clients_setting(mode, monkeypatch):
    no_backoff(monkeypatch)
    server = MockServer()
    server.on("sandboxes.list", refused)
    with pytest.raises(SandboxConnectionError) as caught:
        run(resolve(api(server, mode).list()))
    assert "check platform_base_url / FI_PLATFORM_BASE_URL" in str(caught.value)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("drop,check", [
    (httpx.ReadError("reset"), "list the sandboxes before repeating it"),
    (httpx.ReadTimeout("slow"), "list the sandboxes before repeating it"),
])
def test_a_dropped_create_says_what_to_check_and_never_says_retry(mode, drop, check):
    server = MockServer()

    def answer(request):
        raise type(drop)(str(drop), request=request)

    server.on("sandboxes.create", answer)
    with pytest.raises(SandboxConnectionError) as caught:
        run(resolve(api(server, mode).create(body={})))
    text = str(caught.value)
    assert "completion is unknown" in text and check in text and "retry" not in text, text
    assert len(server.seen) == 1


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("name,call", [
    ("sandboxes.list", lambda sbx: sbx._sandboxes.list()),
    ("sandboxes.files.download", lambda sbx: sbx.files.download("a")),
    ("sandboxes.commands.run", lambda sbx: sbx.commands.run("ls")),
])
def test_a_redirect_on_a_sandbox_call_never_names_its_target(mode, name, call):
    from fi import errors as fe

    server = MockServer()
    server.on(name, lambda request: httpx.Response(307, headers={"location": "https://private-host.test/x"}))
    sbx = cls(mode)(api(server, mode, retries=0), {"id": SBX, "state": "active"})
    with pytest.raises(fe.UnexpectedRedirectError) as caught:
        run(resolve(call(sbx)))
    assert caught.value.target_host is None and caught.value.status_code == 307
    assert "private-host" not in str(caught.value) and caught.value.operation == name
    assert len(server.seen) == 1
