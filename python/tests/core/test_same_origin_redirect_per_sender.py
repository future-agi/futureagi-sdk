"""A loopback server redirects every request to a path on its own origin. Platform and session clients send the
marker keys on each hop and report the redirect limit. The other senders stop after the initial request; exporters
report failure through their export result or status."""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from requests import TooManyRedirects

import fi
from fi import AsyncFutureAGIClient, FutureAGIClient

MARKER_KEY = "mk-same-origin-aaaa1111"
MARKER_SECRET = "ms-same-origin-bbbb2222"
NEXT = "/landed-after-the-redirect"
PROXY_VARIABLES = ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy")


class Redirector:
    def __init__(self, status: int = 302) -> None:
        self.requests: list[dict] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _answer(self) -> None:
                length = int(self.headers.get("content-length") or 0)
                body = self.rfile.read(length) if length else b""
                outer.requests.append({
                    "method": self.command,
                    "path": self.path,
                    "keys": (self.headers.get("X-Api-Key"), self.headers.get("X-Secret-Key")),
                    "body": body,
                })
                self.send_response(status)
                self.send_header("Location", NEXT)
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _answer

            def log_message(self, *args) -> None:
                pass

        self._http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._http.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        threading.Thread(target=self._http.serve_forever, daemon=True).start()

    def close(self) -> None:
        self._http.shutdown()
        self._http.server_close()

    def assert_refused_after_one_request(self) -> None:
        assert len(self.requests) == 1, self.requests
        assert self.requests[0]["path"] != NEXT
        assert all(r["path"] != NEXT for r in self.requests)

    def assert_followed_to_limit(self, first_method: str, first_path: str, hop_method: str) -> None:
        assert [(r["method"], r["path"]) for r in self.requests] == [(first_method, first_path)] + [(hop_method, NEXT)] * 5
        assert all(r["keys"] == (MARKER_KEY, MARKER_SECRET) for r in self.requests)


@pytest.fixture
def origin(monkeypatch, tmp_path):
    for name in PROXY_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "no-login.json"))
    monkeypatch.setenv("FI_RUN_DIR", str(tmp_path / "runs"))
    server = Redirector()
    yield server
    server.close()


def _is_keyed_redirect(error: BaseException) -> bool:
    return isinstance(error, fi.KeyedRedirectRefusedError) and error.get_error_code() == "KEYED_REDIRECT_REFUSED"


def _keys(url: str) -> dict:
    return {"api_key": MARKER_KEY, "secret_key": MARKER_SECRET, "base_url": url, "retries": 0}


def test_the_gateway_client_refuses_a_same_origin_redirect(origin):
    from fi.gateway import AgentCC

    client = AgentCC(api_key=MARKER_KEY, base_url=origin.url, max_retries=2)
    try:
        with pytest.raises(Exception) as info:
            client.models.list()
    finally:
        client.close()
    assert _is_keyed_redirect(info.value)
    origin.assert_refused_after_one_request()


def test_the_async_gateway_client_refuses_a_same_origin_redirect(origin):
    from fi.gateway import AsyncAgentCC

    async def go():
        client = AsyncAgentCC(api_key=MARKER_KEY, base_url=origin.url, max_retries=2)
        try:
            return await client.models.list()
        finally:
            await client.aclose()

    with pytest.raises(Exception) as info:
        asyncio.run(go())
    assert _is_keyed_redirect(info.value)
    origin.assert_refused_after_one_request()


def test_the_gateway_utility_calls_do_not_follow_a_same_origin_redirect(origin):
    from fi.gateway._utils import check_valid_key, health_check

    assert check_valid_key(MARKER_KEY, origin.url) is False
    assert health_check(api_key=MARKER_KEY, base_url=origin.url)["status"] == "error"
    assert health_check("m", api_key=MARKER_KEY, base_url=origin.url)["status"] == "error"
    assert len(origin.requests) == 3 and all(r["path"] != NEXT for r in origin.requests)


def test_the_management_calls_refuse_a_same_origin_redirect(origin):
    client = FutureAGIClient(**_keys(origin.url))
    with pytest.raises(fi.KeyedRedirectRefusedError) as info:
        client.gateway.config.get_active()
    assert _is_keyed_redirect(info.value)
    origin.assert_refused_after_one_request()


def test_the_async_management_calls_refuse_a_same_origin_redirect(origin):
    async def go():
        async with AsyncFutureAGIClient(**_keys(origin.url)) as client:
            return await client.gateway.config.get_active()

    with pytest.raises(fi.KeyedRedirectRefusedError):
        asyncio.run(go())
    origin.assert_refused_after_one_request()


def test_the_sandbox_calls_refuse_a_same_origin_redirect(origin):
    client = FutureAGIClient(**_keys(origin.url), platform_base_url=origin.url + "/omega/api")
    with pytest.raises(fi.KeyedRedirectRefusedError):
        client.sandboxes.list()
    origin.assert_refused_after_one_request()


def test_the_async_sandbox_calls_refuse_a_same_origin_redirect(origin):
    async def go():
        async with AsyncFutureAGIClient(**_keys(origin.url), platform_base_url=origin.url + "/omega/api") as client:
            return await client.sandboxes.list()

    with pytest.raises(fi.KeyedRedirectRefusedError):
        asyncio.run(go())
    origin.assert_refused_after_one_request()


