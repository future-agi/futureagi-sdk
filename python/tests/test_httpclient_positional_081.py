import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.errors import ConfigurationError


@pytest.fixture(params=["127.0.0.1"])
def listener(request, monkeypatch):
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)
    requests_seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests_seen.append(self.headers)
            self.send_response_only(200)
            self.end_headers()

    class Server(HTTPServer):
        connections = 0

        def get_request(self):
            connection = super().get_request()
            self.connections += 1
            return connection

    with Server((request.param, 0), Handler) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        try:
            yield server, requests_seen
        finally:
            server.shutdown()
            thread.join()


def _get(url):
    return RequestConfig(method=HttpMethod.GET, url=url, timeout=2, retry_attempts=1)


def test_fourth_positional_true_reaches_loopback(listener):
    server, requests_seen = listener
    url = f"http://127.0.0.1:{server.server_port}"
    client = HttpClient(url, None, None, True)
    try:
        assert client._allow_insecure_http is True
        assert client.request(_get(url)).status_code == 200
    finally:
        client.close()
    assert server.connections == len(requests_seen) == 1


@pytest.mark.parametrize("listener", ["127.0.0.2"], indirect=True)
@pytest.mark.parametrize("allow", [False, "1"], ids=["false", "non-boolean"])
def test_fourth_positional_opt_out_overrides_environment(listener, monkeypatch, allow):
    server, requests_seen = listener
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    host = "self-managed.example.test"
    getaddrinfo = socket.getaddrinfo

    def resolve(name, *args, **kwargs):
        return getaddrinfo("127.0.0.2" if name == host else name, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    url = f"http://{host}:{server.server_port}"
    client = HttpClient(url, None, None, allow)
    try:
        assert client._allow_insecure_http is False
        config = _get(url)
        config.headers = {"X-Api-Key": "test-key-marker-1"}
        with pytest.raises(ConfigurationError) as exc:
            client.request(config)
        assert exc.value.code == "insecure_http_origin"
    finally:
        client.close()
    assert server.connections == 0
    assert requests_seen == []


def test_extra_headers_bound_by_keyword_only(listener):
    server, requests_seen = listener
    url = f"http://127.0.0.1:{server.server_port}"
    positional = HttpClient(url, None, None, {"X-Team": "positional"})
    try:
        assert positional.request(_get(url)).status_code == 200
    finally:
        positional.close()

    keyword = HttpClient(url, extra_headers={"X-Team": "keyword"})
    try:
        assert keyword.request(_get(url)).status_code == 200
    finally:
        keyword.close()

    assert [headers.get("X-Team") for headers in requests_seen] == [None, "keyword"]


def test_extra_headers_is_not_a_fifth_positional_argument():
    with pytest.raises(TypeError):
        HttpClient("http://127.0.0.1:9", None, None, True, {"X-Team": "positional"})
