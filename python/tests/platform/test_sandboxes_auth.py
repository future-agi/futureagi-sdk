"""Contract section 2 with v2 items 1-2 (sync and async): the handle's classmethods read the
environment only, scope headers depend on the mode, never both credential modes, the origin rule
(no plain HTTP off loopback; a foreign self-host needs the constructor-only allow_custom_base_url),
the explicit client path, and no key in any repr or error."""

from __future__ import annotations

import inspect

import httpx
import pytest
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.sandbox import AsyncSandbox, ConfigurationError, Sandbox, _connection
from fi.sandbox._connection import resolve_origin

from ._sandbox_mock import (
    FAKE_KEY,
    FAKE_SECRET,
    FAKE_TOKEN,
    HOSTED,
    MODES,
    ORIGIN,
    SBX,
    MockServer,
    resolve,
    run,
)

ENV = ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
       "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID", "FI_ALLOW_INSECURE_HTTP", "FI_BASE_URL",
       "FI_PLATFORM_BASE_URL", "FI_PLATFORM_TOKEN", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_EXTRA_HEADERS")
LOCAL = "http://127.0.0.1:8787"
SECRETS = (FAKE_KEY, FAKE_SECRET, FAKE_TOKEN)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def server(monkeypatch):
    mock = MockServer()
    monkeypatch.setattr(_connection, "default_transport", mock.transport)
    return mock


def cls(mode):
    return AsyncSandbox if mode == "async" else Sandbox


def env(monkeypatch, **values):
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def keys(monkeypatch, base=HOSTED):
    env(monkeypatch, OMEGA_BASE_URL=base, FI_API_KEY=FAKE_KEY, FI_SECRET_KEY=FAKE_SECRET)


def assert_no_secret(error):
    text = str(error) + repr(error)
    assert not any(secret in text for secret in SECRETS)


@pytest.mark.parametrize("mode", MODES)
def test_classmethods_take_no_credential_or_origin_arguments(mode):
    banned = {"base_url", "api_key", "secret_key", "bearer_token", "workspace", "organization",
              "allow_insecure_http", "allow_custom_base_url"}
    for name in ("create", "connect", "list", "settings"):
        params = set(inspect.signature(getattr(cls(mode), name)).parameters)
        assert not params & banned, (name, params & banned)
    with pytest.raises(TypeError):
        run(resolve(cls(mode).list(base_url=ORIGIN)))


@pytest.mark.parametrize("mode", MODES)
def test_hosted_keys_and_scope_from_the_environment(mode, server, monkeypatch):
    keys(monkeypatch)
    env(monkeypatch, FI_WORKSPACE_ID="ws_1", FI_ORGANIZATION_ID="org_1", OMEGA_OS_API_KEY="fake-operator-key-0009")
    sbx = run(resolve(cls(mode).create(name="n")))
    assert sbx.id == SBX and server.last.json() == {"name": "n"}
    headers = server.last.request.headers
    assert headers["x-api-key"] == FAKE_KEY and headers["x-secret-key"] == FAKE_SECRET
    assert headers["x-workspace-id"] == "ws_1" and headers["x-organization-id"] == "org_1"
    assert "x-omega-workspace" not in headers and "x-omega-org" not in headers
    assert "authorization" not in headers
    assert "fake-operator-key-0009" not in str(server.last.request.headers.raw)
    assert str(server.last.request.url).startswith(HOSTED + "/workspace/sandboxes")


@pytest.mark.parametrize("mode", MODES)
def test_self_host_bearer_and_scope_from_the_environment(mode, server, monkeypatch):
    env(monkeypatch, OMEGA_BASE_URL=LOCAL, FUTUREAGI_OMEGA_API_KEY=FAKE_TOKEN,
        FI_WORKSPACE_ID="ws_2", FI_ORGANIZATION_ID="org_2")
    sbx = run(resolve(cls(mode).connect(SBX)))
    assert sbx.id == SBX
    headers = server.last.request.headers
    assert headers["authorization"] == f"Bearer {FAKE_TOKEN}"
    assert headers["x-omega-workspace"] == "ws_2" and headers["x-omega-org"] == "org_2"
    assert "x-workspace-id" not in headers and "x-organization-id" not in headers
    assert "x-api-key" not in headers and "x-secret-key" not in headers
    assert str(server.last.request.url) == f"{LOCAL}/workspace/sandboxes/{SBX}"


