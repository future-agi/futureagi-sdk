import sys
from types import SimpleNamespace

import pytest
from fi.telemetry import configure
from fi.telemetry._otel import install, select_provider


def test_configured_wins_and_install_is_idempotent(tracing, monkeypatch):
    _, _, provider = tracing
    monkeypatch.setitem(sys.modules, "fi_instrumentation.otel", SimpleNamespace(get_registered_tracer_providers=lambda: [object()]))
    assert select_provider() == (provider, "configured")
    processors = provider._active_span_processor._span_processors
    install(provider)
    install(provider)
    assert provider._active_span_processor._span_processors == processors


def test_registry_and_global_selection(tracing, monkeypatch):
    import opentelemetry.trace as trace
    _, _, provider = tracing
    configure()
    monkeypatch.setitem(sys.modules, "fi_instrumentation.otel", SimpleNamespace(get_registered_tracer_providers=lambda: [provider]))
    assert select_provider() == (provider, "traceai")
    monkeypatch.delitem(sys.modules, "fi_instrumentation.otel")
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)
    assert select_provider() == (provider, "global")


def test_undiscoverable_provider_enriches_only(tracing, monkeypatch, make_snapshot):
    import opentelemetry.trace as trace
    tracer, exporter, _ = tracing
    configure()
    monkeypatch.delitem(sys.modules, "fi_instrumentation.otel", raising=False)
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: trace.ProxyTracerProvider())
    snapshot, _ = make_snapshot()
    with tracer.start_as_current_span("request") as span:
        snapshot.read_all()
        assert span.attributes["fi.skills.count"] == 1
    assert not [s for s in exporter.get_finished_spans() if s.name == "skill.load"]


def test_real_traceai_registry_preserves_existing_exporter(make_snapshot):
    # Integration gate V1: install ST1's wheel in the cloud before this test.
    pytest.importorskip("fi_instrumentation.otel")
    from fi_instrumentation.otel import get_registered_tracer_providers, register
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
    exporter = InMemorySpanExporter()
    provider = register(project_name="synthetic-runtime-test", set_global_tracer_provider=False,
                        span_exporter=exporter, batch=False, verbose=False)
    try:
        configure()
        assert provider in get_registered_tracer_providers()
        snapshot, _ = make_snapshot()
        with provider.get_tracer("test").start_as_current_span("request"):
            snapshot.read_all()
        assert {s.name for s in exporter.get_finished_spans()} >= {"request", "skill.load"}
    finally:
        configure()
        provider.shutdown()


def test_last_traceai_global_shutdown_is_no_otel(monkeypatch, make_snapshot):
    from fi.telemetry._otel import wire_mode
    from opentelemetry import trace
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    backend = pytest.importorskip("fi_instrumentation.otel")
    monkeypatch.setattr(trace, "_TRACER_PROVIDER", None)
    monkeypatch.setattr(trace, "_TRACER_PROVIDER_SET_ONCE", type(trace._TRACER_PROVIDER_SET_ONCE)())
    exporter = InMemorySpanExporter()
    provider = backend.register(project_name="last-live", set_global_tracer_provider=True,
                                span_exporter=exporter, batch=False, verbose=False)
    try:
        configure(skills_tracing="on")
        snapshot, _ = make_snapshot()
        with provider.get_tracer(__name__).start_as_current_span("live"):
            snapshot.read_file("SKILL.md")
        assert [s.name for s in exporter.get_finished_spans()] == ["skill.load", "live"]
    finally:
        provider.shutdown()
        configure()
    assert trace.get_tracer_provider() is provider
    assert select_provider() == (None, "none")
    assert wire_mode() == "no_otel"
