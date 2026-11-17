import logging
import sys
from types import SimpleNamespace

from fi.telemetry import agent_scope, configure, status


def test_first_load_once_and_status(tracing, make_snapshot, caplog):
    tracer, _, _ = tracing
    snapshot, _ = make_snapshot()
    with caplog.at_level(logging.INFO, logger="futureagi.telemetry"):
        with agent_scope(agent="refund-agent"):
            with tracer.start_as_current_span("request"):
                snapshot.read_all()
                snapshot.read_all()
                facts = status()
    assert len([r for r in caplog.records if "recording skill loads" in r.message]) == 1
    assert facts["provider"] == "configured"
    assert facts["processor_installed"] is True
    assert facts["agent_name_source"] == "agent_scope"
    assert facts["last_load"]["evidence"] == "delivered"
    assert "synthetic-lease" not in caplog.text
    assert "Refund instructions" not in caplog.text


def test_off_silences_lines(tracing, make_snapshot, caplog):
    tracer, _, provider = tracing
    configure(skills_tracing="off", tracer_provider=provider)
    snapshot, _ = make_snapshot()
    with caplog.at_level(logging.DEBUG, logger="futureagi.telemetry"):
        with tracer.start_as_current_span("request"):
            snapshot.read_all()
    assert not caplog.records
    assert status()["mode"] == "off"


def test_truth_table_diagnostics(tracing, monkeypatch):
    import opentelemetry.trace as trace
    _, _, provider = tracing
    assert status()["truth_table_row"] == "Python configured provider"
    configure()
    monkeypatch.setitem(sys.modules, "fi_instrumentation.otel", SimpleNamespace(get_registered_tracer_providers=lambda: [provider]))
    assert status()["truth_table_row"] == "Python traceAI register()"
    monkeypatch.delitem(sys.modules, "fi_instrumentation.otel")
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)
    assert status()["provider"] == "global"
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: trace.ProxyTracerProvider())
    assert status()["provider"] == "none"


def test_doctor_prints_safe_facts(tracing, monkeypatch, capsys):
    from fi.telemetry.__main__ import main
    monkeypatch.setattr(sys, "argv", ["fi.telemetry", "doctor"])
    with agent_scope(agent="secret-never-print"):
        main()
    text = capsys.readouterr().out
    assert "provider: configured" in text
    assert "rule: A load is recorded" in text
    assert "secret-never-print" not in text
