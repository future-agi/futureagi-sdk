"""``HttpClient`` sends a keyed request once when its session refuses the redirect answer.

The SDK's own session raises ``KeyedRedirectRefusedError`` for a 3xx answer to a request that carries keys. That
refusal is an answer, not a transport failure, so the retry loop does not send the request again: a transient 307
followed by a 200 raises, the first origin receives exactly one request, and the redirect target receives
none, also when the ``Location`` cannot be read. Transport failures are retried as configured.
"""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from fi.api.auth import APIKeyAuth, HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.errors import KeyedRedirectRefusedError

API_MARKER = "r4l-retry-api-marker-5e21"
SECRET_MARKER = "r4l-retry-secret-marker-c3a8"


class Origin:
    """A loopback listener answering the first ``redirects`` requests with ``status`` to ``location``, then 200."""

    def __init__(self, host, status=307, redirects=0, location="/"):
        self.raw = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def answer(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                outer.raw.append(str(self.headers))
                if len(outer.raw) <= outer.redirects:
                    self.send_response(outer.status)
                    self.send_header("Location", outer.location)
                else:
                    self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

            do_GET = do_POST = answer

            def log_message(self, *args):
                pass

        self.status, self.redirects, self.location = status, redirects, location
        self.server = ThreadingHTTPServer((host, 0), Handler)
        self.base = f"http://{host}:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def marker_bytes(self):
        text = "".join(self.raw)
        return sum(text.count(marker) * len(marker) for marker in (API_MARKER, SECRET_MARKER))

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def keyed_client(kind, base):
    if kind == "HttpClient":
        return HttpClient(base_url=base, default_headers={"X-Api-Key": API_MARKER, "X-Secret-Key": SECRET_MARKER})
    return APIKeyAuth(fi_api_key=API_MARKER, fi_secret_key=SECRET_MARKER, fi_base_url=base)


@pytest.mark.parametrize("method", [HttpMethod.GET, HttpMethod.POST])
@pytest.mark.parametrize("redirects", [1, 3], ids=["transient", "persistent"])
@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("kind", ["HttpClient", "APIKeyAuth"])
def test_a_refused_redirect_sends_the_keyed_request_once(kind, status, redirects, method):
    with Origin("127.0.0.2") as target:
        with Origin("127.0.0.1", status, redirects, target.base + "/landing") as origin:
            client = keyed_client(kind, origin.base)
            config = RequestConfig(method=method, url=origin.base + "/call", retry_attempts=3, retry_delay=0)
            try:
                with pytest.raises(KeyedRedirectRefusedError) as refused:
                    client.request(config)
            finally:
                client.close()
    assert refused.value.status_code == status
    assert len(origin.raw) == 1
    assert origin.marker_bytes() == len(API_MARKER) + len(SECRET_MARKER)
    assert target.raw == []


@pytest.mark.parametrize("location", ["bracketed-ipv4", "latin-1-byte"])
@pytest.mark.parametrize("kind", ["HttpClient", "APIKeyAuth"])
def test_a_redirect_whose_location_cannot_be_read_is_refused_once(kind, location):
    with Origin("127.0.0.2") as target:
        port = target.base.rsplit(":", 1)[1]
        written = {"bracketed-ipv4": f"http://[127.0.0.2]:{port}/landing", "latin-1-byte": target.base + "/\xe9"}[location]
        with Origin("127.0.0.1", 307, 1, written) as origin:
            client = keyed_client(kind, origin.base)
            config = RequestConfig(method=HttpMethod.POST, url=origin.base + "/call", retry_attempts=3, retry_delay=0)
            try:
                with pytest.raises(KeyedRedirectRefusedError):
                    client.request(config)
            finally:
                client.close()
    assert len(origin.raw) == 1
    assert target.raw == []


def test_a_transport_failure_is_still_retried(monkeypatch):
    client = HttpClient(base_url="http://127.0.0.1:9")
    calls = []

    def request(**kwargs):
        calls.append(kwargs["url"])
        raise ConnectionError("transport failure")

    monkeypatch.setattr(client._session, "request", request)
    with pytest.raises(ConnectionError):
        client.request(RequestConfig(method=HttpMethod.GET, url="http://127.0.0.1:9/x", retry_attempts=3, retry_delay=0))
    client.close()
    assert len(calls) == 3
