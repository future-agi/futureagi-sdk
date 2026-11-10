"""BaseSpanProcessor enabled operations."""
from __future__ import annotations

from fi.evals.otel.processors.base import (Any, Context, Optional, ReadableSpan, abstractmethod)


class _BaseSpanProcessorEnabledMethods:
    __slots__ = ()

    @property
    def enabled(self) -> bool:
        """Check if processor is enabled."""
        return self._enabled and not self._shutdown


    def enable(self) -> None:
        """Enable the processor."""
        self._enabled = True


    def disable(self) -> None:
        """Disable the processor."""
        self._enabled = False


    def on_start(
        self,
        span: Any,
        parent_context: Optional[Context] = None,
    ) -> None:
        """
        Called when a span is started.

        Override this to add attributes at span start time.

        Args:
            span: The span that was started
            parent_context: The parent context (if any)
        """
        from fi.evals.otel.processors.base import (Any, Context, Optional)
        pass


    def _on_ending(self, span: Any) -> None:
        """
        Called while a span is ending, before ``on_end``.

        OpenTelemetry SDK 1.40 and later call this hook on every registered
        span processor; older SDKs never call it. It does nothing by default.

        Args:
            span: The span that is ending
        """


    @abstractmethod
    def on_end(self, span: ReadableSpan) -> None:
        """
        Called when a span is ended.

        This is the main processing hook. Override to add
        evaluation scores, cost data, or other enrichment.

        Args:
            span: The completed span (read-only)
        """
        from fi.evals.otel.processors.base import (ReadableSpan, abstractmethod)
        pass


    def shutdown(self) -> None:
        """
        Shutdown the processor.

        Called when the tracer provider is shutting down.
        Override to cleanup resources.
        """
        self._shutdown = True


    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """
        Force flush any buffered data.

        Args:
            timeout_millis: Maximum time to wait

        Returns:
            True if flush succeeded
        """
        return True


    def should_process(self, span: ReadableSpan) -> bool:
        """
        Determine if this span should be processed.

        Override to implement custom filtering logic.

        Args:
            span: The span to check

        Returns:
            True if span should be processed
        """
        from fi.evals.otel.processors.base import (ReadableSpan)
        return self.enabled


    def get_span_attribute(
        self,
        span: ReadableSpan,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Safely get an attribute from a span.

        Args:
            span: The span
            key: Attribute key
            default: Default value if not found

        Returns:
            Attribute value or default
        """
        from fi.evals.otel.processors.base import (Any, OTEL_AVAILABLE, ReadableSpan)
        if not OTEL_AVAILABLE:
            return default

        try:
            attrs = span.attributes or {}
            return attrs.get(key, default)
        except Exception:
            return default
