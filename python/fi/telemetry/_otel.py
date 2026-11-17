"""Optional OTel bridge. Importing this module never imports OpenTelemetry."""
from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from types import MappingProxyType

CARRIER_KEY = "futureagi.runtime.span_attributes.v1"
_scope = ContextVar("futureagi.skills.scope", default=None)
_suppressed = ContextVar("futureagi.skills.suppressed", default=False)
_configured_mode = None
_configured_provider = None
_debug_logged = False


def debug_failure():
    global _debug_logged
    if not _debug_logged:
        _debug_logged = True
        # Exception messages may contain credentials or file content.
        try:
            logging.getLogger("futureagi.telemetry").debug("futureagi: telemetry bridge unavailable")
        except Exception:
            pass


def mode():
    value = _configured_mode or os.environ.get("FI_SKILLS_TRACING", "on")
    return value if value in ("on", "load_only", "off") else "on"


def configure(*, skills_tracing=None, tracer_provider=None):
    global _configured_mode, _configured_provider
    if skills_tracing is not None and skills_tracing not in ("on", "load_only", "off"):
        raise ValueError("skills_tracing must be on, load_only or off")
    _configured_mode = skills_tracing
    _configured_provider = tracer_provider
    if mode() == "on" and sys.modules.get("opentelemetry.trace") is not None:
        try:
            provider, _ = select_provider()
            install(provider)
        except Exception:
            debug_failure()


def select_provider():
    trace = sys.modules.get("opentelemetry.trace")
    if trace is None:
        return None, "none"
    if _configured_provider is not None:
        return _configured_provider, "configured"
    otel = sys.modules.get("fi_instrumentation.otel")
    if otel is not None:
        get_providers = getattr(otel, "get_registered_tracer_providers", None)
        providers = tuple(get_providers()) if get_providers else ()
        if providers:
            return providers[-1], "traceai"
    provider = trace.get_tracer_provider()
    if type(provider).__name__ in ("ProxyTracerProvider", "NoOpTracerProvider"):
        return None, "none"
    return provider, "global"


def install(provider):
    if provider is None or mode() != "on":
        return
    from .processor import FutureAGISkillsSpanProcessor, INSTALL_LOCK
    with INSTALL_LOCK:
        if getattr(provider, "_futureagi_skills_processor", False):
            return
        add = getattr(provider, "add_span_processor", None)
        if add is not None:
            add(FutureAGISkillsSpanProcessor())
            provider._futureagi_skills_processor = True


def allowlisted(attrs):
    result = {}
    for key, value in attrs.items():
        if not isinstance(key, str) or not key.startswith(("fi.skills.", "fi.context.", "gen_ai.agent.")):
            continue
        if isinstance(value, str):
            value = value.encode("utf-8")[:256].decode("utf-8", errors="ignore")
        elif isinstance(value, (tuple, list)):
            if not all(isinstance(item, str) for item in value):
                continue
            value = tuple(item.encode("utf-8")[:256].decode("utf-8", errors="ignore") for item in value[:32])
        elif type(value) not in (bool, int, float):
            continue
        result[key] = value
        if len(result) == 64:
            break
    return result


def carrier(attrs, reset=False):
    return MappingProxyType({"v": 1, "attrs": MappingProxyType(allowlisted(attrs)), "reset_skills": reset})


def publish(state, reset=False):
    context = sys.modules.get("opentelemetry.context")
    if context is not None and mode() == "on":
        return context.attach(context.set_value(CARRIER_KEY, carrier(state.attrs, reset)))
    return None


def current():
    trace = sys.modules.get("opentelemetry.trace")
    return trace.get_current_span() if trace is not None else None


def wire_mode(tracing=True):
    if not tracing or mode() == "off":
        return "off"
    try:
        return mode() if select_provider()[0] is not None else "no_otel"
    except Exception:
        debug_failure()
        return "no_otel"