def test_the_knowledge_base_create_follows_same_origin_redirects_to_the_limit(origin, monkeypatch):
    # 0.8.1 followed these with requests; the upload follows a redirect on its own origin as requests does (a 302 as a
    # GET without the body), and a sixth redirect in a row raises requests.TooManyRedirects, which create_kb wraps.
    import requests

    from fi.kb.client import KnowledgeBase
    from fi.utils.errors import SDKException

    monkeypatch.setenv("FI_BASE_URL", origin.url)
    monkeypatch.setenv("FI_API_KEY", MARKER_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", MARKER_SECRET)
    with pytest.raises(SDKException) as caught:
        KnowledgeBase().create_kb("kb")
    assert isinstance(caught.value.__cause__ or caught.value.__context__, requests.TooManyRedirects)
    origin.assert_followed_to_limit("POST", origin.requests[0]["path"], "GET")


def test_the_platform_client_follows_same_origin_redirects_to_the_limit(origin):
    import fi.platform as fp

    with fp.Client(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=origin.url, max_retries=0) as client:
        with pytest.raises(fp.APIConnectionError, match="more than 5 redirects"):
            client.request("GET", "/probe/")
    origin.assert_followed_to_limit("GET", "/probe/", "GET")


def test_the_async_platform_client_follows_same_origin_redirects_to_the_limit(origin):
    import fi.platform as fp

    async def go():
        async with fp.AsyncClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=origin.url, max_retries=0) as client:
            return await client.request("GET", "/probe/")

    with pytest.raises(fp.APIConnectionError, match="more than 5 redirects"):
        asyncio.run(go())
    origin.assert_followed_to_limit("GET", "/probe/", "GET")


@pytest.mark.parametrize("status,hop_method", [(301, "GET"), (302, "GET"), (303, "GET"), (307, "POST"), (308, "POST")])
def test_the_platform_client_follows_each_same_origin_redirect_status(monkeypatch, status, hop_method):
    import fi.platform as fp

    for name in PROXY_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    server = Redirector(status)
    try:
        with fp.Client(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=server.url, max_retries=0) as client:
            with pytest.raises(fp.APIConnectionError, match="more than 5 redirects"):
                client.request("POST", "/probe/", query={"initial": 1}, body={"x": 1})
        server.assert_followed_to_limit("POST", "/probe/?initial=1", hop_method)
        body = server.requests[0]["body"]
        assert json.loads(body) == {"x": 1}
        assert [r["body"] for r in server.requests[1:]] == [body if hop_method == "POST" else b""] * 5
    finally:
        server.close()


def test_the_experiment_trace_export_does_not_follow_a_same_origin_redirect(origin):
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._tracing.export_status import ExportStatus
    from fi.experiments._redact import Redactor

    outcome = ExportStatus("run-1", origin.url + "/tracer/v1/traces", Redactor())
    make = exporter_factory(base_url=origin.url, api_key=MARKER_KEY, secret_key=MARKER_SECRET, project="p", run_name="r",
                            run_id="run-1", redactor=Redactor(), outcome=outcome, _endpoint=origin.url + "/tracer/v1/traces")
    provider = make()
    tracer = provider.get_tracer("t")
    tracer.start_span("s").end()
    provider.shutdown()
    outcome.failed()
    assert outcome.error is not None and outcome.error.status_code == 302
    origin.assert_refused_after_one_request()


@pytest.mark.parametrize("kind", ["FUTUREAGI", "ARIZE", "PHOENIX", "LANGFUSE"])
def test_an_evals_exporter_with_keys_does_not_follow_a_same_origin_redirect(origin, kind):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SpanExportResult
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig
    from fi.evals.otel.types import ExporterType

    headers = {"X-Api-Key": MARKER_KEY, "X-Secret-Key": MARKER_SECRET}
    exporter = _create_exporter(ExporterConfig(type=getattr(ExporterType, kind), endpoint=origin.url + "/v1/traces", headers=headers))
    span = TracerProvider().get_tracer("t").start_span("s")
    span.end()
    assert exporter.export([span]) == SpanExportResult.FAILURE
    origin.assert_refused_after_one_request()


def test_the_session_client_follows_same_origin_redirects_to_the_limit(origin, monkeypatch):
    from fi.api.auth import APIKeyAuth
    from fi.api.types import HttpMethod, RequestConfig

    monkeypatch.setenv("FI_BASE_URL", origin.url)
    monkeypatch.setenv("FI_API_KEY", MARKER_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", MARKER_SECRET)
    client = APIKeyAuth()
    try:
        with pytest.raises(TooManyRedirects, match=r"Exceeded 5 redirects\."):
            client.request(RequestConfig(method=HttpMethod.GET, url=f"{origin.url}/x", retry_attempts=1))
    finally:
        client.close()
    origin.assert_followed_to_limit("GET", "/x", "GET")


def test_the_generated_client_refuses_a_same_origin_redirect(origin):
    client = FutureAGIClient(**_keys(origin.url))
    with pytest.raises(fi.KeyedRedirectRefusedError):
        client.users.current()
    origin.assert_refused_after_one_request()
