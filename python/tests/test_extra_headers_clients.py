"""FI_EXTRA_HEADERS in the typed clients and the requests-based HttpClient (fi.api.auth, fi.kb), no network."""

from __future__ import annotations

import pytest

from fi._extra_headers import ENV_VAR, ExtraHeadersError

# a made-up value, low entropy on purpose (never a real token)
TOKEN = "fake-identity-token-" + "x" * 12
VALUE = f"Bearer {TOKEN}"


@pytest.fixture(autouse=True)
def _no_setting(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)


def test_futureagi_clients_take_extra_headers_and_check_them(monkeypatch):
    from fi.futureagi_async_client import AsyncFutureAGIClient
    from fi.futureagi_client import FutureAGIClient

    client = FutureAGIClient(base_url="http://platform.test", extra_headers={"X-Team": "t"})
    assert client._auth.extra is client._extra_headers
    assert client._extra_headers.for_url("http://platform.test/x") == {"X-Team": "t"}
    assert client._extra_headers.for_url("http://other.test/x") == {}
    aclient = AsyncFutureAGIClient(base_url="http://platform.test", extra_headers="X-Team=a")
    assert aclient._auth.extra.for_url("http://platform.test/x") == {"X-Team": "a"}
    with pytest.raises(ExtraHeadersError, match="X-Secret-Key"):
        FutureAGIClient(base_url="http://platform.test", extra_headers={"X-Secret-Key": "s"})
    monkeypatch.setenv(ENV_VAR, "not valid")
    FutureAGIClient(base_url="http://platform.test")  # building never raises for the setting; a request does


def test_http_client_platform_headers_and_default_headers_no_longer_collide(monkeypatch):
    from fi.api.auth import APIKeyAuth

    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization={VALUE}")
    client = APIKeyAuth(fi_api_key="ak", fi_secret_key="sk", fi_base_url="http://platform.test",
                        default_headers={"X-Caller": "c", "X-Api-Key": "caller-tries"}, extra_headers={"X-Team": "t"})
    assert client._default_headers == {"X-Caller": "c", "X-Api-Key": "ak", "X-Secret-Key": "sk"}
    on = client._platform_headers("http://platform.test/model-hub/x", {"Accept": "a"})
    assert on == {"Accept": "a", "Proxy-Authorization": VALUE, "X-Team": "t"}
    assert client._platform_headers("http://other.test/x", {"Accept": "a"}) == {"Accept": "a"}
    kwargs = client._direct_kwargs({"url": "http://platform.test/kb/", "headers": {"A": "1"}})
    assert kwargs["headers"]["Proxy-Authorization"] == VALUE and kwargs["allow_redirects"] is False
    kwargs = client._direct_kwargs({"url": "http://other.test/kb/", "headers": {"A": "1"}})
    assert "Proxy-Authorization" not in kwargs["headers"] and "allow_redirects" not in kwargs
    client.close()


def test_http_client_redirect_guard(monkeypatch):
    import requests

    from fi.api.auth import HttpClient

    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization={VALUE};X-Team=t")
    session = requests.Session()
    HttpClient(base_url="http://platform.test/api", session=session)

    def redirected(url):
        # what requests hands rebuild_auth on a redirect: the old headers, Proxy-Authorization already
        # dropped by rebuild_proxies (it does that on every redirect, even to the same host)
        prepared = requests.Request("GET", url, headers={"X-Team": "t", "Accept": "a"}).prepare()
        response = requests.Response()
        response.request = requests.Request("GET", "http://platform.test/api/start").prepare()
        session.rebuild_auth(prepared, response)
        return prepared.headers

    same = redirected("http://platform.test/api/next")
    assert same["Proxy-Authorization"] == VALUE and same["X-Team"] == "t"
    off = redirected("http://elsewhere.test/api/next")
    assert "Proxy-Authorization" not in off and "X-Team" not in off
    session.close()
