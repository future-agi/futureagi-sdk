"""Sends that carry the SDK's marker keys, counted at loopback listeners.

Each test sends with the SDK's own marker key and secret to a target listener and to a ``CONNECT``-aware proxy sink,
and reads how many marker bytes each one received. Host names resolve to the loopback address (``getaddrinfo`` is
replaced for the test; the gRPC cases use an address, so they need no name); nothing leaves the machine.

* A caller-supplied ``requests`` session is refused with ``KEYED_PROXY_REFUSED`` when its own routing selects a proxy
  or its transport cannot be read.
* A transport the SDK builds for a plain send ignores the proxy settings of the environment.
* A key-carrying request does not follow a redirect; the answer is a ``KeyedRedirectRefusedError`` (``KEYED_REDIRECT_REFUSED``).
* The SDK's key headers in ``OTEL_EXPORTER_OTLP_HEADERS`` do not reach an exporter that is not bound for Future AGI.
"""

import socket
import types

import pytest

from fi._keyed_errors import KeyedRedirectRefusedError
from fi.errors import ConfigurationError
from tests.experiments.unit.oracle_probe import KEY, SECRET, Sink, caller_session, export_through

NAMES = ("FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy",
         "GRPC_PROXY", "grpc_proxy", "NO_PROXY", "no_proxy", "NO_GRPC_PROXY", "no_grpc_proxy", "OTEL_EXPORTER_OTLP_HEADERS",
         "OTEL_EXPORTER_OTLP_TRACES_HEADERS", "OTEL_EXPORTER_OTLP_INSECURE", "FI_BASE_URL", "FI_GRPC_URL", "FI_TRACES_URL")


class Rig:
    """A target, two proxy sinks and a redirect target on the loopback address."""

    def __init__(self, monkeypatch):
        self.monkeypatch = monkeypatch
        self.sinks = []
        self.target = self.sink(False)
        self.a = self.sink(True)
        self.b = self.sink(True)

    def sink(self, connect_aware, redirect=None):
        sink = Sink(connect_aware, redirect)
        self.sinks.append(sink)
        return sink

    def env(self, **values):
        for name, value in values.items():
            self.monkeypatch.setenv(name, value.format(a=self.a.port, b=self.b.port, t=self.target.port))

    def marker(self):
        return {"target": self.target.marker_bytes, "a": self.a.marker_bytes, "b": self.b.marker_bytes}

    def close(self):
        for sink in self.sinks:
            sink.close()


