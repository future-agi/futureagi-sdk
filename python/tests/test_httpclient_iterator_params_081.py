from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest
import requests
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig


@pytest.fixture
def listener(monkeypatch):
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)
    request_lines = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            request_lines.append(self.raw_requestline)
            if self.path.startswith("/retry") and len(request_lines) == 1:
                return  # Close the first connection without a response.
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response_only(200)
            self.end_headers()

        do_POST = do_GET

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}", request_lines
        finally:
            server.shutdown()
            thread.join()


def _pairs():
    yield "item", "one"
    yield "item", "two"


@pytest.mark.parametrize("method", [HttpMethod.GET, HttpMethod.POST])
@pytest.mark.parametrize("session_kind", ["sdk", "requests", "futures", "wrapped"])
def test_iterable_query_params_on_wire(listener, method, session_kind):
    url, request_lines = listener
    with requests.Session() as inner:
        inner.trust_env = False
        session = None
        if session_kind == "requests":
            session = inner
        elif session_kind in ("futures", "wrapped"):
            session = FuturesSession(session=inner if session_kind == "wrapped" else None)
            session.trust_env = False

        client = HttpClient(url, session=session)
        try:
            for params in (iter([("item", "one"), ("item", "two")]), _pairs(), {"item": "one"}.items()):
                config = RequestConfig(method=method, url=url, timeout=2, retry_attempts=1)
                # Supply the transport input after model validation.
                config.params = params
                assert client.request(config).status_code == 200
        finally:
            client.close()

    assert request_lines == [
        f"{method.value} /?{query} HTTP/1.1\r\n".encode()
        for query in ("item=one&item=two", "item=one&item=two", "item=one")
    ]


def test_query_params_match_preflight_and_every_attempt(listener, monkeypatch):
    url, request_lines = listener
    prepared_paths = []
    prepare_request = requests.Session.prepare_request

    def record_path(session, request):
        prepared = prepare_request(session, request)
        prepared_paths.append(prepared.path_url)
        return prepared

    class Pairs:
        def __init__(self):
            self._pairs = _pairs()

        def __iter__(self):
            return self._pairs

    monkeypatch.setattr(requests.Session, "prepare_request", record_path)
    config = RequestConfig(method=HttpMethod.GET, url=f"{url}/retry", timeout=2, retry_attempts=2, retry_delay=0)
    config.params = Pairs()
    client = HttpClient(url)
    try:
        assert client.request(config).status_code == 200
    finally:
        client.close()

    path = "/retry?item=one&item=two"
    assert prepared_paths == [path] * 3
    assert request_lines == [f"GET {path} HTTP/1.1\r\n".encode()] * 2
