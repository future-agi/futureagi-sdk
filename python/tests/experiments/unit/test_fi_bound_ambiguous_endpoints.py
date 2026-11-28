# ruff: noqa: F811
"""An exporter is not built for an endpoint that two parsers read differently.

``requests`` connects to the host ``urllib3`` parses, and the standard library can read another one from
the same text. An endpoint with a backslash, a percent sign, white space, a control character or more than
one ``@`` in its authority, or one whose two readings differ, is refused when the exporter is built, whether
or not either reading is a Future AGI host: ``fi.errors.ConfigurationError`` with code
``insecure_http_origin`` and a standard message that omits the endpoint.
"""

import pytest

from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_authority_forms import (  # noqa: F401
    clean_hosts,
    opted_in_sink,
    through_sink,
)
from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    ambient,
    evals_exporter,
    export_spans,
    sink,
)

CODE = "insecure_http_origin"

HTTP_FORMS = [
    # direction A: urllib3 dials a Future AGI host
    "http://api.futureagi.com\\@other-origin.example/v1/traces",
    "http://api.futureagi.com\\.other-origin.example/v1/traces",
    # direction B: urllib3 dials the other host
    "http://other-origin.example\\@api.futureagi.com/v1/traces",
    "http://other-origin.example\\@api.futureagi.com:80/v1/traces",
    # the same defects with no Future AGI host in them
    "http://other-origin.example\\@other.example/v1/traces",
    "http://%61pi.futureagi.com/v1/traces",
    "http://collector.example%2eother-origin.example/v1/traces",
    "http://collector.example%00.other-origin.example/v1/traces",
    "http://collector.example .other-origin.example/v1/traces",
    "http://collector.example\t.other-origin.example/v1/traces",
    "http://collector.example\x01.other-origin.example/v1/traces",
    "http://a@b@collector.example/v1/traces",
    # user information, an ``@`` in the path, and an empty authority
    "http://user:pw@collector.example.test/v1/traces",
    "http://collector.example.test/v1/@traces",
    "http:///collector.example.test/v1/traces",
    "http://a@api.futureagi.com@other-origin.example/v1/traces",
    # a name the two parsers do not read alike
    "http://ａpi.example.test/v1/traces",
]
GRPC_FORMS = [
    "api.futureagi.com\\@other-origin.example:443",
    "other-origin.example\\@grpc.futureagi.com:443",
    "evil\\@collector.example:4317",
    "dns:///grpc.futureagi.com\\@other-origin.example:443",
    "dns:///other-origin.example\\@grpc.futureagi.com:443",
    "dns://8.8.8.8\\@other-origin.example/grpc.futureagi.com:443",
    "dns:///collector.example%2eevil:443",
    "a@b@collector.example:4317",
    "collector.example :4317",
]
HTTP_KINDS = ["FUTUREAGI", "OTLP_HTTP", "ARIZE", "PHOENIX", "LANGFUSE"]


def build(kind, endpoint, **config):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    return _create_exporter(ExporterConfig(type=getattr(ExporterType, kind), endpoint=endpoint, **config))


@pytest.mark.parametrize("endpoint", HTTP_FORMS)
@pytest.mark.parametrize("kind", HTTP_KINDS)
def test_an_ambiguous_http_endpoint_is_refused_when_the_exporter_is_built(
    through_sink, clean_hosts, ambient, monkeypatch, kind, endpoint
):
    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")
    with pytest.raises(ConfigurationError) as refused:
        build(kind, endpoint)
    assert refused.value.code == CODE
    assert through_sink.requests == []


@pytest.mark.parametrize("endpoint", GRPC_FORMS)
def test_an_ambiguous_grpc_target_is_refused_when_the_exporter_is_built(clean_hosts, ambient, endpoint):
    with pytest.raises(ConfigurationError) as refused:
        build("OTLP_GRPC", endpoint)
    assert refused.value.code == CODE