@pytest.mark.parametrize("mode", MODES)
def test_no_scope_header_when_none_is_set(mode, server, monkeypatch):
    keys(monkeypatch)
    run(resolve(cls(mode).list()))
    sent = {name.lower() for name in server.last.request.headers}
    assert not sent & {"x-workspace-id", "x-organization-id", "x-omega-workspace", "x-omega-org"}


@pytest.mark.parametrize("mode", MODES)
def test_both_credential_modes_is_a_configuration_error(mode, server, monkeypatch):
    keys(monkeypatch)
    env(monkeypatch, FUTUREAGI_OMEGA_API_KEY=FAKE_TOKEN)
    with pytest.raises(ConfigurationError) as caught:
        run(resolve(cls(mode).create()))
    assert caught.value.code == "mixed_credentials" and server.seen == []
    assert "FUTUREAGI_OMEGA_API_KEY" in str(caught.value)
    assert_no_secret(caught.value)


@pytest.mark.parametrize("environ", [
    {"FUTUREAGI_OMEGA_API_KEY": FAKE_TOKEN, "FI_API_KEY": FAKE_KEY},
    {"FUTUREAGI_OMEGA_API_KEY": FAKE_TOKEN, "FI_SECRET_KEY": FAKE_SECRET},
])
def test_a_half_key_pair_beside_a_token_is_still_both_modes(environ):
    with pytest.raises(ConfigurationError) as caught:
        resolve_origin({"OMEGA_BASE_URL": ORIGIN, **environ})
    assert caught.value.code == "mixed_credentials"


@pytest.mark.parametrize("mode", MODES)
def test_no_base_url_names_omega_base_url_and_sends_nothing(mode, server, monkeypatch):
    env(monkeypatch, FI_API_KEY=FAKE_KEY, FI_SECRET_KEY=FAKE_SECRET, FI_BASE_URL="https://api.futureagi.com")
    with pytest.raises(ConfigurationError, match="OMEGA_BASE_URL") as caught:
        run(resolve(cls(mode).create()))
    assert caught.value.code == "missing_base_url" and server.seen == []


@pytest.mark.parametrize("environ,missing", [
    ({}, ("FI_API_KEY", "FI_SECRET_KEY")),
    ({"FI_API_KEY": FAKE_KEY}, ("FI_SECRET_KEY",)),
])
def test_a_missing_or_half_key_pair_names_what_is_missing(environ, missing):
    with pytest.raises(ConfigurationError) as caught:
        resolve_origin({"OMEGA_BASE_URL": ORIGIN, **environ})
    assert caught.value.code == "missing_credentials"
    assert all(name in str(caught.value) for name in missing) and FAKE_KEY not in str(caught.value)


@pytest.mark.parametrize("raw", ["ftp://host", "https://user:pw@host", "https://host/?q=1", "not a url"])
def test_a_bad_base_url_is_refused(raw):
    with pytest.raises(ConfigurationError, match="OMEGA_BASE_URL") as caught:
        resolve_origin({"OMEGA_BASE_URL": raw, "FUTUREAGI_OMEGA_API_KEY": FAKE_TOKEN})
    assert caught.value.code == "invalid_base_url"


@pytest.mark.parametrize("mode", MODES)
def test_the_environment_never_allows_a_foreign_self_host(mode, server, monkeypatch):
    env(monkeypatch, OMEGA_BASE_URL="https://ee.internal:8443", FUTUREAGI_OMEGA_API_KEY=FAKE_TOKEN,
        FI_ALLOW_CUSTOM_PLATFORM_URL="1", FI_ALLOW_INSECURE_HTTP="1")
    with pytest.raises(ConfigurationError) as caught:
        run(resolve(cls(mode).list()))
    assert caught.value.code == "custom_base_url_not_allowed" and server.seen == []
    assert "allow_custom_base_url=True" in str(caught.value) and "ee.internal" in str(caught.value)
    assert caught.value.__cause__ is None and caught.value.__context__ is None
    assert_no_secret(caught.value)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("auth", ["keys", "bearer"])
