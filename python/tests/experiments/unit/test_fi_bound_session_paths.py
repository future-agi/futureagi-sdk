# ruff: noqa: F811
"""Every way a Future AGI-bound session sends refuses to follow a redirect, and netrc stays out.

A redirect from a Future AGI endpoint to another host must not reach that host with the SDK's keys
or any credentials: the second server below is a raw socket, so the tests read the bytes it received
and whether it was connected to at all. A Future AGI-bound session keeps ``trust_env``: proxy and
certificate settings the user configured apply, while netrc credentials do not. An endpoint the user
chose keeps all three.
"""

import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    AMBIENT_VARS,
    SDK_HEADERS,
    ambient,
    evals_exporter,
    export_one,
    export_spans,
    run_provider,
    sink,
)
from tests.experiments.unit.test_fi_bound_exporter_redirects import Redirector
from tests.experiments.unit.test_fi_bound_exporter_session import netrc  # noqa: F401


class RawServer:
    """Counts connections and keeps every byte it reads; answers nothing."""

    def __init__(self):
        self.connections = 0
        self.data = b""
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(8)
        self.listener.settimeout(0.2)
        self.running = True
        self.thread = threading.Thread(target=self.serve, daemon=True)

    @property
    def base(self):
        return f"http://127.0.0.1:{self.listener.getsockname()[1]}"

    def serve(self):
        while self.running:
            try:
                conn, _ = self.listener.accept()
            except OSError:
                continue
            self.connections += 1
            conn.settimeout(0.5)
            try:
                self.data += conn.recv(65536)
            except OSError:
                pass
            conn.close()

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.running = False
        self.thread.join(timeout=2)
        self.listener.close()


@pytest.fixture
def second():
    with RawServer() as server:
        yield server


@pytest.fixture
def first(second):
    """A Future AGI endpoint that answers every request with a 307 to ``second``."""
    with Redirector(second.base + "/collect") as server:
        handler = server.server.RequestHandlerClass
        for method in ("GET", "HEAD", "PUT", "DELETE"):
            setattr(handler, f"do_{method}", handler.do_POST)
        yield server


def nothing_reached(second):
    assert second.connections == 0
    assert second.data == b""
    for secret in (
        b"x-api-key",
        b"x-secret-key",
        b"authorization",
        b"k-test-1234",
        b"s-test-1234",
    ):
        assert secret not in second.data.lower()


def clean_futureagi_session(headers=SDK_HEADERS):
    from fi._otlp_headers import futureagi_session

    session = futureagi_session()
    session.headers.update(headers)
    return session


# ---- check 1: a 307 to a second server, through the exporters ---------------------------------------


@pytest.mark.usefixtures("netrc")
def test_a_307_from_the_futureagi_endpoint_sends_nothing_to_the_second_server(
    first, second, monkeypatch
):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    monkeypatch.setenv("FI_BASE_URL", first.base)
    exporter = evals_exporter(first.base + "/tracer/v1/traces", SDK_HEADERS)
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    export_one(provider)
    assert first.requests
    nothing_reached(second)


@pytest.mark.usefixtures("netrc")
def test_a_307_from_the_run_exporters_endpoint_sends_nothing_to_the_second_server(
    first, second
):
    export_one(run_provider(first.base))
    assert first.requests
    nothing_reached(second)


# ---- check 2: every send path -------------------------------------------------------------------------

SEND_PATHS = ["get", "post", "request", "send", "head", "put", "delete"]


def call(session, path, url, **kwargs):
    if path == "send":
        prepared = session.prepare_request(requests.Request("POST", url, data=b"x"))
        return session.send(prepared, **kwargs)
    if path == "request":
        return session.request("POST", url, data=b"x", **kwargs)
    return getattr(session, path)(url, **kwargs)


@pytest.mark.parametrize("explicit", [None, True, False])
@pytest.mark.parametrize("path", SEND_PATHS)
@pytest.mark.usefixtures("netrc")
def test_no_send_path_of_the_session_follows_a_redirect(first, second, path, explicit):
    session = clean_futureagi_session()
    kwargs = {} if explicit is None else {"allow_redirects": explicit}
    with pytest.raises(requests.RequestException):
        call(session, path, first.base + "/tracer/v1/traces", **kwargs)
    assert first.requests
    nothing_reached(second)


@pytest.mark.usefixtures("netrc")
def test_an_adapter_that_retries_on_redirects_does_not_follow_either(first, second):
    session = clean_futureagi_session()
    session.mount(
        "http://",
        HTTPAdapter(max_retries=Retry(total=5, redirect=5, status_forcelist=[307])),
    )
    with pytest.raises(requests.RequestException):
        session.post(first.base + "/tracer/v1/traces", data=b"x", allow_redirects=True)
    nothing_reached(second)


def test_a_response_that_is_not_a_redirect_comes_back_unchanged(sink):
    session = clean_futureagi_session()
    response = session.post(sink.base + "/tracer/v1/traces", data=b"x")
    assert response.status_code == 200
    assert sink.custom(sink.requests[0]) == SDK_HEADERS


# ---- check 3: netrc off, proxy and certificates on ------------------------------------------------------


def test_the_session_itself_sends_no_netrc_credentials(sink, netrc):
    session = clean_futureagi_session()
    session.post(sink.base + "/tracer/v1/traces", data=b"x")
    assert "authorization" not in sink.requests[0]
    assert session.trust_env is True


def test_the_exporters_send_no_netrc_credentials(sink, netrc, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", sink.base)
    export_spans(evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS))
    export_one(run_provider(sink.base))
    assert len(sink.requests) == 2
    assert all("authorization" not in sent for sent in sink.requests)


