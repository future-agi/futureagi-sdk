"""Export diagnostics must not replace the engine's error or doctor transport contracts."""

import asyncio
import io
import json
from types import SimpleNamespace
import warnings

import pytest
import requests

from fi._cli import doctor
from fi.experiments._cli import routes
from fi.experiments._engine import Engine
from fi.experiments._redact import Redactor
from fi.experiments._tracing.export_status import ExportSession, ExportStatus
from fi.experiments.errors import RunInterrupted, TraceExportError, TraceExportWarning, UsageError
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer, client_for
from tests.experiments.unit.test_otlp_failures import (
    PATH, SECRET, bounded_export, collector, route_client, run_on,
)


@pytest.mark.parametrize("warning_filter", ["default", "error"])
def test_warning_policy_preserves_typed_export_error(warning_filter, caplog):
    with collector(404) as (base, sent), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter(warning_filter)
        with pytest.raises(TraceExportError) as error:
            run_on(base, ContractServer())
    assert sent and error.value.status_code == 404
    assert error.value.endpoint == base + PATH
    assert SECRET not in str(error.value) + caplog.text
    if warning_filter == "default":
        assert len([w for w in caught if isinstance(w.message, TraceExportWarning)]) == 1


@pytest.mark.parametrize("warning_filter", ["default", "error"])
@pytest.mark.parametrize("primary", ["interrupted", "usage"])
def test_warning_policy_preserves_primary_error(monkeypatch, warning_filter, primary):
    original = UsageError("primary failure")

    async def interrupted(self, todo, runner, evaluators, budget, journal, tracing, run_id, shared, total):
        with tracing.trial(todo[0][0].id, todo[0][1]):
            pass
        if primary == "interrupted":
            raise asyncio.CancelledError()
        raise original

    monkeypatch.setattr(Engine, "_run_all", interrupted)
    with collector(404) as (base, sent), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter(warning_filter)
        with pytest.raises(RunInterrupted if primary == "interrupted" else UsageError) as error:
            run_on(base, ContractServer())
    assert sent
    if primary == "usage":
        assert error.value is original
    else:
        assert error.value.exit_code == 4
    if warning_filter == "default":
        assert len([w for w in caught if isinstance(w.message, TraceExportWarning)]) == 1


@pytest.mark.parametrize("warning_filter", ["default", "error"])
def test_warning_policy_preserves_cli_json(tmp_path, monkeypatch, warning_filter):
    source = tmp_path / "run.py"
    source.write_text(
        "from fi import experiments\n"
        "experiments.run(experiments.dataset([{'q': 'x'}], name='warning-contract'), "
        "lambda row: 'ok', instrument=False)\n"
    )
    with collector(404) as (base, sent), warnings.catch_warnings(record=True):
        monkeypatch.setattr(Engine, "_client", lambda self: client_for(ContractServer(), base_url=base))
        warnings.simplefilter(warning_filter)
        code, out, err = cli("run", str(source), "--json", "--no-env-file")
    payload = json.loads(out)
    assert code == 3 and payload["error"]["code"] == "TRACE_EXPORT_FAILED"
    assert base + PATH in payload["error"]["message"]
    assert "HTTP 404" in payload["error"]["message"]
    assert "runs" not in payload and SECRET not in out + err
    assert sent


def test_promoted_warning_is_attempted_only_once(monkeypatch):
    state = ExportStatus("run-1", "http://127.0.0.1:9" + PATH, Redactor([]))
    state.status_code = 404
    state.failed()
    warn = warnings.warn
    calls = []

    def counted(*args, **kwargs):
        calls.append(args)
        return warn(*args, **kwargs)

    monkeypatch.setattr(warnings, "warn", counted)
    with warnings.catch_warnings():
        warnings.simplefilter("error", TraceExportWarning)
        state.warn()
        state.warn()
    assert len(calls) == 1
    assert isinstance(state.error, TraceExportError) and state.error.status_code == 404


@pytest.mark.parametrize("json_mode", [False, True])
def test_doctor_refused_collector_is_inconclusive_not_setup_failure(monkeypatch, json_mode):
    from fi._cli import auth, ownership

    monkeypatch.setattr(auth, "who_info", lambda args: {"line": "local fixture"})
    monkeypatch.setattr(ownership, "section", lambda args: [])
    out = io.StringIO()
    with collector("refused") as (base, sent):
        client, transport = route_client(base)
        monkeypatch.setattr(doctor, "_SECTIONS", [("Experiments", lambda args: routes.route_lines(client))])
        try:
            code = doctor.run_doctor(SimpleNamespace(stdout=out, json=json_mode, offline=False))
        finally:
            transport.close()
    assert code == 0, "a transport failure cannot establish that the collector route is missing"
    text = out.getvalue()
    assert PATH in text and "could not check" in text and "MISSING" not in text
    if json_mode:
        assert "problems" not in json.loads(text)["sections"]["Experiments"]
    assert sent == []


def test_export_error_names_opt_out_without_promising_resume_recovery():
    error = TraceExportError("run-1", "http://127.0.0.1:9" + PATH, 404, "HTTP 404")
    assert "trace=False" in str(error) and "--no-trace" in str(error)
    assert "resume does not re-export" in str(error)
    assert "already be stored" in str(error)


@pytest.mark.parametrize("exception", [
    requests.exceptions.InvalidURL,
    requests.exceptions.MissingSchema,
    requests.exceptions.ChunkedEncodingError,
    requests.RequestException,
])
def test_nonconnection_request_errors_stay_nonretryable_and_redacted(monkeypatch, exception, caplog):
    attempts = []

    def fail(*args, **kwargs):
        attempts.append(1)
        raise exception(SECRET)

    monkeypatch.setattr(requests.Session, "send", fail)
    state = ExportStatus("run-1", "http://127.0.0.1:9" + PATH, Redactor([]))
    with ExportSession(state) as session, pytest.raises(requests.RequestException) as raised:
        session.send(requests.Request("POST", state.endpoint).prepare())
    assert not isinstance(raised.value, (requests.ConnectionError, requests.Timeout))
    assert state.reason == "request failed" and state.status_code is None
    assert SECRET not in str(raised.value)

    attempts.clear()
    with pytest.warns(TraceExportWarning), pytest.raises(TraceExportError) as error:
        run_on("http://127.0.0.1:9", ContractServer())
    assert len(attempts) == 1, "invalid requests must not acquire connection-error retries"
    assert error.value.reason == "request failed" and error.value.status_code is None
    assert SECRET not in str(error.value) + caplog.text
