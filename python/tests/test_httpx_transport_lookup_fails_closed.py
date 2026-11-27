"""How a caller's ``httpx`` client is judged when its transport lookup cannot be read.

``fi.platform`` and ``fi.gateway`` read the transport a caller's ``httpx`` client selects for a URL, through the
client's ``_transport_for_url``, to tell a direct transport from a proxied one. When that lookup is missing,
raises, or returns something that is not an ``httpx`` transport, or when an ``httpx.HTTPTransport`` holds no
connection pool, a keyed plain-``http://`` request to a loopback listener is refused with the code
``insecure_http_origin`` and makes no connection. A pin case checks that, for the ``httpx`` installed, a client
built with an environment proxy is read as proxied.
"""

from __future__ import annotations

import httpx
import pytest

from fi.gateway import AgentCCError, Gateway
from fi.platform import Client
from fi.utils import _http_guard as _guard
from tests.test_plain_http_key_guards import KEY, SECRET, _attempt, net, refused  # noqa: F401


class _NoLookup(httpx.Client):
    """An ``httpx.Client`` on which ``_transport_for_url`` cannot be read."""

    def __getattribute__(self, name):
        if name == "_transport_for_url":
            raise AttributeError(name)
        return super().__getattribute__(name)


def _raising(url):
    raise RuntimeError("lookup failed")


LOOKUPS = {
    "missing": None,
    "raises": _raising,
    "returns-none": lambda url: None,
    "returns-object": lambda url: object(),
    "returns-a-string": lambda url: "http://127.0.0.1:9",
}


def _client(name: str) -> httpx.Client:
    if name == "missing":
        return _NoLookup()
    client = httpx.Client()
    client._transport_for_url = LOOKUPS[name]
    return client


def _send(sender: str, base: str, http_client: httpx.Client):
    if sender == "platform":
        client = Client(api_key=KEY, secret_key=SECRET, base_url=base, max_retries=0, timeout=3, http_client=http_client)
        return _attempt(lambda: client.request("GET", "/v1/ping", unwrap=None))
    gw = Gateway(api_key=KEY, base_url=base, max_retries=0, timeout=3, http_client=http_client)
    return _attempt(lambda: gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}]))


ERRORS = {"platform": ValueError, "gateway": AgentCCError}


@pytest.mark.parametrize("lookup", list(LOOKUPS))
@pytest.mark.parametrize("sender", list(ERRORS))
def test_keyed_loopback_request_is_refused_when_the_transport_lookup_cannot_be_read(net, sender, lookup):  # noqa: F811
    exc = _send(sender, f"http://127.0.0.1:{net.target.port}", _client(lookup))
    net.nothing_sent()
    refused(exc, ERRORS[sender])


@pytest.mark.parametrize("transport_class", [httpx.HTTPTransport])
@pytest.mark.parametrize("sender", list(ERRORS))
def test_keyed_loopback_request_is_refused_when_an_http_transport_holds_no_pool(net, sender, transport_class):  # noqa: F811
    transport = transport_class()
    del transport._pool
    exc = _send(sender, f"http://127.0.0.1:{net.target.port}", httpx.Client(transport=transport))
    net.nothing_sent()
    refused(exc, ERRORS[sender])


def test_lookup_of_the_installed_httpx_reads_an_environment_proxy_as_proxied(monkeypatch, net):  # noqa: F811
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{net.proxy.port}")
    url = "http://plain.example.test/v1/ping"
    with_proxy = httpx.Client(trust_env=True)
    without_proxy = httpx.Client(trust_env=False)
    version = httpx.__version__
    assert callable(getattr(httpx.Client, "_transport_for_url", None)), version
    assert _guard.httpx_client_may_use_proxy(with_proxy, url) is True, version
    assert _guard.httpx_client_may_use_proxy(without_proxy, url) is False, version
    exc = _send("platform", "http://plain.example.test", with_proxy)
    net.nothing_sent()
    refused(exc, ValueError)
