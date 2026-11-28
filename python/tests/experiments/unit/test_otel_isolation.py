"""The tracing fixture restores complete state, including after a failed test."""

import builtins
import sys
from types import SimpleNamespace

import pytest

from tests.experiments.unit.otel_isolation import isolated_otel


@pytest.mark.parametrize("fails", [False, True])
def test_provider_and_instrumentor_lifetimes_are_restored_together(monkeypatch, fails):
    from opentelemetry import trace

    from fi.experiments._tracing import instrument, routing

    class Instrumentor:
        is_instrumented_by_opentelemetry = False

        def uninstrument(self):
            self.is_instrumented_by_opentelemetry = False

    instance = Instrumentor()
    module = SimpleNamespace(Instrumentor=SimpleNamespace(_instance=instance))
    monkeypatch.setitem(sys.modules, "test_isolated_instrumentor", module)
    monkeypatch.setattr(instrument, "INSTRUMENTORS", {
        "test": ("test_isolated_instrumentor", "Instrumentor", "test"),
    })
    old_provider = trace._TRACER_PROVIDER
    old_once = trace._TRACER_PROVIDER_SET_ONCE
    old_proxy = trace._PROXY_TRACER_PROVIDER
    old_done = instrument._done
    old_delegate = routing.current_delegate()
    try:
        with isolated_otel():
            provider = trace.NoOpTracerProvider()
            trace.set_tracer_provider(provider)
            routing.bind_delegate(provider)
            instrument._done["test"] = provider
            instrument._failed["broken"] = "failure"
            instrument._probed_ok.add(("test", "Instrumentor"))
            instance.is_instrumented_by_opentelemetry = True
            if fails:
                raise RuntimeError("failed test body")
    except RuntimeError as exc:
        assert fails and str(exc) == "failed test body"
    assert trace._TRACER_PROVIDER is old_provider
    assert trace._TRACER_PROVIDER_SET_ONCE is old_once
    assert trace._PROXY_TRACER_PROVIDER is old_proxy
    assert routing.current_delegate() is old_delegate
    assert instrument._done is old_done and instrument._done == {}
    assert instrument._failed == {} and instrument._probed_ok == set()
    assert not instance.is_instrumented_by_opentelemetry


def test_nontracing_installations_need_no_otel(monkeypatch):
    original = builtins.__import__

    def importing(name, *args, **kwargs):
        if name.startswith("opentelemetry"):
            raise ModuleNotFoundError(name)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importing)
    with isolated_otel():
        pass
