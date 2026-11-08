"""Carrier for propagation."""
from __future__ import annotations

from fi.evals.framework.propagation import (
    Any, Dict, EvalContext, Generator, Optional, SpanContextPropagator, contextmanager,
    enrich_span_by_context,
)

class ContextCarrier:
    """
    Helper class for carrying context across boundaries.

    Combines EvalContext with additional metadata needed for
    distributed evaluation.

    Example:
        # Create carrier
        carrier = ContextCarrier.capture()

        # Serialize for transmission
        data = carrier.to_dict()

        # Reconstruct in worker
        carrier = ContextCarrier.from_dict(data)
        with carrier.activate():
            # Run in original context
            pass
    """

    def __init__(
        self,
        context: EvalContext,
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.context = context
        self.headers = headers or {}
        self.metadata = metadata or {}

    @classmethod
    def capture(cls, metadata: Optional[Dict[str, Any]] = None) -> "ContextCarrier":
        """
        Capture current context into a carrier.

        Args:
            metadata: Optional additional metadata

        Returns:
            ContextCarrier with captured context
        """
        context = EvalContext.from_current_span()

        # Also capture raw headers
        headers: Dict[str, str] = {}
        SpanContextPropagator.inject(headers)

        return cls(
            context=context,
            headers=headers,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for transmission."""
        return {
            "context": self.context.to_dict(),
            "headers": self.headers,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextCarrier":
        """Deserialize from dict."""
        return cls(
            context=EvalContext.from_dict(data["context"]),
            headers=data.get("headers", {}),
            metadata=data.get("metadata", {}),
        )

    @contextmanager
    def activate(self) -> Generator["ContextCarrier", None, None]:
        """
        Context manager to activate this carrier's context.

        Yields:
            Self for accessing context/metadata
        """
        with SpanContextPropagator.with_context(self.context):
            yield self

    def enrich_span(self, attributes: Dict[str, Any]) -> bool:
        """
        Enrich the original span with attributes.

        Args:
            attributes: Attributes to add

        Returns:
            True if enrichment succeeded
        """
        return enrich_span_by_context(self.context, attributes)


def propagate_context(func):
    """
    Decorator to propagate context to a function running in another thread.

    Captures the current context at call time (when the wrapper is invoked)
    and activates it in the background thread.

    Example:
        @propagate_context
        def background_task(x, y):
            # This runs in the caller's trace context
            return x + y

        # Context is captured when submit() calls the wrapper
        executor.submit(background_task, 1, 2)
    """
    from fi.evals.framework.propagation import (ContextCarrier)
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Capture context at call time, not decoration time
        carrier = ContextCarrier.capture()
        with carrier.activate():
            return func(*args, **kwargs)

    return wrapper


def propagate_context_lazy(func):
    """
    Decorator to propagate context, capturing at call time.

    Unlike propagate_context, this captures context when the wrapped
    function is called, not when decorated.

    Example:
        @propagate_context_lazy
        def background_task(x, y):
            return x + y

        # Context is captured here, when submitted
        executor.submit(background_task, 1, 2)
    """
    from fi.evals.framework.propagation import (ContextCarrier)
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Capture context at call time
        carrier = ContextCarrier.capture()

        def run():
            with carrier.activate():
                return func(*args, **kwargs)

        return run

    return wrapper
