"""The Future AGI Cloud key pair on the environment path (sync and async) goes only where the core's host
guard sends keys: HTTPS in the Future AGI zone, or loopback exactly as the core reads it. Another
host is refused before any request (the transport mock sees nothing), naming only host[:port],
unless FI_ALLOW_CUSTOM_PLATFORM_URL (parsed by the core's own reader) or the explicit
allow_custom_base_url allows it; then the core prints its one-time notice. The client path applies
the same core guard. Fake credentials only."""

from __future__ import annotations

import httpx
import pytest
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi._core import origins
from fi.sandbox import AsyncSandbox, ConfigurationError, Sandbox, _connection
from fi.sandbox._connection import SandboxConnection, resolve_origin

from ._sandbox_mock import (
    FAKE_KEY,
    FAKE_SECRET,
    FAKE_TOKEN,
    HOSTED,
    MODES,
    SBX,
    MockServer,
    resolve,
    run,
)

ENV = ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
       "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID", "FI_ALLOW_INSECURE_HTTP", "FI_BASE_URL",
       "FI_PLATFORM_BASE_URL", "FI_PLATFORM_TOKEN", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_EXTRA_HEADERS")
OTHER_ORIGIN = "https://other-origin.example/omega/api"
NOTICE = "futureagi: sending your keys to other-origin.example, outside the Future AGI zone"
SECRETS = (FAKE_KEY, FAKE_SECRET, FAKE_TOKEN)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(origins, "_warned", set())  # each test sees the one-time notice afresh


@pytest.fixture
def server(monkeypatch):
    mock = MockServer()
    monkeypatch.setattr(_connection, "default_transport", mock.transport)
    return mock


def cls(mode):
    return AsyncSandbox if mode == "async" else Sandbox


def keys(monkeypatch, base, **extra):
    monkeypatch.setenv("OMEGA_BASE_URL", base)
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    for name, value in extra.items():
        monkeypatch.setenv(name, value)


def environ(base, **extra):
    return {"OMEGA_BASE_URL": base, "FI_API_KEY": FAKE_KEY, "FI_SECRET_KEY": FAKE_SECRET, **extra}


def assert_private(text):
    assert not any(secret in text for secret in SECRETS)
    assert "/omega/api" not in text


@pytest.mark.parametrize("mode", MODES)
def test_keys_to_a_host_outside_the_zone_are_refused_before_any_request(mode, server, monkeypatch, capsys):
    keys(monkeypatch, OTHER_ORIGIN)
    for call in (lambda: cls(mode).list(), lambda: cls(mode).create(name="n"), lambda: cls(mode).connect(SBX),
                 lambda: cls(mode).settings()):
        with pytest.raises(ConfigurationError) as caught:
            run(resolve(call()))
        error = caught.value
        assert error.code == "custom_base_url_not_allowed" and server.seen == []
        assert "other-origin.example" in str(error) and "FI_ALLOW_CUSTOM_PLATFORM_URL=1" in str(error)
        assert "FUTUREAGI_OMEGA_API_KEY" in str(error) and "Future AGI hosts" in str(error)
        assert error.__cause__ is None and error.__context__ is None
        assert_private(str(error) + repr(error))
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("base", [
    "https://other-origin.example", "https://futureagi.com.other-origin.example/omega/api",
    "https://otherfutureagi.com/omega/api", "https://other-origin.example:8443/omega/api",
    "https://futureagi.co/omega/api",
])
def test_every_host_the_core_guard_refuses_is_refused_here(base):
    with pytest.raises(ConfigurationError) as caught:
        resolve_origin(environ(base))
    assert caught.value.code == "custom_base_url_not_allowed"
    assert origins.display_host(httpx.URL(base)) in str(caught.value)
    assert not origins.host_allowed(httpx.URL(base))  # the very check the core applies


@pytest.mark.parametrize("base", [
    HOSTED, "https://futureagi.com/omega/api", "https://API.FutureAGI.com./omega/api",
    "https://sbx.futureagi.com:8443/omega/api", "http://127.0.0.1:8787", "http://localhost:8787",
    "http://[::1]:8787", "https://localhost:8443",
])
def test_a_future_agi_host_and_loopback_take_the_keys_without_a_notice(base, capsys):
    found = resolve_origin(environ(base))
    assert found.mode == "keys" and not found.custom
    assert found.headers["X-Api-Key"] == FAKE_KEY
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("mode", MODES)
def test_a_future_agi_host_and_loopback_work_end_to_end(mode, server, monkeypatch):
    for base in (HOSTED, "http://127.0.0.1:8787"):
        keys(monkeypatch, base)
        run(resolve(cls(mode).list()))
        assert str(server.last.request.url).startswith(base + "/workspace/sandboxes")
        assert server.last.request.headers["x-api-key"] == FAKE_KEY
    assert len(server.seen) == 2


