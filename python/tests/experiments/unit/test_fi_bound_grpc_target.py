# ruff: noqa: F811
"""A gRPC exporter is classified by the exact target its channel dials.

The OpenTelemetry gRPC exporter replaces the endpoint with ``urlparse(endpoint).netloc`` when that is not
empty. For a DNS resolver URL with an authority, the exporter passes that authority to gRPC rather than
the path. For an HTTPS URL with user information, the authority is not a plain host name. A Future AGI
exporter is built only for an unambiguous Future AGI target, and its channel carries the SDK's keys
to no other host.
"""

import pytest

from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_ambiguous_endpoints import CODE, build
from tests.experiments.unit.test_fi_bound_authority_forms import (  # noqa: F401
    clean_hosts,
    through_sink,
)
from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    ambient,
    sink,
)

FI_HOSTS = {"api.futureagi.com", "grpc.futureagi.com"}


@pytest.fixture
def channels(monkeypatch):
    """The target string every gRPC channel is opened with."""
    from opentelemetry.exporter.otlp.proto.grpc import exporter as grpc_exporter

    seen = []
    for name in ("secure_channel", "insecure_channel"):
        original = getattr(grpc_exporter, name)

        def make(target, *args, _original=original, **kwargs):
            seen.append(target)
            return _original(target, *args, **kwargs)

        monkeypatch.setattr(grpc_exporter, name, make)
    return seen


