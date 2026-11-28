"""Prompt lookup follows same-origin redirects within the hop limit and refuses other redirect targets.

A redirect refusal or a hop-limit error does not send a request to the default lookup route.
A missing production label still triggers that fallback.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from requests.exceptions import TooManyRedirects

from fi.errors import KeyedRedirectRefusedError
from fi.prompt import Prompt
from fi.prompt.cache import PromptCache
from fi.utils.routes import Routes
from tests.test_plain_http_key_guards import PROXY_VARS

KEY = "test-key-marker-redirect-1"
SECRET = "test-secret-marker-redirect-1"


class _Sink(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, status: int, location: str = "") -> None:
        self.status = status
        self.location = location
        self.requests: list[tuple[str, str | None, str | None]] = []
        self.connections = 0
        super().__init__(("127.0.0.1", 0), _Handler)
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def get_request(self):  # type: ignore[override]
        conn = super().get_request()
        self.connections += 1
        return conn

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"

    def close(self) -> None:
        self.shutdown()
        self.server_close()


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.server.requests.append((self.path, self.headers.get("X-Api-Key"), self.headers.get("X-Secret-Key")))
        self.send_response(self.server.status)
        if self.server.location:
            self.send_header("Location", self.server.location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *_args) -> None:
        pass


@pytest.fixture(autouse=True)
def _clean(monkeypatch, tmp_path):
    for name in (*PROXY_VARS, "FI_ALLOW_INSECURE_HTTP", "FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("fi.prompt.client.prompt_cache", PromptCache(), raising=False)


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("opt", [{}, {"allow_insecure_http": True}], ids=["no-argument", "argument"])
def test_a_same_origin_redirect_loop_hits_the_limit(status, opt):
    target = _Sink(status)
    try:
        target.location = target.base + "/moved"
        with pytest.raises(TooManyRedirects, match=r"^Exceeded 5 redirects\.$"):
            Prompt.get_template_by_name(
                "probe", fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=target.base, **opt
            )
        assert target.connections == 6
        path, key, secret = target.requests[0]
        assert path == f"/{Routes.prompt_label_get_by_name.value}?name=probe&label=production"
        assert (key, secret) == (KEY, SECRET)
        assert target.requests[1:] == [("/moved", KEY, SECRET)] * 5
    finally:
        target.close()


@pytest.mark.parametrize(
    ("status", "cross_origin"),
    [pytest.param(code, True, id=f"cross-origin-{code}") for code in (301, 302, 303, 307, 308, 300)]
    + [pytest.param(300, False, id="same-origin-300")],
)
@pytest.mark.parametrize("opt", [{}, {"allow_insecure_http": True}], ids=["no-argument", "argument"])
def test_a_refused_redirect_answer_sends_the_keyed_lookup_once(status, cross_origin, opt):
    second = _Sink(200)
    target = _Sink(status)
    try:
        target.location = (second.base if cross_origin else target.base) + "/moved"
        with pytest.raises(KeyedRedirectRefusedError):
            Prompt.get_template_by_name(
                "probe", fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=target.base, **opt
            )
        assert len(target.requests) == 1, target.requests
        assert target.requests[0][1] == KEY
        assert "label=production" in target.requests[0][0]
        assert (second.connections, second.requests) == (0, [])
    finally:
        target.close()
        second.close()


def test_a_missing_production_label_still_falls_back_to_the_default_route():
    target = _Sink(404)
    try:
        with pytest.raises(Exception) as caught:
            Prompt.get_template_by_name("probe", fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=target.base)
        assert not isinstance(caught.value, KeyedRedirectRefusedError)
        assert len(target.requests) == 2, target.requests
        assert "label=production" in target.requests[0][0]
        assert "label=production" not in target.requests[1][0]
        assert target.requests[0][0].lstrip("/").startswith(Routes.prompt_label_get_by_name.value)
        assert target.requests[1][0].lstrip("/").startswith(Routes.get_template_by_name.value)
    finally:
        target.close()
