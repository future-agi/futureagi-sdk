"""A sandbox call to a plain-http host that is not loopback is refused with insecure_sandbox_origin on every
path (client, async client, environment classes, command line), whatever FI_ALLOW_INSECURE_HTTP says and with
or without proxy variables. Nothing is sent. Fake credentials only."""

from __future__ import annotations

import asyncio

import pytest
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.sandbox import AsyncSandbox, ConfigurationError, Sandbox

from ._sandbox_cli_support import (  # noqa: F401 (registers the fixture)
    ENV,
    SECRETS,
    run,
    server_fixture,
)
from ._sandbox_mock import FAKE_KEY, FAKE_SECRET, FAKE_TOKEN

URL = "http://sbx.example.test:8080/omega/api"
PROXY = "http://127.0.0.1:9"
PROXY_NAMES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
OPT_INS = (None, "1", "true", "")
PROXIES = (False, True)


@pytest.fixture
def settings(server, monkeypatch):
    def apply(opt_in, proxied):
        for name in ENV:
            monkeypatch.delenv(name, raising=False)
        for name in PROXY_NAMES:
            monkeypatch.delenv(name, raising=False)
        if proxied:
            for name in PROXY_NAMES[:3]:
                monkeypatch.setenv(name, PROXY)
        if opt_in is not None:
            monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", opt_in)

    return apply


def _client(**kw):
    return FutureAGIClient(api_key=FAKE_KEY, secret_key=FAKE_SECRET, **kw)


def _aclient(**kw):
    return AsyncFutureAGIClient(api_key=FAKE_KEY, secret_key=FAKE_SECRET, **kw)


def _sync(kw):
    return lambda: _client(**kw).sandboxes.list()


def _async(kw):
    return lambda: asyncio.run(_aclient(**kw).sandboxes.list())


def _env_class(monkeypatch, call):
    monkeypatch.setenv("OMEGA_BASE_URL", URL)
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    return call


CLIENT_ARGS = [{"base_url": URL}, {"platform_base_url": URL}, {"base_url": URL, "allow_insecure_http": True},
               {"platform_base_url": URL, "platform_token": None, "allow_insecure_http": False}]


@pytest.mark.parametrize("proxied", PROXIES)
@pytest.mark.parametrize("opt_in", OPT_INS)
@pytest.mark.parametrize("kw", range(len(CLIENT_ARGS)))
@pytest.mark.parametrize("make", [_sync, _async], ids=["client", "async client"])
def test_a_client_sandbox_call_refuses_plain_http_off_loopback(settings, server, make, kw, opt_in, proxied):
    settings(opt_in, proxied)
    with pytest.raises(ConfigurationError) as caught:
        make(CLIENT_ARGS[kw])()
    assert caught.value.code == "insecure_sandbox_origin", str(caught.value)
    assert server.seen == []
    assert not any(secret in str(caught.value) for secret in SECRETS)


@pytest.mark.parametrize("proxied", PROXIES)
@pytest.mark.parametrize("opt_in", OPT_INS)
@pytest.mark.parametrize("cls", [Sandbox, AsyncSandbox])
def test_an_environment_sandbox_call_refuses_plain_http_off_loopback(settings, monkeypatch, cls, opt_in, proxied):
    settings(opt_in, proxied)
    monkeypatch.setenv("OMEGA_BASE_URL", URL)
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    with pytest.raises(ConfigurationError) as caught:
        result = cls.list()
        if asyncio.iscoroutine(result):
            asyncio.run(result)
    assert caught.value.code == "insecure_sandbox_origin", str(caught.value)


@pytest.mark.parametrize("proxied", PROXIES)
@pytest.mark.parametrize("opt_in", OPT_INS)
@pytest.mark.parametrize("auth", ["keys", "token"])
@pytest.mark.parametrize("command", [("list",), ("mcp",)])
def test_the_command_line_refuses_plain_http_off_loopback(settings, server, monkeypatch, capsys, command, auth, opt_in, proxied):
    settings(opt_in, proxied)
    if auth == "keys":
        monkeypatch.delenv("FUTUREAGI_OMEGA_API_KEY", raising=False)
        monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
        monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    else:
        monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", FAKE_TOKEN)
    monkeypatch.delenv("OMEGA_BASE_URL", raising=False)
    assert run("--base-url", URL, "--allow-custom-base-url", *command) == 2
    err = capsys.readouterr().err
    assert err.startswith("insecure_sandbox_origin: "), err
    assert server.seen == []
