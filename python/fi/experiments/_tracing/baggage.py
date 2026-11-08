"""``BaggageAttributesProcessor``: copies the run identity from W3C baggage onto every span.

Same behaviour as OTel contrib's ``BaggageSpanProcessor``, limited to ``fi.experiment.*`` and
``fi.dataset.*`` keys, with no traceAI dependency. Worker threads get the context through
``contextvars.copy_context()``.
"""

from __future__ import annotations

from typing import Optional

from opentelemetry import baggage
from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor

PREFIXES = ("fi.experiment.", "fi.dataset.")
SCHEMA_VERSION = "1"  # the attribute contract's version (fi.experiment.schema_version)


class BaggageAttributesProcessor(SpanProcessor):
    def __init__(self, prefixes: tuple[str, ...] = PREFIXES) -> None:
        self._prefixes = prefixes

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        for key, value in baggage.get_all(parent_context).items():
            if key.startswith(self._prefixes) and value is not None:
                span.set_attribute(key, str(value))

    def on_end(self, span: ReadableSpan) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
