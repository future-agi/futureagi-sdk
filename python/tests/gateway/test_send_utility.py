"""``fi.gateway._utils._send_utility``: the passed callable sends a non-loopback request, and a loopback request goes
through the gateway clients' loopback-direct client when the callable is ``httpx.get`` or ``httpx.post``."""

from __future__ import annotations

import httpx
import pytest

from fi.gateway import _utils
from fi.gateway._transport import _direct

REAL = {"get": httpx.get, "post": httpx.post}


def _recorder(sent):
    def send(url, **kwargs):
        sent.append((url, kwargs))
        return httpx.Response(200, request=httpx.Request("GET", url))

    return send


def test_a_non_loopback_url_is_sent_with_the_callable_it_was_given():
    sent = []
    response = _utils._send_utility(_recorder(sent), "http://gateway.test/healthz", headers={"a": "b"}, timeout=3.0)
    assert response.status_code == 200
    assert sent == [("http://gateway.test/healthz", {"headers": {"a": "b"}, "timeout": 3.0})]


@pytest.mark.parametrize("send_name", ["get", "post"])
def test_a_non_loopback_url_with_httpx_get_or_post_uses_that_function(monkeypatch, send_name):
    sent = []
    monkeypatch.setattr(httpx, send_name, _recorder(sent))
    _utils._send_utility(getattr(httpx, send_name), "https://gateway.test/x")
    assert [url for url, _ in sent] == ["https://gateway.test/x"]


def test_a_loopback_url_with_another_callable_uses_that_callable():
    sent = []
    _utils._send_utility(_recorder(sent), "http://127.0.0.1:8080/healthz")
    assert [url for url, _ in sent] == ["http://127.0.0.1:8080/healthz"]


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "[::1]"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_a_loopback_url_with_httpx_get_or_post_goes_through_the_loopback_direct_client(monkeypatch, host, method):
    made = []

    class Client(httpx.Client):
        def __init__(self, **kwargs):
            made.append(kwargs)
            super().__init__(transport=httpx.MockTransport(lambda request: httpx.Response(204)))

    monkeypatch.setattr(_direct, "LoopbackDirectClient", Client)
    response = _utils._send_utility(REAL[method], f"http://{host}:8080/x", timeout=2.0)
    assert response.status_code == 204 and made[0].keys() >= {"timeout", "follow_redirects"}
    assert made[0]["timeout"] == 2.0 and made[0]["follow_redirects"] is False


def test_a_replaced_httpx_get_is_called_for_a_loopback_url(monkeypatch):
    sent = []
    monkeypatch.setattr(httpx, "get", _recorder(sent))
    _utils._send_utility(httpx.get, "http://localhost:8080/healthz")
    assert [url for url, _ in sent] == ["http://localhost:8080/healthz"]
