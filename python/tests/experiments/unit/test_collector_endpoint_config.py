"""Experiment collector configuration, credential scope and value-free diagnostics."""

import json
import sys
from types import ModuleType, SimpleNamespace
import warnings

import pytest
import requests
from opentelemetry.sdk.trace.export import SpanExportResult

from fi._extra_headers import ExtraHeaders
from fi.experiments._redact import Redactor
from fi.experiments._tracing import export as tracing_export
from fi.experiments._tracing.export_status import ExportSession, ExportStatus
from fi.experiments._upload_session import UploadSession
from fi.experiments.errors import ExperimentError, TraceExportError, TraceExportWarning


@pytest.fixture(autouse=True)
def isolated_endpoint_environment(monkeypatch):
    for name in (
        "FI_BASE_URL", "FI_COLLECTOR_ENDPOINT", "FI_EXTRA_HEADERS", "FI_API_KEY", "FI_SECRET_KEY",
        "OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        "OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_TRACES_HEADERS",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def provider_capture(monkeypatch):
    """Exercise the delayed factory without starting a batch worker or global provider."""
    import opentelemetry.sdk.trace
    import opentelemetry.sdk.trace.export

    class Provider:
        def __init__(self, **kwargs):
            self.processors = []

        def add_span_processor(self, processor):
            self.processors.append(processor)

    monkeypatch.setattr(opentelemetry.sdk.trace, "TracerProvider", Provider)
    monkeypatch.setattr(opentelemetry.sdk.trace.export, "BatchSpanProcessor",
                        lambda exporter: SimpleNamespace(exporter=exporter))


@pytest.fixture
def exporter_calls(monkeypatch, provider_capture):
    calls = []

    class Exporter:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def export(self, spans):
            return SpanExportResult.SUCCESS

        def force_flush(self, timeout_millis=30000):
            return True

        def shutdown(self):
            pass

    package = ModuleType("fi_instrumentation")
    package.__path__ = []
    otel = ModuleType("fi_instrumentation.otel")
    otel.HTTPSpanExporter = Exporter
    package.otel = otel
    monkeypatch.setitem(sys.modules, "fi_instrumentation", package)
    monkeypatch.setitem(sys.modules, "fi_instrumentation.otel", otel)
    return calls


def _factory(base_url="https://api.example.test", **kwargs):
    return tracing_export.exporter_factory(
        base_url=base_url, api_key="test-run-api", secret_key="test-run-secret",
        project="test-project", run_name="test-run", run_id="test-run-id", redactor=Redactor(), **kwargs,
    )


def _session(base_url="http://localhost:8000", *, client_extras=True):
    client = SimpleNamespace(base_url=base_url,
                             auth=SimpleNamespace(api_key="test-run-api", secret_key="test-run-secret"))
    if client_extras:
        client._extra_headers = ExtraHeaders(base_url, {"X-Client-Only": "test-client-header"})
    return UploadSession(client=client, dataset=None)


def _session_factory(session):
    return session.exporter_factory(project="test-project", run_name="test-run", run_id="test-run-id",
                                    redactor=Redactor())


def test_self_host_api_and_trace_ports_are_independent(monkeypatch, exporter_calls):
    monkeypatch.setenv("FI_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", "http://localhost:4318/v1/traces")
    session = _session()
    _session_factory(session)()
    assert session.base_url == "http://localhost:8000"
    assert exporter_calls[0]["endpoint"] == "http://localhost:4318/v1/traces"
    assert session.export_status.endpoint == "http://localhost:4318"
    assert exporter_calls[0]["session"].outcome is session.export_status


@pytest.mark.parametrize("endpoint", [
    "https://collector.example.test/custom/trace/path/",
    "https://collector.example.test/v1/traces",
    "https://collector.example.test/opaque%2Fsegment",
    "https://collector.example.test",
], ids=["custom-path", "otlp-path", "escaped-path", "origin"])
def test_explicit_full_url_wins_without_appending(monkeypatch, endpoint):
    monkeypatch.setenv("FI_BASE_URL", "https://ambient-api.example.test")
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", endpoint)
    assert tracing_export.collector_endpoint("https://client-api.example.test/prefix/") == endpoint


@pytest.mark.parametrize("setting", [None, ""], ids=["unset", "empty"])
def test_hosted_fallback_keeps_legacy_path(monkeypatch, setting):
    if setting is not None:
        monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", setting)
    assert tracing_export.collector_endpoint("https://api.example.test/prefix///") == (
        "https://api.example.test/prefix/tracer/v1/traces"
    )


def test_ambient_otel_destinations_and_headers_are_not_selected(monkeypatch, exporter_calls):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://foreign.example.test/base")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "https://foreign.example.test/traces")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "Authorization=test-foreign-header")
    _factory()()
    assert exporter_calls[0]["endpoint"] == "https://api.example.test/tracer/v1/traces"
    assert exporter_calls[0]["headers"] == {"X-Api-Key": "test-run-api", "X-Secret-Key": "test-run-secret"}


def test_real_http_exporter_ignores_ambient_otel_headers(monkeypatch, provider_capture):
    """Use traceAI's real constructor and OTLP serializer, with an in-memory HTTP adapter."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://foreign.example.test/base")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "https://foreign.example.test/traces")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "Authorization=test-foreign-header,X-Ambient=test-ambient")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_HEADERS", "X-Ambient-Traces=test-ambient-traces")
    sent = []

    def send(adapter, request, **kwargs):
        sent.append(request)
        response = requests.Response()
        response.status_code = 200
        response._content = b""
        response.request = request
        response.url = request.url
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    provider = _factory()()
    exporter = provider.processors[0].exporter
    try:
        assert exporter.export([]) == SpanExportResult.SUCCESS
    finally:
        exporter.shutdown()
    assert len(sent) == 1
    assert sent[0].url == "https://api.example.test/tracer/v1/traces"
    assert sent[0].headers["X-Api-Key"] == "test-run-api"
    assert sent[0].headers["X-Secret-Key"] == "test-run-secret"
    assert "Authorization" not in sent[0].headers
    assert "X-Ambient" not in sent[0].headers
    assert "X-Ambient-Traces" not in sent[0].headers


@pytest.mark.parametrize("endpoint", [
    "http://localhost:4318/v1/traces", "https://collector.example.test:8443/custom/traces",
], ids=["different-port", "different-host"])
def test_explicit_collector_receives_run_keys_not_extra_headers(monkeypatch, exporter_calls, endpoint):
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", endpoint)
    monkeypatch.setenv("FI_API_KEY", "test-ambient-api")
    monkeypatch.setenv("FI_SECRET_KEY", "test-ambient-secret")
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Environment-Only=test-environment-header")
    _session_factory(_session())()
    assert exporter_calls[0]["headers"] == {"X-Api-Key": "test-run-api", "X-Secret-Key": "test-run-secret"}
    assert exporter_calls[0]["endpoint"] == endpoint


def test_legacy_destination_keeps_origin_bound_extras(monkeypatch, exporter_calls):
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Environment-Only=test-environment-header")
    _session_factory(_session())()
    assert exporter_calls[0]["headers"] == {
        "X-Api-Key": "test-run-api", "X-Secret-Key": "test-run-secret",
        "X-Client-Only": "test-client-header", "X-Environment-Only": "test-environment-header",
    }


def test_explicit_same_origin_keeps_extras(monkeypatch, exporter_calls):
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", "https://api.example.test/prefix/custom/traces")
    _session_factory(_session("https://api.example.test/prefix"))()
    assert exporter_calls[0]["headers"]["X-Client-Only"] == "test-client-header"
    assert exporter_calls[0]["endpoint"] == "https://api.example.test/prefix/custom/traces"


def test_explicit_outside_base_path_does_not_widen_extra_header_scope(monkeypatch, exporter_calls):
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", "https://api.example.test/other/traces")
    _session_factory(_session("https://api.example.test/prefix"))()
    assert "X-Client-Only" not in exporter_calls[0]["headers"]


def test_test_double_client_extra_headers_remain_origin_bound(monkeypatch, exporter_calls):
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", "http://localhost:4318/v1/traces")
    monkeypatch.setenv("FI_EXTRA_HEADERS", "X-Environment-Only=test-environment-header")
    _session_factory(_session(client_extras=False))()
    assert "X-Environment-Only" not in exporter_calls[0]["headers"]


@pytest.mark.parametrize("explicit", [False, True], ids=["legacy", "explicit"])
def test_delayed_factory_snapshots_destination(monkeypatch, exporter_calls, explicit):
    expected = "https://api.example.test/tracer/v1/traces"
    if explicit:
        expected = "https://collector.example.test/original/traces"
        monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", expected)
    make = _factory()
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", "https://later.example.test/new/traces")
    make()
    assert exporter_calls[0]["endpoint"] == expected


def test_upload_session_resolves_once_for_status_headers_and_delayed_export(monkeypatch, exporter_calls):
    first = "http://localhost:4318/first/traces"
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", first)
    session = _session()
    original_resolve = tracing_export.collector_endpoint
    original_headers = session.extra_headers
    resolved = []
    selected = []

    def resolve(base):
        resolved.append(base)
        return original_resolve(base)

    def headers(endpoint):
        selected.append(endpoint)
        monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", "https://later.example.test/second/traces")
        return original_headers(endpoint)

    monkeypatch.setattr(tracing_export, "collector_endpoint", resolve)
    monkeypatch.setattr(session, "extra_headers", headers)
    make = _session_factory(session)
    make()
    assert len(resolved) == 1
    assert selected == [first]
    assert exporter_calls[0]["endpoint"] == first
    assert exporter_calls[0]["session"].outcome is session.export_status
    assert session.export_status.endpoint == "http://localhost:4318"


@pytest.mark.parametrize("endpoint", [
    "https://collector.example.test:443/v1/traces",
    "http://localhost:4318/v1/traces",
    "http://127.0.0.1:4318/v1/traces",
    "http://127.2.3.4:4318/v1/traces",
    "http://[::1]:4318/v1/traces",
], ids=["https", "localhost", "ipv4", "ipv4-range", "ipv6"])
def test_secure_or_loopback_destinations_are_valid(monkeypatch, endpoint):
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", endpoint)
    assert tracing_export.collector_endpoint("https://api.example.test") == endpoint


@pytest.mark.parametrize("endpoint", [
    "not-a-url", "/v1/traces", "ftp://collector.example.test/traces",
    "http://collector.example.test/traces", "http://localhost.evil.test/traces",
    "http://192.168.1.1:4318/traces", "http://[::2]:4318/traces",
    "https:///traces", "https://collector.example.test:/traces",
    "https://collector.example.test:bad/traces", "https://collector.example.test:65536/traces",
    "https://collector.example.test:0/traces", "https://[::1/traces",
    "https://test-user:test-sensitive-value@collector.example.test/traces",
    "https://collector.example.test/traces?api_key=test-sensitive-value",
    "https://collector.example.test/traces?tenant=test-sensitive-value",
    "https://collector.example.test/traces?", "https://collector.example.test/traces#test-sensitive-value",
    " https://collector.example.test/traces", "https://collector.example.test/traces\n",
    "https://collector.example.test/\ttraces", "https://collector.example.test/\x00traces",
    "https://collector.example.test/%0d%0atraces", "https://collector.example.test/%zz",
    "https://collector.example.test\\@other.example.test/traces", "https://bad host.example.test/traces",
    "https://bad..example.test/traces", "   ",
], ids=[
    "no-scheme", "relative", "wrong-scheme", "remote-http", "localhost-suffix", "private-http", "ipv6-remote-http",
    "no-host", "empty-port", "nonnumeric-port", "port-too-large", "zero-port", "unclosed-ipv6",
    "userinfo", "credential-query", "other-query", "empty-query", "fragment", "leading-space", "newline", "tab",
    "nul", "encoded-control", "bad-escape", "backslash", "host-space", "empty-host-label", "blank",
])
def test_invalid_explicit_destination_fails_without_echo(monkeypatch, endpoint, capsys, caplog):
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", endpoint)
    with pytest.raises(ExperimentError, match="FI_COLLECTOR_ENDPOINT") as caught:
        _factory()
    assert caught.value.exit_code == 3
    diagnostic = str(caught.value) + json.dumps(caught.value.to_json()) + caplog.text
    output = capsys.readouterr()
    diagnostic += output.out + output.err
    assert "test-sensitive-value" not in diagnostic
    assert "collector.example.test" not in diagnostic
    assert endpoint not in diagnostic
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__


def test_invalid_legacy_destination_is_rejected_without_echo():
    with pytest.raises(ExperimentError, match="FI_COLLECTOR_ENDPOINT") as caught:
        _factory("http://test-user:test-sensitive-value@remote.example.test")
    assert "remote.example.test" not in str(caught.value)
    assert "test-sensitive-value" not in str(caught.value)


def test_status_warning_and_json_disclose_only_origin():
    status = ExportStatus("test-run-id", "https://test-user:test-sensitive-value@collector.example.test:8443/"
                          "private-path?token=test-sensitive-value#private-fragment", Redactor())
    status.status_code = 503
    status.failed()
    assert status.endpoint == "https://collector.example.test:8443"
    assert status.error.to_json()["endpoint"] == status.endpoint
    with pytest.warns(TraceExportWarning) as caught:
        status.warn()
    diagnostic = str(caught[0].message) + json.dumps(status.error.to_json())
    for hidden in ("test-user", "test-sensitive-value", "private-path", "private-fragment"):
        assert hidden not in diagnostic


def test_trace_export_error_names_collector_remedy_and_preserves_failure_policy():
    error = TraceExportError("test-run-id", "https://collector.example.test/private-path", 503, "HTTP 503")
    assert error.exit_code == 3
    assert error.get_error_code() == "TRACE_EXPORT_FAILED"
    assert "FI_COLLECTOR_ENDPOINT" in str(error)
    assert "Run items may already be stored" in str(error)
    assert "Spans are not journaled" in str(error)
    assert "private-path" not in str(error)
    assert error.to_json()["endpoint"] == "https://collector.example.test"


def test_cross_origin_redirect_never_receives_run_credentials():
    sent = []

    class RedirectAdapter(requests.adapters.BaseAdapter):
        def send(self, request, **kwargs):
            sent.append(request)
            response = requests.Response()
            response.status_code = 307
            response.headers["Location"] = "https://foreign.example.test/steal"
            response._content = b"test-sensitive-response"
            response.url = request.url
            response.request = request
            return response

        def close(self):
            pass

    status = ExportStatus("test-run-id", "https://collector.example.test/traces", Redactor())
    with ExportSession(status) as session:
        session.mount("https://", RedirectAdapter())
        response = session.post("https://collector.example.test/traces", data=b"test-spans",
                                headers={"X-Api-Key": "test-run-api", "X-Secret-Key": "test-run-secret"},
                                allow_redirects=True)
    assert len(sent) == 1
    assert sent[0].url == "https://collector.example.test/traces"
    assert sent[0].headers["X-Api-Key"] == "test-run-api"
    assert sent[0].headers["X-Secret-Key"] == "test-run-secret"
    assert response.status_code == status.status_code == 307
    assert response.content == b""
    status.failed()
    assert status.error.status_code == 307


def test_flush_and_warning_controls_do_not_erase_terminal_failure():
    calls = []

    class Inner:
        def export(self, spans):
            return SpanExportResult.FAILURE

        def force_flush(self, timeout_millis):
            calls.append(("flush", timeout_millis))
            return True

        def shutdown(self):
            calls.append(("shutdown",))

    status = ExportStatus("test-run-id", "https://api.example.test/tracer/v1/traces", Redactor())
    wrapper = tracing_export.ScrubbingExporter(Inner(), Redactor(), status)
    assert wrapper.export([]) == SpanExportResult.FAILURE
    error = status.error
    assert wrapper.force_flush(1234)
    wrapper.shutdown()
    assert calls == [("flush", 1234), ("shutdown",)]
    session = _session()
    session.export_status = status
    with warnings.catch_warnings():
        warnings.simplefilter("error", TraceExportWarning)
        session.warn_export_failure()
    with pytest.raises(TraceExportError) as caught:
        session.check_export()
    assert caught.value is error
