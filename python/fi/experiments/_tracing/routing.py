"""``RoutingTracerProvider``: the process-global provider that routes each span to the current
run's delegate.

A provider's Resource is fixed when the provider is made (it names the run's project), OTel allows
the global provider to be set once, and instrumentors bind to a provider once. So the first run in
a process installs this router as the global provider and instruments against it; each run gets
its own delegate (a plain ``TracerProvider`` with the run's resource, ``export.py``; traceAI's
``register()`` is not used); the router looks the delegate up from a context variable on every
``start_span``. Concurrent runs in one process (a sweep, a notebook re-run) therefore stay
separate.
"""

from __future__ import annotations

import contextvars
import threading
import weakref
from contextlib import contextmanager
from typing import Any, Iterator, Optional

from opentelemetry import trace as trace_api

from fi.experiments.errors import TracingConflictError

_current_delegate: contextvars.ContextVar[Optional[trace_api.TracerProvider]] = contextvars.ContextVar(
    "fi_experiments_delegate", default=None
)


def bind_delegate(provider: Optional[trace_api.TracerProvider]) -> contextvars.Token:
    return _current_delegate.set(provider)


def unbind_delegate(token: contextvars.Token) -> None:
    _current_delegate.reset(token)


def current_delegate() -> Optional[trace_api.TracerProvider]:
    return _current_delegate.get()


class _RoutingTracer(trace_api.Tracer):
    """Instrumentors call ``get_tracer()`` once per process, so one of these lives as long as the
    process. The per-provider tracer cache is keyed by the provider object itself (weakly), never
    by ``id()``: a run's delegate is freed when the run ends, CPython reuses its address, and an
    ``id()`` key would hand a later run the dead run's tracer and span processors."""

    def __init__(self, router: "RoutingTracerProvider", args: tuple, kwargs: dict) -> None:
        self._router = router
        self._args = args
        self._kwargs = kwargs
        self._cache: "weakref.WeakKeyDictionary[Any, trace_api.Tracer]" = weakref.WeakKeyDictionary()
        self._lock = threading.Lock()

    def _target(self) -> trace_api.Tracer:
        provider = _current_delegate.get() or self._router.fallback
        try:
            tracer = self._cache.get(provider)
        except TypeError:  # a provider that cannot be weakly referenced: no cache
            return provider.get_tracer(*self._args, **self._kwargs)
        if tracer is None:
            tracer = provider.get_tracer(*self._args, **self._kwargs)
            with self._lock:
                self._cache[provider] = tracer
        return tracer

    def start_span(self, *args: Any, **kwargs: Any) -> trace_api.Span:
        return self._target().start_span(*args, **kwargs)

    @contextmanager
    def start_as_current_span(self, *args: Any, **kwargs: Any) -> Iterator[trace_api.Span]:
        with self._target().start_as_current_span(*args, **kwargs) as span:
            yield span


class RoutingTracerProvider(trace_api.TracerProvider):
    """Spans started inside a trial go to that run's delegate; others go to ``fallback``
    (nowhere by default)."""

    def __init__(self, fallback: Optional[trace_api.TracerProvider] = None) -> None:
        self.fallback = fallback or trace_api.NoOpTracerProvider()

    def get_tracer(self, *args: Any, **kwargs: Any) -> trace_api.Tracer:
        return _RoutingTracer(self, args, kwargs)


def _global_is_unset(provider: trace_api.TracerProvider) -> bool:
    return isinstance(provider, trace_api.ProxyTracerProvider)


def is_observe_provider(provider: Any) -> bool:
    resource = getattr(provider, "resource", None)
    attrs = getattr(resource, "attributes", {}) or {}
    return str(attrs.get("project_type", "")).lower() == "observe"


def install_router() -> RoutingTracerProvider:
    """Install (once) and return the routing provider as the global provider.

    Refuses a foreign global provider (most often the app's own ``register(project_type=OBSERVE)``
    at import time), because experiment spans would land in that project.
    """
    current = trace_api.get_tracer_provider()
    if isinstance(current, RoutingTracerProvider):
        return current
    if not _global_is_unset(current):
        kind = "an OBSERVE project provider" if is_observe_provider(current) else type(current).__name__
        raise TracingConflictError(
            f"A global tracer provider is already set ({kind}). Experiment spans would land in it. "
            "Pass it explicitly with trace=<provider> (the run then records its identity on span "
            "attributes), skip the app's register() under experiments, or run with trace=False."
        )
    router = RoutingTracerProvider()
    trace_api.set_tracer_provider(router)
    if trace_api.get_tracer_provider() is not router:  # pragma: no cover - lost a race
        raise TracingConflictError("another global tracer provider was installed concurrently")
    return router
