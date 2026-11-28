"""Each hop of a same-origin redirect that HttpClient and the fi.kb uploads follow goes out as requests sent it in
futureagi 0.8.1: one retry budget for the whole call, the sending session's lower ``max_redirects``, the same body and
media type for a 307 or 308, cookies from the jar, the authentication's headers without running it again, no body
headers on a redirect that drops the body, and the redirect history. Loopback listener and planted marker keys only."""

from __future__ import annotations

import io
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socket import SHUT_RDWR

import pytest
import requests
from requests_futures.sessions import FuturesSession

from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig

KEY = "mk-hops-marker-key"
SECRET = "ms-hops-marker-secret"


class Listener:
    def __init__(self, answer):
        self.hits: list[dict] = []
        self.counts: Counter = Counter()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _any(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                outer.counts[self.path] += 1
                outer.hits.append({
                    "method": self.command, "path": self.path, "body": body,
                    "type": self.headers.get("Content-Type"), "cookie": self.headers.get("Cookie"),
                    "auth": self.headers.get("X-Count"),
                    "keyed": (self.headers.get("X-Api-Key"), self.headers.get("X-Secret-Key")) == (KEY, SECRET),
                })
                reply = answer(self.path, outer.counts[self.path])
                if reply is None:
                    self.close_connection = True
                    self.connection.shutdown(SHUT_RDWR)
                    return
                status, extra = reply
                self.send_response(status)
                for name, value in extra.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_GET = do_POST = do_PATCH = _any

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def listen(monkeypatch):
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "FI_EXTRA_HEADERS"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    made = []

    def make(answer):
        made.append(Listener(answer))
        return made[-1]

    yield make
    for listener in made:
        listener.close()


def _session(kind, inner=None):
    if kind == "sdk":
        return None
    inner = inner or requests.Session()
    inner.trust_env = False
    return inner if kind == "requests" else FuturesSession(session=inner)


def _call(base, session, method=HttpMethod.GET, retries=1, **config):
    client = APIKeyAuth(fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base, session=session)
    return client.request(RequestConfig(method=method, url=base + "/start", timeout=3, retry_attempts=retries,
                                        retry_delay=0, **config))


@pytest.mark.parametrize("kind", ["sdk", "futures"])
def test_one_retry_budget_covers_the_call_and_its_hops(listen, kind):
    # Each path drops its first request; /start then answers a 307 to /hop. With two attempts 0.8.1 sent three
    # keyed requests and raised the connection error.
    site = listen(lambda path, n: None if n == 1 else ((307, {"Location": "/hop"}) if path == "/start" else (200, {})))
    with pytest.raises(requests.ConnectionError):
        _call(site.base, _session(kind), retries=2)
    assert [(hit["path"], hit["keyed"]) for hit in site.hits] == [("/start", True), ("/start", True), ("/hop", True)]


@pytest.mark.parametrize("kind", ["requests", "futures"])
@pytest.mark.parametrize("limit", [1, 3])
def test_the_sending_sessions_lower_max_redirects_applies(listen, kind, limit):
    site = listen(lambda path, n: (307, {"Location": "/hop"}))
    inner = requests.Session()
    inner.max_redirects = limit
    with pytest.raises(requests.TooManyRedirects, match=f"Exceeded {limit} redirects"):
        _call(site.base, _session(kind, inner))
    assert [hit["path"] for hit in site.hits] == ["/start"] + ["/hop"] * limit


@pytest.mark.parametrize("kind", ["sdk", "requests", "futures"])
@pytest.mark.parametrize("status", [307, 308])
def test_a_307_or_308_sends_the_same_multipart_bytes_and_media_type(listen, kind, status):
    site = listen(lambda path, n: (status, {"Location": "/hop"}) if path == "/start" else (200, {}))
    _call(site.base, _session(kind), method=HttpMethod.POST, files={"file": ("a.txt", io.BytesIO(b"planted-file"))})
    first, second = site.hits
    assert b"planted-file" in first["body"]
    assert (second["body"], second["type"], second["method"]) == (first["body"], first["type"], "POST")


@pytest.mark.parametrize("kind", ["sdk", "futures"])
def test_a_hop_takes_its_cookies_from_the_jar(listen, kind):
    site = listen(lambda path, n: (302, {"Location": "/hop", "Set-Cookie": "session=new; Path=/"}) if path == "/start"
                  else (200, {}))
    _call(site.base, _session(kind), headers={"Cookie": "session=old"})
    assert [hit["cookie"] for hit in site.hits] == ["session=old", "session=new"]


def test_the_sessions_authentication_is_not_run_again_on_a_hop(listen):
    calls = []

    class Counting(requests.auth.AuthBase):
        def __call__(self, request):
            calls.append(1)
            request.headers["X-Count"] = str(len(calls))
            return request

    site = listen(lambda path, n: (302, {"Location": "/hop"}) if path == "/start" else (200, {}))
    inner = requests.Session()
    inner.auth = Counting()
    _call(site.base, _session("futures", inner))
    assert [hit["auth"] for hit in site.hits] == ["1", "1"]


@pytest.mark.parametrize("kind", ["requests", "futures"])
def test_a_redirect_that_drops_the_body_sends_no_body_headers(listen, kind):
    site = listen(lambda path, n: (302, {"Location": "/hop"}) if path == "/start" else (200, {}))
    inner = requests.Session()
    inner.headers["Content-Type"] = "application/custom"
    _call(site.base, _session(kind, inner), method=HttpMethod.POST, data={"planted": "body"})
    assert [(hit["method"], hit["body"], hit["type"]) for hit in site.hits] == [
        ("POST", b"planted=body", "application/custom"), ("GET", b"", None)]


@pytest.mark.parametrize("kind", ["sdk", "futures"])
def test_the_redirect_history_and_fragment_are_kept(listen, kind):
    site = listen(lambda path, n: ((308, {"Location": "#new"}) if n == 1 else (308, {"Location": "/hop"}))
                  if path == "/start" else (200, {}))
    response = _call(site.base, _session(kind))
    assert [hit["path"] for hit in site.hits] == ["/start", "/start", "/hop"]
    assert ([r.status_code for r in response.history], response.url.rsplit("#", 1)[-1]) == ([308, 308], "new")


def test_a_kb_upload_307_off_the_extra_headers_scope_keeps_the_body_media_type(listen, monkeypatch, tmp_path):
    from fi.kb.client import KnowledgeBase

    site = listen(lambda path, n: (307, {"Location": "/outside"}) if path.endswith("/knowledge-base/") else (200, {}))
    monkeypatch.setenv("FI_EXTRA_HEADERS", "Content-Type=application/json")
    kb = KnowledgeBase(fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=site.base + "/scope")
    try:
        kb.create_kb(name="planted-kb")
    except Exception:  # noqa: BLE001 - the empty answer is not a knowledge base; the requests are what is read
        pass
    first, second = site.hits[-2:]
    assert (second["path"], second["body"], second["type"]) == ("/outside", first["body"], first["type"])