@pytest.fixture
def rig(monkeypatch):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/login.json")
    monkeypatch.setenv("FI_API_KEY", KEY.decode())
    monkeypatch.setenv("FI_SECRET_KEY", SECRET.decode())
    real = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        if isinstance(host, str) and host not in ("localhost",) and not host.replace(".", "").isdigit() and ":" not in host:
            host = "127.0.0.1"
        return real(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    from fi.api import auth

    monkeypatch.setattr(auth, "time", types.SimpleNamespace(sleep=lambda seconds: None))
    made = Rig(monkeypatch)
    yield made
    made.close()


def evaluate_with(base, session=None):
    from fi.evals.evaluator import Evaluator

    arguments = {"session": session} if session is not None else {}
    client = Evaluator(fi_api_key=KEY.decode(), fi_secret_key=SECRET.decode(), fi_base_url=base, **arguments)
    return client._configure_evaluations("template", {"input": "x"}, "other", "check", span_id="0" * 16, trace_id="0" * 32)


def refused(call):
    try:
        call()
    except ConfigurationError as error:
        return error.code
    except Exception:  # noqa: BLE001 - a send that failed on the wire was not refused
        return None
    return None


def stock_session():
    from requests_futures.sessions import FuturesSession

    from fi.utils.executor import BoundedExecutor

    return FuturesSession(executor=BoundedExecutor(bound=4, max_workers=1))


# --- a caller-supplied session ----------------------------------------------------------------------------------

CALLER_CASES = {
    "ALL_PROXY only": ({"ALL_PROXY": "http://127.0.0.1:{a}"}, "http://example.com:{t}"),
    "an upper-case and a lower-case proxy that differ": (
        {"HTTP_PROXY": "http://127.0.0.1:{a}", "http_proxy": "http://127.0.0.1:{b}"}, "http://example.com:{t}"),
    "a NO_PROXY with a port": (
        {"http_proxy": "http://127.0.0.1:{a}", "NO_PROXY": "example.com:{t}", "no_proxy": "other.test"},
        "http://example.com:{t}"),
}


@pytest.mark.parametrize("case", list(CALLER_CASES))
def test_a_caller_session_with_a_proxy_in_the_environment_is_refused(rig, case):
    settings, base = CALLER_CASES[case]
    rig.env(FI_ALLOW_INSECURE_HTTP="1", **settings)
    base = base.format(t=rig.target.port)
    code = refused(lambda: evaluate_with(base, stock_session()))
    assert code == "KEYED_PROXY_REFUSED"
    assert rig.marker() == {"target": 0, "a": 0, "b": 0}
    assert rig.target.connections + rig.a.connections + rig.b.connections == 0


def test_a_cidr_no_proxy_that_holds_the_host_sends_direct_and_no_proxy_receives_a_byte(rig):
    # requests reads a CIDR range in NO_PROXY and sends direct; the proxy sinks see no connection and no marker byte.
    rig.env(FI_ALLOW_INSECURE_HTTP="1", http_proxy="http://127.0.0.1:{a}", no_proxy="127.0.0.0/8")
    refused(lambda: evaluate_with(f"http://127.0.0.1:{rig.target.port}", stock_session()))
    assert rig.target.marker_bytes > 0
    assert rig.a.connections == rig.b.connections == 0
    assert rig.a.marker_bytes == rig.b.marker_bytes == 0


def test_a_requests_session_sends_direct_with_a_dot_suffix_exemption(rig):
    # requests exempts the apex host even though httpx's pattern matches only subdomains.
    rig.env(FI_ALLOW_INSECURE_HTTP="1", HTTP_PROXY="http://127.0.0.1:{a}", NO_PROXY=".example.com")
    with stock_session() as session:
        assert evaluate_with(f"http://example.com:{rig.target.port}", session) == {}
    assert rig.target.marker_bytes > 0
    assert rig.a.connections == rig.b.connections == 0
    assert rig.a.marker_bytes == rig.b.marker_bytes == 0


@pytest.mark.parametrize("kind", ["client_with_proxy", "uninspectable_transport"])
def test_a_caller_session_that_routes_by_itself_is_refused(rig, kind):
    rig.env(FI_ALLOW_INSECURE_HTTP="1")
    ports = {"A": rig.a.port, "B": rig.b.port}
    code = refused(lambda: evaluate_with(f"http://example.com:{rig.target.port}", caller_session(kind, ports)))
    assert code == "KEYED_PROXY_REFUSED"
    assert rig.marker() == {"target": 0, "a": 0, "b": 0}


def test_a_caller_session_with_no_proxy_in_reach_sends_to_the_target(rig):
    rig.env(FI_ALLOW_INSECURE_HTTP="1")
    refused(lambda: evaluate_with(f"http://example.com:{rig.target.port}", stock_session()))
    assert rig.target.marker_bytes > 0
    assert rig.a.marker_bytes == rig.b.marker_bytes == 0


# --- a transport the SDK builds --------------------------------------------------------------------------------

def http_exporter(endpoint):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    return _create_exporter(ExporterConfig(type=ExporterType.FUTUREAGI, endpoint=endpoint, timeout_ms=1000))


@pytest.mark.parametrize("settings", [
    {"HTTP_PROXY": "http://127.0.0.1:{a}"},
    {"http_proxy": "http://127.0.0.1:{a}"},
    {"ALL_PROXY": "http://127.0.0.1:{a}"},
    {"all_proxy": "http://127.0.0.1:{a}", "NO_PROXY": "127.0.0.0/8"},
    {"HTTP_PROXY": "http://127.0.0.1:{a}", "http_proxy": "http://127.0.0.1:{b}"},
])
def test_the_http_exporter_to_loopback_ignores_a_proxy_in_the_environment(rig, settings):
    rig.env(**settings)
    export_through(http_exporter(f"http://127.0.0.1:{rig.target.port}/v1/traces"))
    assert rig.a.connections == rig.b.connections == 0
    assert rig.a.marker_bytes == rig.b.marker_bytes == 0
    assert rig.target.marker_bytes > 0


def test_the_http_exporter_to_a_self_hosted_target_ignores_a_proxy_in_the_environment(rig):
    rig.env(FI_ALLOW_INSECURE_HTTP="1", HTTP_PROXY="http://127.0.0.1:{a}", ALL_PROXY="http://127.0.0.1:{a}")
    export_through(http_exporter(f"http://collector.example:{rig.target.port}/v1/traces"))
    assert rig.a.connections == rig.b.connections == 0
    assert rig.target.marker_bytes > 0


def test_the_evaluation_request_to_loopback_ignores_a_proxy_in_the_environment(rig):
    rig.env(HTTP_PROXY="http://127.0.0.1:{a}", ALL_PROXY="http://127.0.0.1:{a}")
    refused(lambda: evaluate_with(f"http://127.0.0.1:{rig.target.port}"))
    assert rig.a.connections == rig.b.connections == 0
    assert rig.a.marker_bytes == rig.b.marker_bytes == 0
    assert rig.target.marker_bytes > 0


def test_the_grpc_exporter_to_loopback_ignores_a_proxy_in_the_environment(rig):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    rig.env(grpc_proxy="http://127.0.0.1:{a}", https_proxy="http://127.0.0.1:{a}", http_proxy="http://127.0.0.1:{a}")
    exporter = _create_exporter(ExporterConfig(
        type=ExporterType.OTLP_GRPC, endpoint=f"127.0.0.1:{rig.target.port}", insecure=True, timeout_ms=1000,
        headers={"x-api-key": KEY.decode(), "x-secret-key": SECRET.decode()}))
    try:
        export_through(exporter)
    except Exception:  # noqa: BLE001
        pass
    assert rig.a.connections == rig.b.connections == 0
    assert rig.a.marker_bytes == rig.b.marker_bytes == 0
    assert rig.target.connections > 0


def test_the_experiments_exporter_to_loopback_ignores_a_proxy_in_the_environment(rig):
    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._tracing.export_status import ExportStatus

    rig.env(HTTP_PROXY="http://127.0.0.1:{a}", http_proxy="http://127.0.0.1:{a}", ALL_PROXY="http://127.0.0.1:{a}")
    base = f"http://127.0.0.1:{rig.target.port}"
    outcome = ExportStatus("run-1", base, Redactor([]))
    provider = exporter_factory(base_url=base, api_key=KEY.decode(), secret_key=SECRET.decode(), project="p",
                                run_name="r", run_id="run-1", redactor=Redactor([]), outcome=outcome)()
    provider.get_tracer("measured").start_span("one").end()
    provider.force_flush(3000)
    provider.shutdown()
    assert rig.a.connections == rig.b.connections == 0
    assert rig.a.marker_bytes == rig.b.marker_bytes == 0
    assert rig.target.marker_bytes > 0


# --- redirects ---------------------------------------------------------------------------------------------------

def test_the_evaluation_request_does_not_follow_a_redirect(rig):
    rig.target.redirect = f"http://127.0.0.1:{rig.b.port}/elsewhere"
    code = None
    try:
        evaluate_with(f"http://127.0.0.1:{rig.target.port}")
    except Exception as error:  # noqa: BLE001
        code = error.get_error_code() if isinstance(error, KeyedRedirectRefusedError) else None
    assert code == "KEYED_REDIRECT_REFUSED"
    assert rig.b.connections == 0
    assert rig.b.marker_bytes == 0


def test_the_http_exporter_does_not_follow_a_redirect(rig):
    rig.target.redirect = f"http://127.0.0.1:{rig.b.port}/elsewhere"
    try:
        export_through(http_exporter(f"http://127.0.0.1:{rig.target.port}/v1/traces"))
    except Exception:  # noqa: BLE001
        pass
    assert rig.target.marker_bytes > 0
    assert rig.b.connections == 0
    assert rig.b.marker_bytes == 0


def test_an_http_exporter_with_the_keys_in_its_headers_does_not_follow_a_redirect(rig):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    rig.target.redirect = f"http://127.0.0.1:{rig.b.port}/elsewhere"
    exporter = _create_exporter(ExporterConfig(
        type=ExporterType.OTLP_HTTP, endpoint=f"http://127.0.0.1:{rig.target.port}/v1/traces", timeout_ms=1000,
        headers={"x-api-key": KEY.decode(), "x-secret-key": SECRET.decode()}))
    try:
        export_through(exporter)
    except Exception:  # noqa: BLE001
        pass
    assert rig.target.marker_bytes > 0
    assert rig.b.connections == 0 and rig.b.marker_bytes == 0


# --- the key headers in the OpenTelemetry environment --------------------------------------------------------------

VARIANTS = [
    {"OTEL_EXPORTER_OTLP_HEADERS": f"x-api-key={KEY.decode()},x-secret-key={SECRET.decode()}"},
    {"OTEL_EXPORTER_OTLP_TRACES_HEADERS": f"X-Api-Key={KEY.decode()}"},
    {"OTEL_EXPORTER_OTLP_HEADERS": f"authorization=x, X-Secret-Key={SECRET.decode()}"},
]


@pytest.mark.parametrize("settings", VARIANTS)
@pytest.mark.parametrize("kind", ["OTLP_HTTP", "OTLP_GRPC", "ARIZE"])
def test_key_headers_in_the_environment_are_refused_for_an_exporter_not_bound_for_future_agi(rig, settings, kind):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    rig.env(FI_ALLOW_INSECURE_HTTP="1", **settings)
    endpoint = (f"127.0.0.1:{rig.target.port}" if kind == "OTLP_GRPC"
                else f"http://127.0.0.1:{rig.target.port}/v1/traces")
    config = ExporterConfig(type=getattr(ExporterType, kind), endpoint=endpoint, timeout_ms=1000,
                            insecure=kind == "OTLP_GRPC")
    with pytest.raises(ConfigurationError) as refusal:
        _create_exporter(config)
    assert refusal.value.code == "otel_env_key_headers"
    for value in (KEY.decode(), SECRET.decode(), "127.0.0.1"):
        assert value not in str(refusal.value)
    assert rig.target.connections == 0
    assert rig.target.marker_bytes == rig.a.marker_bytes == rig.b.marker_bytes == 0


def test_other_headers_in_the_environment_are_left_alone(rig):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    rig.env(OTEL_EXPORTER_OTLP_HEADERS="authorization=Bearer-other,x-tenant=a")
    exporter = _create_exporter(ExporterConfig(
        type=ExporterType.OTLP_HTTP, endpoint=f"http://127.0.0.1:{rig.target.port}/v1/traces", timeout_ms=1000))
    assert exporter is not None