@pytest.mark.parametrize("mode", MODES)
def test_plain_http_to_a_future_agi_host_is_the_sandbox_refusal(mode, server, monkeypatch):
    keys(monkeypatch, "http://sbx.futureagi.com/omega/api", FI_ALLOW_CUSTOM_PLATFORM_URL="1")
    with pytest.raises(ConfigurationError) as caught:
        run(resolve(cls(mode).list()))
    assert caught.value.code == "insecure_sandbox_origin" and server.seen == []


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", " Yes ", "0", "false", "no", "on", "", "2"])
def test_the_environment_opt_in_is_read_exactly_as_the_core_reads_it(value):
    env = environ(OTHER_ORIGIN, FI_ALLOW_CUSTOM_PLATFORM_URL=value)
    core_allows = origins._allow_flag(None, env)
    if core_allows:
        assert resolve_origin(env).custom is True
    else:
        with pytest.raises(ConfigurationError) as caught:
            resolve_origin(env)
        assert caught.value.code == "custom_base_url_not_allowed"
    assert core_allows == (value.strip().lower() in ("1", "true", "yes"))


@pytest.mark.parametrize("mode", MODES)
def test_the_environment_opt_in_sends_the_keys_and_prints_the_core_notice_once(mode, server, monkeypatch, capsys):
    keys(monkeypatch, OTHER_ORIGIN, FI_ALLOW_CUSTOM_PLATFORM_URL="1")
    run(resolve(cls(mode).list()))
    run(resolve(cls(mode).connect(SBX)))
    assert [str(seen.request.url).split("/omega/api")[0] for seen in server.seen] == ["https://other-origin.example"] * 2
    assert server.last.request.headers["x-api-key"] == FAKE_KEY
    err = capsys.readouterr().err
    assert err.count(NOTICE) == 1 and "FI_ALLOW_CUSTOM_PLATFORM_URL" in err
    assert_private(err)


def test_the_explicit_argument_allows_another_host_and_prints_the_notice_once(capsys):
    env = environ(OTHER_ORIGIN)
    first = resolve_origin(env, allow_custom_base_url=True)
    second = SandboxConnection(environ=env, allow_custom_base_url=True).core().shared.origin()
    assert first.custom and second.custom and first.base == "https://other-origin.example/omega/api"
    assert capsys.readouterr().err.count(NOTICE) == 1


def test_an_explicit_refusal_wins_over_the_environment_opt_in():
    env = environ(OTHER_ORIGIN, FI_ALLOW_CUSTOM_PLATFORM_URL="1")
    with pytest.raises(ConfigurationError) as caught:
        resolve_origin(env, allow_custom_base_url=False)
    assert caught.value.code == "custom_base_url_not_allowed"


def test_loopback_follows_the_one_rule_in_the_core_guard_and_the_http_policy(capsys):
    """127.0.0.2 is loopback to the plain-HTTP rule and to the core's host guard alike, so it needs no opt-in
    and gets neither a custom-host notice nor a plain-HTTP warning."""
    origin = resolve_origin(environ("http://127.0.0.2:8787"))
    assert origin.custom is False
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("mode", MODES)
def test_a_self_host_token_is_not_opened_by_the_keys_opt_in(mode, server, monkeypatch):
    monkeypatch.setenv("OMEGA_BASE_URL", OTHER_ORIGIN)
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", FAKE_TOKEN)
    monkeypatch.setenv("FI_ALLOW_CUSTOM_PLATFORM_URL", "1")
    with pytest.raises(ConfigurationError) as caught:
        run(resolve(cls(mode).list()))
    assert caught.value.code == "custom_base_url_not_allowed" and server.seen == []
    assert "Bearer" in str(caught.value)


def client_over(server, mode, **options):
    client = (AsyncFutureAGIClient if mode == "async" else FutureAGIClient)(retries=0, **options)
    shared = client._platform.shared
    shared._recorder._inner = httpx.MockTransport(server.handler)
    shared._recorder._inner_async = httpx.MockTransport(server.handler)
    return client


async def finish(client):
    await resolve(client.aclose() if isinstance(client, AsyncFutureAGIClient) else client.close())


@pytest.mark.parametrize("mode", MODES)
def test_the_client_path_keeps_the_core_guard(mode, monkeypatch, tmp_path):
    """The core guard accepts keys and origin supplied together as arguments, but rejects environment
    keys paired with an origin argument outside the zone."""
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "no-login.json"))
    server = MockServer()
    both = client_over(server, mode, api_key=FAKE_KEY, secret_key=FAKE_SECRET, platform_base_url=OTHER_ORIGIN)
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    mixed = client_over(server, mode, platform_base_url=OTHER_ORIGIN)

    async def go():
        try:
            await resolve(both.sandboxes.list())
            with pytest.raises(ConfigurationError) as caught:
                await resolve(mixed.sandboxes.list())
            return caught.value
        finally:
            await finish(both)
            await finish(mixed)

    error = run(go())
    assert [seen.name for seen in server.seen] == ["sandboxes.list"]
    assert error.code == "host_not_allowed" and "allow_custom_platform_url" in str(error)
