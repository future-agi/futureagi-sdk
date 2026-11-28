# ruff: noqa: F811
"""A session built for Future AGI does not follow redirects, and its refusals and host list are honest.

A redirect from a Future AGI endpoint to another host must not carry the SDK's keys along: the older
OpenTelemetry HTTP exporters post through a ``requests`` session that follows redirects, and a redirect
re-applies netrc credentials and forwards every header except ``Authorization``. A Future AGI-bound session
sets ``allow_redirects=False`` on every request, as the experiments run exporter's does, and keeps
``trust_env`` so the proxy and certificate settings the user configured still apply.
"""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    SDK_HEADERS,
    ambient,
    evals_exporter,
    export_one,
    export_spans,
    sink,
)
from tests.experiments.unit.test_fi_bound_exporter_session import netrc  # noqa: F401
from tests.experiments.unit.test_pin_headers_refusal import Hidden


class Redirector:
    """Answers every POST with a 307 to ``location``."""

    def __init__(self, location):
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                outer.requests.append({k.lower(): v for k, v in self.headers.items()})
                self.send_response(307)
                self.send_header("Location", location)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def redirected(sink):
    """A Future AGI endpoint that answers 307 to a second server; ``sink`` is the second server."""
    with Redirector(sink.base + "/collect") as first:
        yield first


def test_a_redirect_from_a_futureagi_endpoint_is_not_followed(
    redirected, sink, netrc, monkeypatch
):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult

    monkeypatch.setenv("FI_BASE_URL", redirected.base)
    exporter = evals_exporter(redirected.base + "/tracer/v1/traces", SDK_HEADERS)
    outcomes = []
    original = exporter.export

    def export(spans):
        try:
            result = original(spans)
        except Exception as error:  # the processors log what an exporter raises
            outcomes.append(error)
            raise
        outcomes.append(result)
        return result

    exporter.export = export
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    export_one(provider)

    assert len(redirected.requests) >= 1
    assert (
        sink.requests == []
    )  # the second server received nothing: no keys, no netrc credentials
    # The redirect is a failed export, not an accepted one.
    assert outcomes
    assert all(
        isinstance(outcome, Exception) or outcome == SpanExportResult.FAILURE
        for outcome in outcomes
    )


def test_the_futureagi_session_forces_no_redirects_and_keeps_trust_env():
    from fi._otlp_headers import futureagi_session

    session = futureagi_session()
    assert session.trust_env is True
    seen = {}

    def send(self, request, **kwargs):
        seen.update(kwargs)
        raise RuntimeError("stop")

    import requests

    original = requests.Session.send
    requests.Session.send = send
    try:
        with pytest.raises(RuntimeError):
            session.get("http://127.0.0.1:9/")
    finally:
        requests.Session.send = original
    assert seen["allow_redirects"] is False


# ---- the evals path raises the refusal ----------------------------------------------------------


def hidden_exporter(monkeypatch):
    from opentelemetry.exporter.otlp.proto.http import trace_exporter

    real = trace_exporter.OTLPSpanExporter
    monkeypatch.setattr(
        trace_exporter, "OTLPSpanExporter", lambda **kwargs: Hidden(real(**kwargs))
    )


@pytest.mark.parametrize("kind", ["FUTUREAGI", "OTLP_HTTP"])
def test_evals_refuses_an_exporter_of_an_unknown_shape_instead_of_dropping_spans(
    kind, monkeypatch
):
    hidden_exporter(monkeypatch)
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")
    with pytest.raises(ConfigurationError) as refused:
        evals_exporter("http://127.0.0.1:9/tracer/v1/traces", SDK_HEADERS, kind=kind)
    assert refused.value.code == "unsupported_otlp_exporter"
    assert "Hidden" in str(refused.value)


def test_evals_returns_none_for_other_exporter_errors(monkeypatch):
    from opentelemetry.exporter.otlp.proto.http import trace_exporter

    def broken(**kwargs):
        raise ValueError("not a configuration refusal")

    monkeypatch.setattr(trace_exporter, "OTLPSpanExporter", broken)
    assert evals_exporter("http://127.0.0.1:9/tracer/v1/traces", SDK_HEADERS) is None


# ---- the hosts that are Future AGI ----------------------------------------------------------


