"""
Base Span Processors.

Foundation classes for span processing in the OTEL integration.
Processors can filter, enrich, and transform spans before export.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor
import logging

try:
    from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan
    from opentelemetry.context import Context
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # Define stub types for when OTEL is not installed
    SpanProcessor = object
    ReadableSpan = Any
    Context = Any

logger = logging.getLogger(__name__)


from ._base_base_span_processor_enabled import _BaseSpanProcessorEnabledMethods

class BaseSpanProcessor(_BaseSpanProcessorEnabledMethods, ABC):
    """
    Base class for custom span processors.

    Span processors intercept spans at various lifecycle points:
    - on_start: When a span is started
    - on_end: When a span is ended

    Subclasses can enrich spans with additional attributes,
    filter spans, or perform side effects like evaluation.

    Example:
        class MyProcessor(BaseSpanProcessor):
            def on_end(self, span: ReadableSpan) -> None:
                if self.should_process(span):
                    self.enrich_span(span)
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize the processor.

        Args:
            enabled: Whether this processor is active
        """
        self._enabled = enabled
        self._shutdown = False


class FilteringSpanProcessor(BaseSpanProcessor):
    """
    A processor that filters spans based on criteria.

    Only processes spans that match the filter function.
    Useful for processing only LLM spans, only certain models, etc.

    Example:
        # Only process OpenAI spans
        processor = FilteringSpanProcessor(
            filter_fn=lambda span: span.attributes.get("gen_ai.system") == "openai",
            delegate=MyEnrichmentProcessor(),
        )
    """

    def __init__(
        self,
        filter_fn: Callable[[ReadableSpan], bool],
        delegate: Optional[BaseSpanProcessor] = None,
        enabled: bool = True,
    ):
        """
        Initialize the filtering processor.

        Args:
            filter_fn: Function that returns True for spans to process
            delegate: Optional processor to delegate to for matching spans
            enabled: Whether this processor is active
        """
        super().__init__(enabled=enabled)
        self._filter_fn = filter_fn
        self._delegate = delegate

    def should_process(self, span: ReadableSpan) -> bool:
        """Check if span passes the filter."""
        if not self.enabled:
            return False
        try:
            return self._filter_fn(span)
        except Exception as e:
            logger.warning(f"Filter function error: {e}")
            return False

    def on_end(self, span: ReadableSpan) -> None:
        """Process span if it passes the filter."""
        if self.should_process(span) and self._delegate:
            self._delegate.on_end(span)

    def shutdown(self) -> None:
        """Shutdown delegate processor."""
        super().shutdown()
        if self._delegate:
            self._delegate.shutdown()


from ._base_composite_span_processor_add_processor import _CompositeSpanProcessorAddProcessorMethods

class CompositeSpanProcessor(_CompositeSpanProcessorAddProcessorMethods, BaseSpanProcessor):
    """
    A processor that combines multiple processors.

    Runs all child processors on each span. Can run processors
    in sequence or parallel.

    Example:
        processor = CompositeSpanProcessor([
            LLMSpanProcessor(),
            EvaluationSpanProcessor(metrics=["relevance"]),
            CostSpanProcessor(),
        ])
    """

    def __init__(
        self,
        processors: List[BaseSpanProcessor],
        parallel: bool = False,
        max_workers: int = 4,
        enabled: bool = True,
    ):
        """
        Initialize the composite processor.

        Args:
            processors: List of processors to run
            parallel: Whether to run processors in parallel
            max_workers: Max threads for parallel execution
            enabled: Whether this processor is active
        """
        super().__init__(enabled=enabled)
        self._processors = processors
        self._parallel = parallel
        self._max_workers = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None


    def shutdown(self) -> None:
        """Shutdown all child processors."""
        super().shutdown()

        for processor in self._processors:
            try:
                processor.shutdown()
            except Exception as e:
                logger.warning(f"Processor shutdown error: {e}")

        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None


class AttributeEnrichmentProcessor(BaseSpanProcessor):
    """
    A processor that adds static attributes to spans.

    Useful for adding deployment info, version numbers, or
    other metadata to all spans.

    Example:
        processor = AttributeEnrichmentProcessor({
            "deployment.environment": "production",
            "service.version": "1.2.3",
            "team": "ml-platform",
        })
    """

    def __init__(
        self,
        attributes: Dict[str, Any],
        enabled: bool = True,
    ):
        """
        Initialize with attributes to add.

        Args:
            attributes: Static attributes to add to all spans
            enabled: Whether this processor is active
        """
        super().__init__(enabled=enabled)
        self._attributes = attributes

    def on_end(self, span: ReadableSpan) -> None:
        """Add attributes to span (Note: spans are read-only at end)."""
        # Note: In OTEL, spans are read-only after ending.
        # This processor is mainly useful for on_start enrichment.
        # For on_end, we'd need to use span events or a different approach.
        pass

    def on_start(
        self,
        span: Any,
        parent_context: Optional[Context] = None,
    ) -> None:
        """Add attributes when span starts."""
        if not self.enabled:
            return

        try:
            for key, value in self._attributes.items():
                span.set_attribute(key, value)
        except Exception as e:
            logger.warning(f"Failed to set attributes: {e}")


class ConditionalProcessor(BaseSpanProcessor):
    """
    A processor that conditionally delegates based on span attributes.

    Allows different processing paths for different span types.

    Example:
        processor = ConditionalProcessor(
            conditions=[
                (lambda s: s.attributes.get("gen_ai.system") == "openai", openai_processor),
                (lambda s: s.attributes.get("gen_ai.system") == "anthropic", anthropic_processor),
            ],
            default=generic_processor,
        )
    """

    def __init__(
        self,
        conditions: List[tuple[Callable[[ReadableSpan], bool], BaseSpanProcessor]],
        default: Optional[BaseSpanProcessor] = None,
        enabled: bool = True,
    ):
        """
        Initialize with conditions and delegates.

        Args:
            conditions: List of (condition, processor) tuples
            default: Default processor if no conditions match
            enabled: Whether this processor is active
        """
        super().__init__(enabled=enabled)
        self._conditions = conditions
        self._default = default

    def on_end(self, span: ReadableSpan) -> None:
        """Route span to appropriate processor."""
        if not self.enabled:
            return

        for condition_fn, processor in self._conditions:
            try:
                if condition_fn(span):
                    processor.on_end(span)
                    return
            except Exception as e:
                logger.warning(f"Condition check error: {e}")

        # No condition matched, use default
        if self._default:
            self._default.on_end(span)

    def shutdown(self) -> None:
        """Shutdown all delegate processors."""
        super().shutdown()

        for _, processor in self._conditions:
            try:
                processor.shutdown()
            except Exception as e:
                logger.warning(f"Processor shutdown error: {e}")

        if self._default:
            self._default.shutdown()


__all__ = [
    "BaseSpanProcessor",
    "FilteringSpanProcessor",
    "CompositeSpanProcessor",
    "AttributeEnrichmentProcessor",
    "ConditionalProcessor",
    "OTEL_AVAILABLE",
]
