"""OTLP exporters bound for Future AGI send the SDK's own headers and leave os.environ alone.

Newer OpenTelemetry HTTP exporters merge OTEL_EXPORTER_OTLP_HEADERS and
OTEL_EXPORTER_OTLP_TRACES_HEADERS into the headers they are given. A header meant for another
backend must not reach a Future AGI endpoint, and building an exporter must not change the
process environment for the user's own threads. An exporter that points at an endpoint the
user chose keeps the standard OpenTelemetry environment behaviour.

A local HTTP sink records the headers of every export. Everything runs on loopback.
"""

import functools
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

AMBIENT_VARS = ("OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_TRACES_HEADERS")
AMBIENT = "Authorization=Bearer fake-ambient,x-ambient=1"
SDK_HEADERS = {"x-api-key": "k-test-1234", "x-secret-key": "s-test-1234"}
# What the HTTP transport itself adds to every request, whoever builds the exporter.
TRANSPORT = {"host", "content-length", "content-type", "content-encoding", "user-agent",
             "accept", "accept-encoding", "connection"}


class Sink:
    def __init__(self):
        self.requests = []
        sink = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                sink.requests.append({k.lower(): v for k, v in self.headers.items()})
                self.send_response(200)
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

    def custom(self, headers):
        """Header names the request carried beyond the transport's own."""
        return {k: v for k, v in headers.items() if k not in TRANSPORT}


@pytest.fixture
def sink():
    with Sink() as s:
        yield s


@pytest.fixture
def ambient(monkeypatch):
    for name in AMBIENT_VARS:
        monkeypatch.setenv(name, AMBIENT)
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.delenv("FI_SECRET_KEY", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)


def observe_env_while_building(monkeypatch, seen):
    """Record the ambient variables as another thread sees them while an exporter is constructed."""
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    original = OTLPSpanExporter.__init__

    @functools.wraps(original)
    def init(self, *args, **kwargs):
        def look():
            seen.append({k: os.environ.get(k) for k in AMBIENT_VARS})

        thread = threading.Thread(target=look)
        thread.start()
        thread.join()
        original(self, *args, **kwargs)

    monkeypatch.setattr(OTLPSpanExporter, "__init__", init)


def export_one(provider):
    provider.get_tracer("headers-test").start_span("one").end()
    provider.force_flush()
    provider.shutdown()


# ---- site 1: the experiments run exporter -------------------------------------------------------


def run_provider(base):
    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import exporter_factory

    return exporter_factory(base_url=base, api_key=SDK_HEADERS["x-api-key"], secret_key=SDK_HEADERS["x-secret-key"],
                            project="p", run_name="r", run_id="run-1", redactor=Redactor([]))()


def test_run_exporter_sends_only_the_sdk_headers(sink, ambient):
    export_one(run_provider(sink.base))
    assert len(sink.requests) == 1
    assert sink.custom(sink.requests[0]) == SDK_HEADERS


def test_run_exporter_leaves_the_environment_unchanged_while_building(sink, ambient, monkeypatch):
    seen = []
    observe_env_while_building(monkeypatch, seen)
    before = dict(os.environ)
    provider = run_provider(sink.base)
    assert seen == [{k: AMBIENT for k in AMBIENT_VARS}]
    assert dict(os.environ) == before
    export_one(provider)
    assert dict(os.environ) == before


def test_run_exporter_ignores_ambient_headers_set_after_building(sink, monkeypatch):
    for name in AMBIENT_VARS:
        monkeypatch.delenv(name, raising=False)
    provider = run_provider(sink.base)
    for name in AMBIENT_VARS:
        monkeypatch.setenv(name, AMBIENT)
    export_one(provider)
    assert sink.custom(sink.requests[0]) == SDK_HEADERS


# ---- site 2: the evals OpenTelemetry exporter for Future AGI ------------------------------------


def evals_exporter(endpoint, headers=None, kind="FUTUREAGI"):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    return _create_exporter(ExporterConfig(type=getattr(ExporterType, kind), endpoint=endpoint,
                                           headers=dict(headers or {})))


def export_spans(exporter):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    export_one(provider)


def test_evals_futureagi_exporter_with_configured_headers_sends_only_those(sink, ambient):
    export_spans(evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS))
    assert sink.custom(sink.requests[0]) == SDK_HEADERS


def test_evals_futureagi_exporter_with_environment_keys_sends_only_the_keys(sink, ambient, monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "k-test-1234")
    monkeypatch.setenv("FI_SECRET_KEY", "s-test-1234")
    export_spans(evals_exporter(sink.base + "/tracer/v1/traces"))
    assert sink.custom(sink.requests[0]) == SDK_HEADERS


def test_evals_futureagi_exporter_without_keys_sends_no_ambient_header(sink, ambient):
    export_spans(evals_exporter(sink.base + "/tracer/v1/traces"))
    assert sink.custom(sink.requests[0]) == {}


def test_evals_futureagi_exporter_leaves_the_environment_unchanged_while_building(sink, ambient, monkeypatch):
    seen = []
    observe_env_while_building(monkeypatch, seen)
    before = dict(os.environ)
    exporter = evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS)
    assert seen == [{k: AMBIENT for k in AMBIENT_VARS}]
    assert dict(os.environ) == before
    export_spans(exporter)
    assert dict(os.environ) == before


def test_evals_futureagi_exporter_ignores_ambient_headers_set_after_building(sink, monkeypatch):
    for name in AMBIENT_VARS:
        monkeypatch.delenv(name, raising=False)
    exporter = evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS)
    for name in AMBIENT_VARS:
        monkeypatch.setenv(name, AMBIENT)
    export_spans(exporter)
    assert sink.custom(sink.requests[0]) == SDK_HEADERS


# ---- a user-chosen endpoint keeps the standard OpenTelemetry environment behaviour --------------


def test_user_chosen_endpoint_receives_the_ambient_headers(sink, ambient, monkeypatch):
    # An endpoint on the host of FI_BASE_URL is bound for Future AGI; this one is on another host.
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test")
    export_spans(evals_exporter(sink.base + "/v1/traces", kind="OTLP_HTTP"))
    assert sink.custom(sink.requests[0]) == {"authorization": "Bearer fake-ambient", "x-ambient": "1"}
