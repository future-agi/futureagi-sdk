"""Outcome bookkeeping, redacted diagnostics, and CLI propagation for OTLP failures."""

import json
import warnings

import pytest
import requests
from opentelemetry.sdk.trace.export import SpanExportResult

from fi.experiments._redact import Redactor
from fi.experiments._tracing.export import ScrubbingExporter
from fi.experiments._tracing.export_status import ExportSession, ExportStatus
from fi.experiments.errors import TraceExportError, TraceExportWarning
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer, client_for
from tests.experiments.unit.test_otlp_failures import PATH, SECRET, bounded_export, collector, run_on


@pytest.mark.parametrize("later_status", [200, 404])
def test_real_batches_keep_first_failure_and_warn_once(monkeypatch, later_status):
    monkeypatch.setenv("OTEL_BSP_MAX_EXPORT_BATCH_SIZE", "1")
    with collector(lambda n: 404 if n == 1 else later_status) as (base, sent):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with pytest.raises(TraceExportError) as error:
                run_on(base, ContractServer())
    assert error.value.status_code == 404 and len(sent) == 2
    assert len([w for w in caught if isinstance(w.message, TraceExportWarning)]) == 1


def test_real_503_retry_then_success_does_not_fail_run(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_TIMEOUT", "5")
    with collector(lambda n: 503 if n == 1 else 200) as (base, sent):
        with warnings.catch_warnings(record=True) as caught:
            result = run_on(base, ContractServer())
    assert result.status == "completed" and len(sent) == 2
    assert not [w for w in caught if isinstance(w.message, TraceExportWarning)]


def outcome():
    return ExportStatus("run-1", "http://127.0.0.1:1" + PATH, Redactor([]))


def test_dropped_batch_stays_failed_after_later_success_and_warns_once():
    state = outcome()

    class Inner:
        calls = 0

        def export(self, spans):
            self.calls += 1
            state.status_code = 404 if self.calls == 1 else 200
            return SpanExportResult.FAILURE if self.calls == 1 else SpanExportResult.SUCCESS

    exporter = ScrubbingExporter(Inner(), Redactor([]), state)
    assert exporter.export([]) == SpanExportResult.FAILURE
    assert exporter.export([]) == SpanExportResult.SUCCESS
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        state.warn()
        state.warn()
    assert len(caught) == 1 and isinstance(caught[0].message, TraceExportWarning)
    assert state.error.status_code == 404
    assert outcome().error is None, "export failure state belongs to one run only"


def test_successful_retry_is_not_a_dropped_batch():
    state = outcome()

    class Inner:
        def export(self, spans):
            state.status_code = 503  # failed attempt, then a successful retry within this batch
            state.status_code = 200
            return SpanExportResult.SUCCESS

    assert ScrubbingExporter(Inner(), Redactor([]), state).export([]) == SpanExportResult.SUCCESS
    assert state.error is None


def test_exporter_exception_is_typed_without_leaking_exception_text(caplog):
    state = outcome()

    class Inner:
        def export(self, spans):
            raise RuntimeError("server echoed " + SECRET)

    assert ScrubbingExporter(Inner(), Redactor([]), state).export([]) == SpanExportResult.FAILURE
    assert isinstance(state.error, TraceExportError)
    assert SECRET not in str(state.error) + caplog.text
    assert state.error.status_code is None and state.error.reason == "exporter failed"


def test_diagnostic_endpoint_omits_url_credentials_query_and_fragment():
    state = ExportStatus("r", "https://user:password@host.test/tracer/v1/traces?token=hidden#secret", Redactor([]))
    state.failed()
    assert state.error.endpoint == "https://host.test/tracer/v1/traces"
    assert all(s not in json.dumps(state.error.to_json()) for s in ("password", "hidden", "secret"))


def test_http_session_drops_server_controlled_reason_and_body(monkeypatch):
    response = requests.Response()
    response.status_code = 503
    response.reason = SECRET
    response._content = SECRET.encode()
    monkeypatch.setattr(requests.Session, "send", lambda *args, **kwargs: response)
    state = outcome()
    with ExportSession(state) as session:
        got = session.send(requests.Request("POST", state.endpoint).prepare())
    assert got.text == "" and SECRET not in got.reason
    assert state.status_code == 503


@pytest.mark.parametrize("exception", [requests.ConnectionError, requests.Timeout])
def test_http_session_drops_transport_exception_text(monkeypatch, exception):
    def fail(*args, **kwargs):
        raise exception(SECRET)

    monkeypatch.setattr(requests.Session, "send", fail)
    state = outcome()
    with ExportSession(state) as session, pytest.raises(requests.RequestException) as error:
        session.send(requests.Request("POST", state.endpoint).prepare())
    assert SECRET not in str(error.value)
    assert state.status_code is None and "connection" in state.reason


def test_cli_json_is_setup_error_not_success_after_collector_404(tmp_path, monkeypatch):
    from fi.experiments._engine import Engine

    source = tmp_path / "run.py"
    source.write_text(
        "from fi import experiments\n"
        "experiments.run(experiments.dataset([{'q': 'x'}], name='otlp-cli'), "
        "lambda row: 'ok', instrument=False)\n"
    )
    with collector(404) as (base, sent):
        monkeypatch.setattr(Engine, "_client", lambda self: client_for(ContractServer(), base_url=base))
        with pytest.warns(TraceExportWarning, match="HTTP 404"):
            code, out, err = cli("run", str(source), "--json", "--no-env-file")
    payload = json.loads(out)
    assert code == 3 and payload["error"]["code"] == "TRACE_EXPORT_FAILED"
    assert base + PATH in payload["error"]["message"]
    assert "runs" not in payload and SECRET not in out + err
    assert sent
