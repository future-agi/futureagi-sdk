"""Isolate OTel's provider and the instrumentors bound to it as one lifetime."""

import sys
from contextlib import contextmanager


def _active_instrumentors(specs):
    # Do not load optional libraries just to clean up. Their BaseInstrumentor
    # singleton records whether it actually patched the client library.
    active = set()
    for module_name, class_name, _ in specs:
        module = sys.modules.get(module_name)
        cls = getattr(module, class_name, None)
        instance = getattr(cls, "_instance", None)
        if instance is not None and instance.is_instrumented_by_opentelemetry:
            active.add(instance)
    return active


@contextmanager
def isolated_otel():
    try:
        from opentelemetry import trace
        from opentelemetry.util._once import Once
    except ImportError:
        # Non-tracing tests also run in installations without the tracing extra.
        yield
        return

    from fi.experiments._tracing import instrument, routing

    attributes = ("_TRACER_PROVIDER", "_TRACER_PROVIDER_SET_ONCE", "_PROXY_TRACER_PROVIDER")
    original = {name: getattr(trace, name) for name in attributes}
    caches = {name: getattr(instrument, name) for name in ("_done", "_failed", "_probed_ok")}
    saved = {name: value.copy() for name, value in caches.items()}
    specs = tuple(instrument.INSTRUMENTORS.values())
    active_before = _active_instrumentors(specs)
    token = routing.bind_delegate(None)
    try:
        trace._TRACER_PROVIDER = None
        trace._TRACER_PROVIDER_SET_ONCE = Once()
        trace._PROXY_TRACER_PROVIDER = trace.ProxyTracerProvider()
        for value in caches.values():
            value.clear()
        yield
    finally:
        try:
            for instance in _active_instrumentors(specs) - active_before:
                instance.uninstrument()
        finally:
            # Keep the original containers: a test's monkeypatch may restore a
            # reference to one after this fixture finishes.
            for name, value in caches.items():
                value.clear()
                value.update(saved[name])
                setattr(instrument, name, value)
            for name, value in original.items():
                setattr(trace, name, value)
            routing.unbind_delegate(token)
