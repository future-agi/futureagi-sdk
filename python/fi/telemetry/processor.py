"""On-start attribution only: no I/O, resource changes, or span retention."""
from __future__ import annotations

import sys
from collections.abc import Mapping
from threading import RLock

from . import _otel
from ._registry import registry

INSTALL_LOCK = RLock()


class FutureAGISkillsSpanProcessor:
    def on_start(self, span, parent_context=None):
        if _otel.mode() != "on":
            return
        try:
            context = sys.modules.get("opentelemetry.context")
            value = context.get_value(_otel.CARRIER_KEY, parent_context) if context else None
            if value is not None:
                if not isinstance(value, Mapping) or value.get("v") != 1 or not isinstance(value.get("attrs"), Mapping):
                    return
                attrs = _otel.allowlisted(value["attrs"])
            else:
                state = registry.get(span.get_span_context().trace_id)
                attrs = dict(state.attrs) if state else {}
            existing = getattr(span, "attributes", None) or {}
            for key, value in attrs.items():
                if key not in existing:
                    span.set_attribute(key, value)
        except Exception:
            # Processor failures must not break application span creation.
            # No logging/I/O in this hot path.
            return

    def on_end(self, span):
        pass

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=30000):
        return True
