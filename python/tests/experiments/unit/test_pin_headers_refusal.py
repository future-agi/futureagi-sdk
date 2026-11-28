# ruff: noqa: F811
"""An exporter bound for Future AGI whose headers cannot be pinned is refused, not warned about.

``pin_headers`` knows where the OTLP HTTP exporters (1.39 and 1.45) and the gRPC exporter keep
the headers they send. For any other shape it cannot replace them, so ambient
OTEL_EXPORTER_OTLP_HEADERS values could reach Future AGI. The build stops with a configuration
error that names the exporter class and the supported versions and carries no header or
environment values. Nothing is sent, and no unpinned exporter takes its place.
"""

import pytest

from fi._otlp_headers import pin_headers
from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    SDK_HEADERS,
    ambient,
    sink,
)


class Odd:
    pass


def test_an_exporter_of_an_unknown_shape_is_refused(ambient):
    with pytest.raises(ConfigurationError) as refused:
        pin_headers(Odd(), SDK_HEADERS)
    message = str(refused.value)
    assert "Odd" in message
    assert "supported versions" in message
    for secret in (*SDK_HEADERS.values(), "fake-ambient", "x-ambient"):
        assert secret not in message


def test_the_refusal_names_the_installed_exporter_version(ambient):
    from importlib.metadata import version

    with pytest.raises(ConfigurationError) as refused:
        pin_headers(Odd(), SDK_HEADERS)
    assert version("opentelemetry-exporter-otlp-proto-http") in str(refused.value)


class Hidden:
    """Wraps a real exporter and keeps every attribute pin_headers looks at out of sight."""

    def __init__(self, real):
        self._real = real

    def export(self, spans):
        return self._real.export(spans)

    def shutdown(self):
        return self._real.shutdown()

    def force_flush(self, timeout_millis=30000):
        return True


def test_no_request_reaches_the_sink_when_the_exporter_shape_is_unknown(ambient, sink, monkeypatch):
    """The run keeps going without exporting: nothing is sent, no unpinned exporter takes over, and
    the run reports a trace export failure after shutdown."""
    from fi_instrumentation import otel

    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._tracing.export_status import ExportStatus
    from fi.experiments.errors import TraceExportError

    real_class = otel.HTTPSpanExporter
    monkeypatch.setattr(otel, "HTTPSpanExporter", lambda **kwargs: Hidden(real_class(**kwargs)))
    outcome = ExportStatus("run-1", sink.base + "/tracer/v1/traces", Redactor([]))
    provider = exporter_factory(
        base_url=sink.base, api_key=SDK_HEADERS["x-api-key"], secret_key=SDK_HEADERS["x-secret-key"],
        project="p", run_name="r", run_id="run-1", redactor=Redactor([]), outcome=outcome)()
    provider.get_tracer("refusal-test").start_span("one").end()
    provider.force_flush()
    provider.shutdown()
    assert sink.requests == []
    assert isinstance(outcome.error, TraceExportError)