@pytest.fixture
def clean_hosts(monkeypatch):
    for name in ("FI_BASE_URL", "FI_GRPC_URL", "FI_TRACES_URL"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize(
    ("endpoint", "bound"),
    [
        ("https://api.futureagi.com/tracer/v1/traces", True),
        ("https://grpc.futureagi.com", True),
        ("grpc.futureagi.com:443", True),
        ("https://collector.example.test/v1/traces", False),
        ("localhost:4317", False),
        ("", False),
        (None, False),
    ],
)
def test_the_futureagi_hosts(clean_hosts, endpoint, bound):
    from fi._otlp_headers import is_future_agi_endpoint

    assert is_future_agi_endpoint(endpoint) is bound


@pytest.mark.parametrize(
    ("name", "value", "endpoint"),
    [
        ("FI_GRPC_URL", "https://grpc.eu.example.test:443", "grpc.eu.example.test:443"),
        (
            "FI_TRACES_URL",
            "https://traces.example.test/tracer/v1/traces",
            "https://traces.example.test/v1/traces",
        ),
        (
            "FI_BASE_URL",
            "https://api.example.test",
            "https://api.example.test/tracer/v1/traces",
        ),
    ],
)
def test_the_hosts_named_in_the_environment(
    clean_hosts, monkeypatch, name, value, endpoint
):
    from fi._otlp_headers import is_future_agi_endpoint

    assert is_future_agi_endpoint(endpoint) is False
    monkeypatch.setenv(name, value)
    assert is_future_agi_endpoint(endpoint) is True


def test_a_grpc_exporter_at_a_futureagi_host_is_pinned(clean_hosts, ambient):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    exporter = _create_exporter(
        ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint="grpc.futureagi.com:443")
    )
    sent = {key.lower(): value for key, value in exporter._headers}
    assert sent == {}


def test_a_grpc_exporter_at_another_host_keeps_the_ambient_headers(
    clean_hosts, ambient
):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    exporter = _create_exporter(
        ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint="localhost:4317")
    )
    sent = {key.lower(): value for key, value in exporter._headers}
    assert sent.get("x-ambient") == "1"


@pytest.mark.parametrize("kind", ["ARIZE", "PHOENIX", "LANGFUSE"])
def test_a_platform_exporter_at_the_futureagi_host_is_pinned(
    kind, sink, ambient, monkeypatch
):
    monkeypatch.setenv("FI_BASE_URL", sink.base)
    export_spans(evals_exporter(sink.base + "/v1/traces", kind=kind))
    assert sink.custom(sink.requests[0]) == {}


@pytest.mark.parametrize("kind", ["ARIZE", "PHOENIX", "LANGFUSE"])
def test_a_platform_exporter_at_another_host_keeps_the_ambient_headers(
    kind, sink, ambient, monkeypatch
):
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test")
    export_spans(evals_exporter(sink.base + "/v1/traces", kind=kind))
    assert sink.custom(sink.requests[0]) == {
        "authorization": "Bearer fake-ambient",
        "x-ambient": "1",
    }


# ---- an exporter that fi-instrumentation-otel refuses to build ---------------------------------


def test_a_refusal_from_the_instrumentation_package_is_a_stored_items_exit_3_outcome(
    sink, ambient, monkeypatch
):
    from fi_instrumentation import otel

    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._tracing.export_status import ExportStatus
    from fi.experiments.errors import TraceExportError

    class Unsupported(RuntimeError):
        pass

    def refuse(**kwargs):
        raise Unsupported("cannot send")

    monkeypatch.setattr(
        otel, "UnsupportedOTLPExporterError", Unsupported, raising=False
    )
    monkeypatch.setattr(otel, "HTTPSpanExporter", refuse)
    outcome = ExportStatus("run-1", sink.base + "/tracer/v1/traces", Redactor([]))
    provider = exporter_factory(
        base_url=sink.base,
        api_key=SDK_HEADERS["x-api-key"],
        secret_key=SDK_HEADERS["x-secret-key"],
        project="p",
        run_name="r",
        run_id="run-1",
        redactor=Redactor([]),
        outcome=outcome,
    )()
    provider.get_tracer("refusal-test").start_span("one").end()
    provider.force_flush()
    provider.shutdown()
    assert sink.requests == []
    assert isinstance(outcome.error, TraceExportError)
