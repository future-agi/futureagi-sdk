"""``FI_ALLOW_INSECURE_HTTP`` on every Python credential path.

Plain HTTP to a host that is not loopback is refused by default. The opt-in is exactly ``1`` (or the explicit
argument where a client offers one); it does not apply to ``futureagi.com`` or ``*.futureagi.com`` and it does not
apply when an environment proxy would route the request. With it, one notice per process names the setting and the
origin and carries no value.
"""

from __future__ import annotations

import asyncio
from functools import partial
from types import SimpleNamespace

import httpx
import pytest
from fi._core import http_security
from fi._core.http_security import (
    ALLOW_INSECURE_HTTP_ENV,
    check_http_security,
    require_secure_credentials_url,
)
from fi.errors import ConfigurationError

from tests._judged_mock_transport import JudgedMockTransport

REMOTE = "http://optin-host.test:8080"
SECRET = "key-not-a-secret"
PROXY_ENV = ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy")


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in (ALLOW_INSECURE_HTTP_ENV, *PROXY_ENV):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(http_security, "_warned", set())


def _refusal_types():
    from fi.gateway._exceptions import AgentCCError

    return (ConfigurationError, AgentCCError)


def _keys_check(url):
    check_http_security(httpx.URL(url), "keys")


def _bearer_check(url):
    check_http_security(httpx.URL(url), "bearer")


def _helper(url):
    require_secure_credentials_url(url)


def _gateway_destination(url):
    from fi.gateway._http_security import validate_destination

    validate_destination(url, url)


def _gateway_client(url, *, transport=httpx.MockTransport):
    from fi.gateway import AgentCC

    with httpx.Client(transport=transport(lambda r: httpx.Response(200, json={"object": "list", "data": []}))) as http:
        with AgentCC(api_key="sk-test-key", base_url=url, http_client=http) as client:
            client.models.list()


def _lazy_keys(url):
    from fi._http import LazyKeyAuth

    auth = LazyKeyAuth(lambda: SimpleNamespace(require=lambda: SimpleNamespace(api_key="k", secret_key="s")))
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200)), auth=auth) as http:
        http.get(url + "/x")


def _lazy_keys_explicit(url):
    from fi._http import LazyKeyAuth

    auth = LazyKeyAuth(lambda: SimpleNamespace(require=lambda: SimpleNamespace(api_key="k", secret_key="s")),
                       allow_insecure_http=True)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200)), auth=auth) as http:
        http.get(url + "/x")


def _legacy(url):
    from fi.api.auth import APIKeyAuth

    client = APIKeyAuth(fi_api_key=SECRET, fi_secret_key="secret-not-a-secret", fi_base_url=url, session=object())
    client._direct_kwargs({"url": url + "/x", "headers": {"X-Api-Key": SECRET}})


def _judge(url):
    from fi.experiments.evaluators import _judge_http

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))) as http:
            await _judge_http.post(http, url + "/v1/chat/completions", {"m": 1}, SECRET)

    asyncio.run(run())


PATHS = {
    "keys": _keys_check, "bearer": _bearer_check, "helper": _helper, "gateway-destination": _gateway_destination,
    "gateway-client": _gateway_client, "lazy-keys-env": _lazy_keys, "legacy": _legacy, "judge": _judge,
}
NAMES = list(PATHS)
JUDGED_PATHS = {**PATHS, "gateway-client": partial(_gateway_client, transport=JudgedMockTransport)}


def _refused(call, url=REMOTE):
    with pytest.raises(_refusal_types()) as caught:
        call(url)
    assert ALLOW_INSECURE_HTTP_ENV in str(caught.value) or "allow_insecure_http" in str(caught.value)
    return str(caught.value)


@pytest.mark.parametrize("name", NAMES)
def test_refused_by_default(name):
    _refused(JUDGED_PATHS[name])


@pytest.mark.parametrize("name", NAMES)
def test_allowed_with_the_opt_in(name, monkeypatch):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    JUDGED_PATHS[name](REMOTE)


@pytest.mark.parametrize("value", ["true", "yes", "TRUE", "on", " 1", "1 ", "2", "0", ""])
@pytest.mark.parametrize("name", ["keys", "helper", "gateway-destination", "legacy"])
def test_only_exactly_one_is_the_opt_in(name, value, monkeypatch):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, value)
    _refused(PATHS[name])


