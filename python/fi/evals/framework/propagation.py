"""
Context propagation utilities for distributed tracing.

This module provides utilities for propagating trace context across thread
and process boundaries, enabling:
- Background threads to operate within the original trace context
- Distributed workers to maintain trace continuity
- Async evaluations to enrich parent spans
"""

from typing import Dict, Any, Optional, Generator
from contextlib import contextmanager
from .context import EvalContext
from .registry import get_span, register_span


class SpanContextPropagator:
    """
    Propagate and restore span context across boundaries.

    Supports:
    - Thread boundaries (same process)
    - Process boundaries (via headers)
    - Async boundaries (futures)

    Example:
        # Capture context before spawning thread
        carrier = {}
        SpanContextPropagator.inject(carrier)

        # In background thread
        context = SpanContextPropagator.extract(carrier)
        with SpanContextPropagator.with_context(context):
            # Code runs in original trace context
            pass
    """

    @staticmethod
    def inject(carrier: Dict[str, str]) -> bool:
        """
        Inject current trace context into carrier.

        Uses W3C Trace Context format (traceparent, baggage headers).

        Args:
            carrier: Dict to inject headers into (modified in place)

        Returns:
            True if context was injected, False if no active context
        """
        try:
            from opentelemetry.propagate import inject
            inject(carrier)
            return bool(carrier)
        except ImportError:
            # Fallback: inject from EvalContext
            try:
                ctx = EvalContext.from_current_span()
                if ctx.is_valid:
                    carrier.update(ctx.to_headers())
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    def extract(carrier: Dict[str, str]) -> EvalContext:
        """
        Extract trace context from carrier.

        Args:
            carrier: Dict containing trace headers

        Returns:
            EvalContext reconstructed from headers
        """
        return EvalContext.from_headers(carrier)

    @staticmethod
    @contextmanager
    def with_context(context: EvalContext) -> Generator[None, None, None]:
        """
        Context manager to run code with specific trace context.

        Useful for background threads that need to operate in
        the context of a specific trace.

        Args:
            context: EvalContext to activate

        Yields:
            None

        Example:
            ctx = EvalContext.from_current_span()

            def background_task():
                with SpanContextPropagator.with_context(ctx):
                    # This code runs in the original trace context
                    span = trace.get_current_span()
                    span.set_attribute("from_background", True)
        """
        try:
            from opentelemetry import trace
            from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags
            from opentelemetry.context import attach, detach

            # Create a span context from our EvalContext
            span_context = SpanContext(
                trace_id=int(context.trace_id, 16),
                span_id=int(context.span_id, 16),
                is_remote=True,
                trace_flags=TraceFlags(0x01),  # Sampled
            )

            # Create a non-recording span with this context
            span = NonRecordingSpan(span_context)

            # Attach to current context
            ctx = trace.set_span_in_context(span)
            token = attach(ctx)

            try:
                yield
            finally:
                detach(token)
        except ImportError:
            # No OTEL - just yield
            yield
        except Exception:
            # Any other error - just yield
            yield

    @staticmethod
    def create_child_context(parent: EvalContext) -> EvalContext:
        """
        Create a child context from a parent.

        Maintains the same trace_id but generates a new span_id.

        Args:
            parent: Parent context

        Returns:
            New child EvalContext
        """
        return parent.child_context()


def enrich_span_by_context(
    context: EvalContext,
    attributes: Dict[str, Any],
) -> bool:
    """
    Enrich a span using its context, even from a different thread.

    This looks up the span in the registry and adds attributes to it.

    Args:
        context: The EvalContext identifying the span
        attributes: Attributes to add (will be filtered for valid types)

    Returns:
        True if enrichment succeeded, False otherwise

    Example:
        # In main thread
        ctx = EvalContext.from_current_span()
        register_current_span()

        # In background thread
        enrich_span_by_context(ctx, {
            "eval.faithfulness.score": 0.95,
            "eval.faithfulness.async": True,
        })
    """
    span = get_span(context.trace_id, context.span_id)
    if span is None:
        return False

    try:
        if not span.is_recording():
            return False

        for key, value in attributes.items():
            if value is not None and _is_valid_attribute(value):
                span.set_attribute(key, value)

        return True
    except Exception:
        return False


def enrich_span_by_ids(
    trace_id: str,
    span_id: str,
    attributes: Dict[str, Any],
) -> bool:
    """
    Enrich a span by trace/span IDs.

    Convenience wrapper around enrich_span_by_context.

    Args:
        trace_id: The trace ID
        span_id: The span ID
        attributes: Attributes to add

    Returns:
        True if enrichment succeeded
    """
    span = get_span(trace_id, span_id)
    if span is None:
        return False

    try:
        if not span.is_recording():
            return False

        for key, value in attributes.items():
            if value is not None and _is_valid_attribute(value):
                span.set_attribute(key, value)

        return True
    except Exception:
        return False


def add_event_by_context(
    context: EvalContext,
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Add an event to a span using its context.

    Args:
        context: The EvalContext identifying the span
        name: Event name
        attributes: Optional event attributes

    Returns:
        True if event was added
    """
    span = get_span(context.trace_id, context.span_id)
    if span is None:
        return False

    try:
        if not span.is_recording():
            return False

        event_attrs = {}
        if attributes:
            for key, value in attributes.items():
                if value is not None and _is_valid_attribute(value):
                    event_attrs[key] = value

        span.add_event(name, attributes=event_attrs if event_attrs else None)
        return True
    except Exception:
        return False


def _is_valid_attribute(value: Any) -> bool:
    """Check if a value is valid for span attributes."""
    return isinstance(value, (str, int, float, bool))


from ._propagation_carrier import ContextCarrier
ContextCarrier.__module__ = __name__


from ._propagation_carrier import propagate_context
propagate_context.__module__ = __name__


from ._propagation_carrier import propagate_context_lazy
propagate_context_lazy.__module__ = __name__