def test_the_refusal_message_is_fixed_and_holds_no_endpoint_text(clean_hosts, ambient, monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")
    messages = set()
    for kind, endpoint in (
        ("OTLP_HTTP", "http://other-origin.example\\@api.futureagi.com/v1/traces"),
        ("FUTUREAGI", "http://api.futureagi.com\\@other-origin.example/v1/traces"),
        ("OTLP_GRPC", "evil\\@secret-collector.example:4317"),
    ):
        with pytest.raises(ConfigurationError) as refused:
            build(kind, endpoint)
        messages.add(str(refused.value))
    assert len(messages) == 1
    message = messages.pop().lower()
    for part in ("evil", "futureagi", "secret-collector", "example", "fi-key-value", "fi-secret-value", "\\"):
        assert part not in message


def test_an_ambiguous_fi_base_url_is_refused_for_the_futureagi_type(clean_hosts, ambient, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "https://other-origin.example\\@api.futureagi.com")
    with pytest.raises(ConfigurationError) as refused:
        build("FUTUREAGI", None)
    assert refused.value.code == CODE


@pytest.mark.parametrize("kind", ["OTLP_HTTP", "OTLP_GRPC"])
def test_the_tracer_setup_raises_the_refusal(clean_hosts, ambient, kind):
    from fi.evals.otel.config import ExporterConfig, ExporterType
    from fi.evals.otel.tracer import _create_exporter

    endpoint = "other-origin\\@grpc.futureagi.com:443" if kind == "OTLP_GRPC" else "http://other-origin.example\\@api.futureagi.com/v1"
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(ExporterConfig(type=getattr(ExporterType, kind), endpoint=endpoint))
    assert refused.value.code == CODE


# --- clean endpoints still work -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://collector.example.test:4318/v1/traces",
        "http://127.0.0.1:4318/v1/traces",
        "http://[::1]:4318/v1/traces",
        "http://bücher.example.test/v1/traces",
        "http://collector.example.test/v1/traces?x=a%20b#frag",
        "https://API.FUTUREAGI.COM./tracer/v1/traces",
    ],
)
def test_a_clean_http_endpoint_builds(clean_hosts, ambient, endpoint):
    assert build("OTLP_HTTP", endpoint) is not None


@pytest.mark.parametrize(
    "endpoint",
    [
        "collector.example.test:4317",
        "localhost:4317",
        "dns:///collector.example.test:4317",
        "dns://8.8.8.8/collector.example.test:4317",
        "ipv4:127.0.0.1:4317",
        "unix:/tmp/collector socket",
        "grpc.futureagi.com:443",
        "dns:///GRPC.FUTUREAGI.COM.:443",
    ],
)
def test_a_clean_grpc_target_builds(clean_hosts, ambient, endpoint):
    assert build("OTLP_GRPC", endpoint) is not None


def test_a_clean_futureagi_endpoint_sends_the_sdk_keys(opted_in_sink, clean_hosts, ambient, monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")
    port = opted_in_sink.server.server_address[1]
    monkeypatch.setenv("FI_BASE_URL", f"http://api.example.test:{port}")
    export_spans(evals_exporter(f"http://api.example.test:{port}/tracer/v1/traces", kind="OTLP_HTTP"))
    assert opted_in_sink.requests[0]["x-api-key"] == "fi-key-value"


# --- the experiments run exporter ------------------------------------------------------------------------


def test_a_run_with_an_ambiguous_endpoint_stores_items_and_reports_a_trace_export_failure(
    through_sink, clean_hosts, ambient
):
    """The refusal is caught as the unsupported-exporter refusal is: nothing is sent, no exporter takes its
    place, and the run reports a trace export failure after shutdown (exit 3)."""
    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._tracing.export_status import ExportStatus
    from fi.experiments.errors import TraceExportError

    from fi.errors import ConfigurationError

    endpoint = "http://ａpi.example.test/tracer/v1/traces"
    outcome = ExportStatus("run-1", endpoint, Redactor([]))
    try:
        provider = exporter_factory(
            base_url="http://ａpi.example.test", api_key="k-test-1234", secret_key="s-test-1234",
            project="p", run_name="r", run_id="run-1", redactor=Redactor([]), outcome=outcome,
            _endpoint=endpoint)()
    except ConfigurationError as error:
        # The non-ASCII host is refused when the exporter is built (the 0.8.1 rule), before any send.
        assert error.code == "insecure_http_origin"
        assert through_sink.requests == []
        return
    provider.get_tracer("refusal-test").start_span("one").end()
    provider.force_flush()
    provider.shutdown()
    assert through_sink.requests == []
    assert isinstance(outcome.error, TraceExportError)
