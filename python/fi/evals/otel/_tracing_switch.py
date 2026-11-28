"""The provider ``setup_tracing`` installs as the OpenTelemetry global provider: it sends each span to the one active
configuration's provider, and to none between configurations."""
from __future__ import annotations

import threading
import weakref
from typing import Any, Optional

from fi.errors import ConfigurationError

_switch: Optional[Any] = None
_made = threading.Lock()


class TracingAlreadyConfigured(ConfigurationError):
    """``setup_tracing`` refused: a configuration is active (call ``shutdown_tracing()`` first), or the OpenTelemetry
    global tracer provider is another one, which would receive the spans instead of the configuration asked for."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="tracing_already_configured", operation="setup_tracing")


def current_switch() -> Optional[Any]:
    """The switching provider, or None when tracing was not configured in this process."""
    return _switch


def switching_provider() -> Any:
    """The switching provider, made on first use (it needs the OpenTelemetry API)."""
    global _switch
    with _made:
        if _switch is None:
            _switch = _switching_class()()
    return _switch


def _switching_class() -> Any:
    from opentelemetry import trace as trace_api

    class _SwitchingTracer(trace_api.Tracer):
        """A tracer that looks up the active configuration on each span, so a tracer cached during one configuration
        (instrumentors keep theirs) sends later spans to the configuration active then, and spans between
        configurations to none."""

        def __init__(self, owner: Any, args: tuple, kwargs: dict) -> None:
            self._owner = owner
            self._args = args
            self._kwargs = kwargs
            # Keyed by the provider object (weakly), not id(): a freed provider's address can be reused.
            self._cache: "weakref.WeakKeyDictionary[Any, Any]" = weakref.WeakKeyDictionary()
            self._lock = threading.Lock()

        def _target(self) -> Any:
            provider = self._owner.delegate
            with self._lock:
                tracer = self._cache.get(provider)
                if tracer is None:
                    tracer = provider.get_tracer(*self._args, **self._kwargs)
                    self._cache[provider] = tracer
            return tracer

        def start_span(self, *args: Any, **kwargs: Any) -> Any:
            return self._target().start_span(*args, **kwargs)

        def start_as_current_span(self, *args: Any, **kwargs: Any) -> Any:
            return self._target().start_as_current_span(*args, **kwargs)

    class _SwitchingTracerProvider(trace_api.TracerProvider):
        """Installed once as the OpenTelemetry global provider; sends each span to the active configuration's
        provider, or to a no-op provider when none is active."""

        def __init__(self) -> None:
            self._idle = trace_api.NoOpTracerProvider()
            self.delegate: Any = self._idle

        def activate(self, provider: Any) -> None:
            self.delegate = provider

        def deactivate(self) -> None:
            self.delegate = self._idle

        def get_tracer(self, *args: Any, **kwargs: Any) -> Any:
            return _SwitchingTracer(self, args, kwargs)

        @property
        def resource(self) -> Any:
            """The active configuration's resource; none (``AttributeError``) between configurations."""
            return self.delegate.resource

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            flush = getattr(self.delegate, "force_flush", None)
            return bool(flush(timeout_millis)) if flush is not None else True

    return _SwitchingTracerProvider


def install_switching_provider() -> Any:
    """Make the switching provider the OpenTelemetry global provider, or refuse when another one is."""
    from opentelemetry import trace as trace_api

    switch = switching_provider()
    current = trace_api.get_tracer_provider()
    if current is switch:
        return switch
    if not isinstance(current, trace_api.ProxyTracerProvider):
        raise TracingAlreadyConfigured(
            f"The OpenTelemetry global tracer provider is already set ({type(current).__name__}); spans would go to it "
            "and not to the exporters configured here. Configure tracing with setup_tracing before any other "
            "provider is set, or add these exporters to that provider."
        )
    trace_api.set_tracer_provider(switch)
    if trace_api.get_tracer_provider() is not switch:  # pragma: no cover - another thread set one first
        raise TracingAlreadyConfigured("Another OpenTelemetry global tracer provider was set at the same time.")
    return switch