def test_plain_http_off_loopback_is_refused_whatever_the_flags(mode, auth, server, monkeypatch):
    base = "http://ee.internal:8080"
    if auth == "keys":
        keys(monkeypatch, base)
    else:
        env(monkeypatch, OMEGA_BASE_URL=base, FUTUREAGI_OMEGA_API_KEY=FAKE_TOKEN)
    env(monkeypatch, FI_ALLOW_INSECURE_HTTP="1")
    with pytest.raises(ConfigurationError) as caught:
        run(resolve(cls(mode).list()))
    assert caught.value.code == "insecure_sandbox_origin" and server.seen == []


def test_the_origin_carries_its_secrets_for_scrubbing_and_hides_them_from_repr():
    found = resolve_origin({"OMEGA_BASE_URL": HOSTED + "/", "FI_API_KEY": FAKE_KEY, "FI_SECRET_KEY": FAKE_SECRET})
    assert found.base == HOSTED and found.mode == "keys" and set(found.secrets) == {FAKE_KEY, FAKE_SECRET}
    assert not any(secret in repr(found) for secret in SECRETS)


@pytest.mark.parametrize("mode", MODES)
def test_a_handle_repr_shows_only_id_and_state(mode, server, monkeypatch):
    keys(monkeypatch)
    sbx = run(resolve(cls(mode).connect(SBX)))
    assert repr(sbx) == f"{cls(mode).__name__}(id={SBX!r}, state='active')"


def client_over(server, mode, **options):
    """A real FutureAGIClient / AsyncFutureAGIClient whose platform HTTP boundary is the mock."""
    client = (AsyncFutureAGIClient if mode == "async" else FutureAGIClient)(retries=0, **options)
    shared = client._platform.shared
    shared._recorder._inner = httpx.MockTransport(server.handler)
    shared._recorder._inner_async = httpx.MockTransport(server.handler)
    return client


async def finish(client):
    await resolve(client.aclose() if isinstance(client, AsyncFutureAGIClient) else client.close())


@pytest.mark.parametrize("mode", MODES)
def test_the_client_path_sends_hosted_scope_and_returns_the_handle(mode):
    server = MockServer()
    client = client_over(server, mode, api_key=FAKE_KEY, secret_key=FAKE_SECRET, base_url="http://127.0.0.1:9",
                         workspace_id="ws_3", organization_id="org_3")

    async def go():
        try:
            sbx = await resolve(client.sandboxes.create(body={"name": "n"}))
            again = await resolve(client.sandboxes.connect(SBX))
            return sbx, again
        finally:
            await finish(client)

    sbx, again = run(go())
    assert type(sbx) is type(again) is cls(mode) and sbx.id == again.id == SBX
    headers = server.seen[0].request.headers
    assert headers["x-api-key"] == FAKE_KEY and headers["x-workspace-id"] == "ws_3"
    assert headers["x-organization-id"] == "org_3" and "x-omega-workspace" not in headers
    assert [s.name for s in server.seen] == ["sandboxes.create", "sandboxes.getInfo"]


@pytest.mark.parametrize("mode", MODES)
def test_the_client_path_sends_self_host_scope(mode):
    server = MockServer()
    client = client_over(server, mode, platform_token=FAKE_TOKEN, platform_base_url=LOCAL,
                         workspace_id="ws_4", organization_id="org_4")

    async def go():
        try:
            await resolve(client.sandboxes.list())
        finally:
            await finish(client)

    run(go())
    headers = server.last.request.headers
    assert headers["authorization"] == f"Bearer {FAKE_TOKEN}"
    assert headers["x-omega-workspace"] == "ws_4" and headers["x-omega-org"] == "org_4"
    assert "x-workspace-id" not in headers and "x-api-key" not in headers


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("allowed", [False, True])
def test_a_foreign_self_host_needs_the_constructor_only_flag(mode, allowed):
    server = MockServer()
    client = client_over(server, mode, platform_token=FAKE_TOKEN, platform_base_url="https://ee.example.test",
                         allow_custom_base_url=allowed)

    async def go():
        try:
            await resolve(client.sandboxes.list())
            await resolve(client.with_options(retries=0).sandboxes.list())
        finally:
            await finish(client)

    if allowed:
        run(go())
        assert [s.name for s in server.seen] == ["sandboxes.list", "sandboxes.list"]
        return
    with pytest.raises(ConfigurationError) as caught:
        run(go())
    assert caught.value.code == "custom_base_url_not_allowed" and server.seen == []
    assert caught.value.__cause__ is None and caught.value.__context__ is None
    assert_no_secret(caught.value)