@pytest.fixture
def keys(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")


def dialed_host(target):
    """The host gRPC resolves from a target, or None when the target is not a plain host[:port]."""
    target = target.removeprefix("dns:///")
    if any(ch in target for ch in "@/\\%[]") or target.count(":") > 1:
        return None
    host = target.split(":")[0].lower().removesuffix(".")
    return host or None


def metadata_keys(exporter):
    return {str(name).lower() for name, _ in exporter._headers}


# Every form of the brief. "refused": no exporter is built (insecure_http_origin). "fi": built with the
# SDK's keys, and the channel dials a Future AGI host. "other": built with no Future AGI key.
GRPC_FORMS = [
    # the dns authority names the host that is dialed
    ("dns://other-origin.example/grpc.futureagi.com:443", "refused"),
    ("dns://8.8.8.8/grpc.futureagi.com:443", "refused"),
    ("dns://8.8.8.8:53/grpc.futureagi.com:443", "refused"),
    ("dns://grpc.futureagi.com/other-origin.example:443", "refused"),
    ("dns://grpc.futureagi.com", "refused"),
    ("DNS://other-origin.example/grpc.futureagi.com:443", "refused"),
    # user information and target grammar behind a URL form
    ("https://ipv4:203.0.113.5:443@grpc.futureagi.com", "refused"),
    ("https://user@grpc.futureagi.com:443", "refused"),
    ("https://user:pw@grpc.futureagi.com:443", "refused"),
    ("https://unix:/tmp/sock@grpc.futureagi.com", "refused"),
    # a target-grammar prefix with a Future AGI name in it
    ("ipv4:203.0.113.5:443,grpc.futureagi.com:443", "refused"),
    ("ipv6:[::1]:443,grpc.futureagi.com:443", "refused"),
    ("unix:grpc.futureagi.com", "refused"),
    ("unix-abstract:grpc.futureagi.com", "refused"),
    ("vsock:grpc.futureagi.com", "refused"),
    ("dns:grpc.futureagi.com:443", "refused"),
    ("DNS:///grpc.futureagi.com:443", "refused"),
    ("Dns:///grpc.futureagi.com:443", "refused"),
    ("xds:///grpc.futureagi.com", "refused"),
    ("google-c2p:///grpc.futureagi.com", "refused"),
    ("dns:///grpc.futureagi.com/other-origin.example:443", "refused"),
    # percent-encoded name
    ("grpc.futureagi%2ecom:443", "refused"),
    ("https://grpc%2efutureagi.com", "refused"),
    ("https://grpc.futureagi.com%3a443", "refused"),
    ("https://other-origin.example%40grpc.futureagi.com", "refused"),
    # the host that is dialed decides the class
    ("//grpc.futureagi.com:443", "fi"),
    ("//api.futureagi.com", "fi"),
    # plain Future AGI forms stay Future AGI
    ("grpc.futureagi.com:443", "fi"),
    ("grpc.futureagi.com", "fi"),
    ("https://grpc.futureagi.com:443", "fi"),
    ("HTTPS://GRPC.FUTUREAGI.COM:443", "fi"),
    ("dns:///grpc.futureagi.com:443", "fi"),
    ("dns:///grpc.futureagi.com", "fi"),
    ("dns:///GRPC.FUTUREAGI.COM.:443", "fi"),
    ("grpc.futureagi.com.:443", "fi"),
    ("api.futureagi.com:443", "fi"),
    # other backends are untouched
    ("collector.example.test:4317", "other"),
    ("localhost:4317", "other"),
    ("dns:///collector.example.test:4317", "other"),
    ("dns://8.8.8.8/collector.example.test:4317", "other"),
    ("https://collector.example.test:4317", "other"),
    ("//collector.example.test:4317", "other"),
    ("ipv4:127.0.0.1:4317", "other"),
    ("ipv6:[::1]:4317", "other"),
    ("[::1]:4317", "other"),
    ("unix:/tmp/collector.sock", "other"),
    ("grpc.futureagi.com.other-origin.example:443", "other"),
    ("othergrpc.futureagi.com:443", "other"),
    ("dns:///grpc.futureagi.com.other-origin.example:443", "other"),
]


@pytest.mark.parametrize(("endpoint", "outcome"), GRPC_FORMS, ids=[f"{o}:{e}" for e, o in GRPC_FORMS])
def test_the_grpc_form_table(clean_hosts, ambient, keys, channels, endpoint, outcome):
    if outcome == "refused":
        with pytest.raises(ConfigurationError) as refused:
            build("OTLP_GRPC", endpoint)
        assert refused.value.code == CODE
        assert channels == []
        return
    exporter = build("OTLP_GRPC", endpoint)
    assert len(channels) == 1
    host = dialed_host(channels[0])
    if outcome == "fi":
        assert host in FI_HOSTS
        assert metadata_keys(exporter) == {"x-api-key", "x-secret-key"}
    else:
        assert host not in FI_HOSTS
        assert not metadata_keys(exporter) & {"x-api-key", "x-secret-key"}


@pytest.mark.parametrize("endpoint", [e for e, _ in GRPC_FORMS], ids=[e for e, _ in GRPC_FORMS])
def test_no_channel_that_dials_another_host_carries_a_futureagi_key(
    clean_hosts, ambient, keys, channels, endpoint
):
    """The property behind the table: whatever the form, a built exporter's keys go only to a Future AGI host,
    and a channel that dials a Future AGI host carries only the SDK's headers."""
    try:
        exporter = build("OTLP_GRPC", endpoint)
    except ConfigurationError as refusal:
        assert refusal.code == CODE
        return
    carries_keys = bool(metadata_keys(exporter) & {"x-api-key", "x-secret-key"})
    host = dialed_host(channels[0])
    if carries_keys:
        assert host in FI_HOSTS
    if host in FI_HOSTS:
        assert metadata_keys(exporter) == {"x-api-key", "x-secret-key"}


@pytest.mark.parametrize("kind", ["FUTUREAGI", "OTLP_HTTP", "ARIZE", "PHOENIX", "LANGFUSE"])
def test_http_endpoints_are_unchanged(through_sink, clean_hosts, ambient, keys, kind):
    exporter = build(kind, "https://api.futureagi.com/tracer/v1/traces")
    assert exporter is not None
    exporter = build("OTLP_HTTP", "http://collector.example.test:4318/v1/traces")
    assert exporter is not None
    with pytest.raises(ConfigurationError) as refused:
        build(kind, "http://other-origin.example\\@api.futureagi.com/tracer/v1/traces")
    assert refused.value.code == CODE
    assert through_sink.requests == []


# --- an endpoint taken from the environment ------------------------------------------------------------


@pytest.mark.parametrize("kind", ["ARIZE", "PHOENIX", "LANGFUSE"])
@pytest.mark.parametrize("variable", ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "OTEL_EXPORTER_OTLP_ENDPOINT"])
@pytest.mark.parametrize(
    "value",
    [
        "http://other-origin.example\\@api.futureagi.com/v1/traces",
        "http://api.futureagi.com\\@other-origin.example/v1/traces",
        "http://%61pi.futureagi.com/v1/traces",
        "http://a@b@collector.example.test/v1/traces",
    ],
)
def test_an_ambiguous_endpoint_from_the_environment_is_refused(
    through_sink, clean_hosts, ambient, keys, monkeypatch, kind, variable, value
):
    monkeypatch.setenv(variable, value)
    with pytest.raises(ConfigurationError) as refused:
        build(kind, None)
    assert refused.value.code == CODE
    assert through_sink.requests == []


