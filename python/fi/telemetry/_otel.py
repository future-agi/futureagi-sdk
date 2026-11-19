"""Optional OTel bridge. Importing this module never imports OpenTelemetry."""
from __future__ import annotations

import logging
import os
import sys
from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._registry import State

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
    otel = sys.modules.get("fi_instrumentation.otel")
    # Optional lifecycle contract: OTel retains the first global even after
    # shutdown. Older backends and unrelated host providers keep their fallback.
    closed = getattr(otel, "is_tracer_provider_shutdown", None)
    if _configured_provider is not None and not (closed and closed(_configured_provider)):
        return _configured_provider, "configured"
    if otel is not None:
        get_providers = getattr(otel, "get_registered_tracer_providers", None)
        providers = tuple(get_providers()) if get_providers else ()
        if providers:
            return providers[-1], "traceai"
    provider = trace.get_tracer_provider()
    if type(provider).__name__ in ("ProxyTracerProvider", "NoOpTracerProvider") or (closed and closed(provider)):
        return None, "none"
    return provider, "global"


def install(provider):
    if provider is None or mode() != "on":
        return
    from .processor import INSTALL_LOCK, FutureAGISkillsSpanProcessor
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
            # Every Unicode code point occupies at most four UTF-8 bytes. Most
            # identifiers fit without encoding, slicing, and decoding again.
            if len(value) > 64:
                value = value.encode("utf-8")[:256].decode("utf-8", errors="ignore")
        elif isinstance(value, (tuple, list)):
            if isinstance(value, tuple) and len(value) <= 32 and all(
                isinstance(item, str) and len(item) <= 64 for item in value
            ):
                pass  # Already immutable and bounded; no attribute copy needed.
            else:
                if not all(isinstance(item, str) for item in value):
                    continue
                value = tuple(item if len(item) <= 64 else item.encode("utf-8")[:256].decode("utf-8", errors="ignore") for item in value[:32])
        elif type(value) not in (bool, int, float):
            continue
        result[key] = value
        if len(result) == 64:
            break
    return result


_EMPTY_ATTRS = MappingProxyType({})


@dataclass(frozen=True, init=False)
class _Carrier(Mapping):
    """Read-only v1 mapping. Each attrs value is an immutable snapshot.

    A plain carrier stays fixed. An explicit scope's carrier follows the last
    published on-mode snapshot even after an inner OTel span detaches.
    """

    _attrs: Mapping
    _scope_state: State | None
    reset_skills: bool

    def __init__(self, attrs, reset=False, *, scope_state=None):
        object.__setattr__(self, "_attrs", MappingProxyType(allowlisted(attrs)))
        object.__setattr__(self, "_scope_state", scope_state)
        object.__setattr__(self, "reset_skills", reset)

    @property
    def attrs(self):
        if self._scope_state is None:
            return self._attrs
        return self._scope_state.published_attrs if mode() == "on" else _EMPTY_ATTRS

    def __getitem__(self, key):
        if key == "v":
            return 1
        if key == "attrs":
            return self.attrs
        if key == "reset_skills":
            return self.reset_skills
        raise KeyError(key)

    def __iter__(self):
        return iter(("v", "attrs", "reset_skills"))

    def __len__(self):
        return 3


def carrier(attrs, reset=False):
    return _Carrier(attrs, reset)


def publish(state):
    state.published_attrs = MappingProxyType(allowlisted(state.attrs))


def bind_scope(state, *, reset, parent=None):
    context = sys.modules.get("opentelemetry.context")
    if context is None:
        return None
    publish(state)
    return context.attach(context.set_value(CARRIER_KEY, _Carrier({}, reset, scope_state=state), parent))


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