@pytest.mark.parametrize("host", ["futureagi.com", "api.futureagi.com", "App.FutureAGI.com", "api.futureagi.com."])
@pytest.mark.parametrize("name", NAMES)
def test_refused_for_a_future_agi_host_with_the_opt_in_on(name, host, monkeypatch):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    message = _refused(JUDGED_PATHS[name], f"http://{host}")
    assert "Future AGI" in message
    assert http_security._warned == set()


def test_a_look_alike_domain_is_not_a_future_agi_host(monkeypatch):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    require_secure_credentials_url("http://notfutureagi.com")
    require_secure_credentials_url("http://futureagi.com.example.test")


#: The paths whose request the SDK sends itself on a plain-http transport that reads no proxy variable.
SENT_DIRECT = ["gateway-destination", "gateway-client", "legacy"]


@pytest.mark.parametrize("proxy_name", ["HTTP_PROXY", "http_proxy", "ALL_PROXY"])
@pytest.mark.parametrize("name", [n for n in NAMES if n not in SENT_DIRECT])
def test_refused_through_an_environment_proxy_with_the_opt_in_on(name, proxy_name, monkeypatch):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    monkeypatch.setenv(proxy_name, "http://proxy.test:3128")
    message = _refused(PATHS[name])
    assert "proxy" in message
    assert http_security._warned == set()


@pytest.mark.parametrize("proxy_name", ["HTTP_PROXY", "http_proxy", "ALL_PROXY"])
@pytest.mark.parametrize("name", SENT_DIRECT)
def test_allowed_with_the_opt_in_whatever_the_proxy_variables_say_when_the_sdk_sends_direct(name, proxy_name, monkeypatch):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    monkeypatch.setenv(proxy_name, "http://proxy.test:3128")
    JUDGED_PATHS[name](REMOTE)


def test_a_no_proxy_entry_keeps_the_route_direct(monkeypatch):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.test:3128")
    monkeypatch.setenv("NO_PROXY", "optin-host.test")
    require_secure_credentials_url(REMOTE)


def test_a_proxy_does_not_change_the_loopback_or_https_answers(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.test:3128")
    require_secure_credentials_url("http://127.0.0.1:8080")
    require_secure_credentials_url("https://optin-host.test")


def test_an_explicit_argument_is_honoured_on_the_generated_client_keys_path():
    _lazy_keys_explicit(REMOTE)
    with pytest.raises(ConfigurationError):
        _lazy_keys_explicit("http://api.futureagi.com")


def test_the_explicit_argument_does_not_override_a_proxy(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.test:3128")
    with pytest.raises(ConfigurationError):
        _lazy_keys_explicit(REMOTE)


def test_one_value_free_notice_per_process_names_the_setting_and_the_origin(monkeypatch, capsys):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    for path in ("keys", "bearer", "helper", "gateway-destination", "gateway-client", "legacy", "judge"):
        for url in (REMOTE, REMOTE, "http://second-host.test:9000"):
            PATHS[path](url)
    err = capsys.readouterr().err
    lines = [line for line in err.splitlines() if ALLOW_INSECURE_HTTP_ENV in line]
    assert len(lines) == 1 and len(err.splitlines()) == 1
    assert "http://optin-host.test:8080" in lines[0]
    for value in (SECRET, "secret-not-a-secret", "sk-test-key", "/x", "/v1"):
        assert value not in lines[0]


def test_no_notice_without_the_opt_in_and_none_for_loopback(monkeypatch, capsys):
    require_secure_credentials_url("http://127.0.0.1:8080")
    require_secure_credentials_url("https://optin-host.test")
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    require_secure_credentials_url("http://localhost:8080")
    assert capsys.readouterr().err == ""


def test_the_gateway_client_warns_once_across_clients(monkeypatch, capsys, recwarn):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    for _ in range(3):
        JUDGED_PATHS["gateway-client"](REMOTE)
    assert capsys.readouterr().err.count(ALLOW_INSECURE_HTTP_ENV) == 1
    assert [w for w in recwarn.list if "FI_ALLOW" in str(w.message)] == []