@pytest.mark.parametrize("kind", ["ARIZE", "PHOENIX", "LANGFUSE"])
@pytest.mark.parametrize("variable", ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "OTEL_EXPORTER_OTLP_ENDPOINT"])
def test_a_futureagi_endpoint_from_the_environment_gets_the_sdk_headers_only(
    clean_hosts, ambient, keys, monkeypatch, kind, variable
):
    monkeypatch.setenv(variable, "https://api.futureagi.com")
    exporter = build(kind, None)
    headers = {k.lower() for k in (getattr(exporter, "_headers", None) or exporter._client._headers)}
    assert {"x-api-key", "x-secret-key"} <= headers
    assert "authorization" not in headers and "x-ambient" not in headers


# --- an injected exporter ----------------------------------------------------------------------------


def run_with_inner(inner):
    """Run one span through the run exporter around ``inner``; returns the outcome and the batches ``inner`` got."""
    from opentelemetry.sdk.trace.export import SpanExportResult

    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._tracing.export_status import ExportStatus

    outcome = ExportStatus("run-1", "http://api.example.test/tracer/v1/traces", Redactor([]))
    received = []
    inner.export = lambda spans: received.append(list(spans)) or SpanExportResult.SUCCESS
    provider = exporter_factory(
        base_url="http://api.example.test", api_key="k-test-1234", secret_key="s-test-1234",
        project="p", run_name="r", run_id="run-1", redactor=Redactor([]), outcome=outcome, inner=inner,
        _endpoint="http://api.example.test/tracer/v1/traces")()
    provider.get_tracer("inner-test").start_span("one").end()
    provider.force_flush()
    provider.shutdown()
    return outcome, received


def test_an_injected_exporter_with_an_ambiguous_endpoint_is_refused(through_sink, clean_hosts, ambient):
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    from fi.experiments.errors import TraceExportError

    inner = OTLPSpanExporter(endpoint="http://other-origin.example\\@api.futureagi.com/v1/traces")
    outcome, received = run_with_inner(inner)
    assert through_sink.requests == [] and received == []
    assert isinstance(outcome.error, TraceExportError)


def test_an_injected_grpc_exporter_with_an_unreadable_futureagi_target_is_refused(clean_hosts, ambient):
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    from fi.experiments.errors import TraceExportError

    inner = OTLPSpanExporter(endpoint="https://ipv4:203.0.113.5:443@grpc.futureagi.com")
    outcome, received = run_with_inner(inner)
    assert received == []
    assert isinstance(outcome.error, TraceExportError)


def test_an_injected_otlp_exporter_whose_target_cannot_be_read_is_refused(through_sink, clean_hosts, ambient):
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    from fi.experiments.errors import TraceExportError

    inner = OTLPSpanExporter(endpoint="collector.example.test:4317")
    inner._endpoint = None
    outcome, received = run_with_inner(inner)
    assert received == []
    assert isinstance(outcome.error, TraceExportError)


# --- a certificate file that is missing ---------------------------------------------------------------


@pytest.mark.parametrize(
    "variable",
    [
        "OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE",
        "OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY",
        "OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE",
    ],
)
def test_a_missing_tls_file_is_refused_and_its_path_is_not_echoed(
    clean_hosts, ambient, keys, monkeypatch, tmp_path, variable
):
    present = tmp_path / "present.pem"
    present.write_bytes(b"not a certificate")
    for name in (
        "OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE",
        "OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY",
        "OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE",
    ):
        monkeypatch.setenv(name, str(present))
    monkeypatch.setenv(variable, str(tmp_path / "secret-dir-name" / "missing.pem"))
    with pytest.raises(ConfigurationError) as refused:
        build("OTLP_GRPC", "grpc.futureagi.com:443")
    assert refused.value.code == "unreadable_tls_file"
    message = str(refused.value)
    assert variable in message
    assert "secret-dir-name" not in message and "missing.pem" not in message


def test_a_missing_tls_file_does_not_matter_for_another_backend(clean_hosts, ambient, monkeypatch, tmp_path):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE", str(tmp_path / "missing.pem"))
    assert build("OTLP_GRPC", "collector.example.test:4317") is not None