def test_a_user_chosen_endpoint_keeps_netrc(sink, netrc, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test")
    export_spans(evals_exporter(sink.base + "/v1/traces", kind="OTLP_HTTP"))
    assert sink.requests[0].get("authorization", "").startswith("Basic ")


class Proxy:
    """A forward proxy that records the absolute URL of every request it is asked for."""

    def __init__(self):
        self.urls = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                outer.urls.append(self.path)
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def proxy(monkeypatch):
    for name in (
        "NO_PROXY",
        "no_proxy",
        "HTTPS_PROXY",
        "https_proxy",
        "ALL_PROXY",
        "all_proxy",
    ):
        monkeypatch.delenv(name, raising=False)
    with Proxy() as server:
        monkeypatch.setenv("HTTP_PROXY", server.url)
        monkeypatch.setenv("http_proxy", server.url)
        yield server


def test_the_session_uses_the_proxy_the_user_configured(proxy):
    session = clean_futureagi_session()
    response = session.post("http://api.futureagi.com/tracer/v1/traces", data=b"x")
    assert response.status_code == 200
    assert proxy.urls == ["http://api.futureagi.com/tracer/v1/traces"]


def test_a_self_hosted_http_base_with_the_opt_in_ignores_a_configured_proxy(proxy, ambient, monkeypatch):
    # The exporter the SDK builds for a plain send of its keys reaches its target itself: nothing reaches the proxy.
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    monkeypatch.setenv("FI_BASE_URL", "http://self-managed.example.test")
    exporter = evals_exporter("http://self-managed.example.test/tracer/v1/traces", SDK_HEADERS)
    export_spans(exporter)
    assert proxy.urls == []


def test_a_self_hosted_http_base_without_the_opt_in_is_refused_whatever_the_proxy(proxy, ambient, monkeypatch):
    from fi.errors import ConfigurationError

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    monkeypatch.setenv("FI_BASE_URL", "http://self-managed.example.test")
    with pytest.raises(ConfigurationError) as refused:
        evals_exporter("http://self-managed.example.test/tracer/v1/traces", SDK_HEADERS)
    assert refused.value.code == "insecure_http_origin"
    assert proxy.urls == []


def test_a_user_chosen_endpoint_uses_the_proxy(proxy, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test")
    export_spans(
        evals_exporter("http://collector.example.test/v1/traces", kind="OTLP_HTTP")
    )
    assert proxy.urls == ["http://collector.example.test/v1/traces"]


def test_the_session_uses_the_certificate_bundle_the_user_configured(
    tmp_path, monkeypatch
):
    missing = tmp_path / "no-such-bundle.pem"
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(missing))
    session = clean_futureagi_session()
    with pytest.raises(OSError, match="CA"):
        session.post("https://api.futureagi.com/tracer/v1/traces", data=b"x")


def test_a_user_chosen_endpoint_uses_the_certificate_bundle(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(tmp_path / "no-such-bundle.pem"))
    with pytest.raises(OSError, match="CA"):
        requests.Session().post("https://collector.example.test/v1/traces", data=b"x")


# ---- the session accepts only adapters the SDK built ------------------------------------------------------


class FollowingAdapter(HTTPAdapter):
    """An adapter that follows a redirect inside its own send, out of the session's reach."""

    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        if response.is_redirect:
            followed = requests.Request(
                request.method,
                response.headers["Location"],
                headers=dict(request.headers),
                data=request.body,
            ).prepare()
            return super().send(followed, **kwargs)
        return response


def test_mounting_an_adapter_the_sdk_did_not_build_is_refused():
    from fi.errors import ConfigurationError

    session = clean_futureagi_session()
    with pytest.raises(ConfigurationError) as refused:
        session.mount("http://", FollowingAdapter())
    message = str(refused.value)
    for secret in ("k-test-1234", "s-test-1234", "x-api-key"):
        assert secret not in message


def test_an_adapter_that_follows_inside_its_send_gets_no_connection_on_the_second_server(
    first, second
):
    from fi.errors import ConfigurationError

    session = clean_futureagi_session()
    try:
        session.mount("http://", FollowingAdapter())
    except ConfigurationError:
        pass
    try:
        session.post(first.base + "/tracer/v1/traces", data=b"x")
    except requests.RequestException:
        pass
    nothing_reached(second)


def test_replacing_the_adapters_after_construction_is_refused():
    from fi.errors import ConfigurationError

    session = clean_futureagi_session()
    with pytest.raises(ConfigurationError):
        session.adapters = {"http://": FollowingAdapter()}
    assert type(session.adapters["http://"]) is HTTPAdapter


def test_the_adapters_requests_mounts_by_default_work(sink):
    session = clean_futureagi_session()
    assert set(session.adapters) == {"https://", "http://"}
    assert session.post(sink.base + "/tracer/v1/traces", data=b"x").status_code == 200


def test_a_plain_adapter_with_its_own_retry_settings_is_accepted(sink):
    session = clean_futureagi_session()
    session.mount("http://", HTTPAdapter(max_retries=Retry(total=2)))
    assert session.post(sink.base + "/tracer/v1/traces", data=b"x").status_code == 200


def test_the_session_exports_with_only_the_sdk_headers(sink):
    export_spans(evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS))
    assert sink.custom(sink.requests[0]) == SDK_HEADERS


def test_a_user_chosen_endpoints_session_accepts_any_adapter(sink, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test")
    session = requests.Session()
    session.mount("http://", FollowingAdapter())
    assert session.post(sink.base + "/v1/traces", data=b"x").status_code == 200
