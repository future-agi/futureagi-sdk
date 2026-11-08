"""
Evaluation Span Processor.

Enriches LLM spans with evaluation scores by running
configured metrics against the prompt/completion pairs.
"""

from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, Future
import logging
import time
import random
import hashlib

from .base import BaseSpanProcessor, OTEL_AVAILABLE
from ..conventions import (
    GenAIAttributes,
    EvaluationAttributes,
    create_evaluation_attributes,
)
from ..types import EvaluationResult

if OTEL_AVAILABLE:
    from opentelemetry.sdk.trace import ReadableSpan
else:
    ReadableSpan = Any

logger = logging.getLogger(__name__)


# Type alias for evaluator function
EvaluatorFn = Callable[[str, str, Optional[str]], List[EvaluationResult]]


from ._evaluation_evaluation_span_processor_should_process import _EvaluationSpanProcessorShouldProcessMethods
from ._evaluation_evaluation_span_processor_get_cached_results import _EvaluationSpanProcessorGetCachedResultsMethods

class EvaluationSpanProcessor(
    _EvaluationSpanProcessorShouldProcessMethods,
    _EvaluationSpanProcessorGetCachedResultsMethods,
    BaseSpanProcessor,
):
    """
    Processor that evaluates LLM spans and attaches scores.

    This processor runs configured evaluation metrics against
    the prompt/completion pairs in LLM spans and records the
    evaluation results as span attributes or events.

    Supports:
    - Multiple evaluation metrics
    - Sampling (evaluate only a fraction of spans)
    - Async evaluation (non-blocking)
    - Result caching
    - Timeout handling

    Example:
        from fi.evals import evaluate

        processor = EvaluationSpanProcessor(
            metrics=["relevance", "coherence", "faithfulness"],
            sample_rate=0.1,  # Evaluate 10% of spans
            async_evaluation=True,
        )

        # Or with custom evaluator
        processor = EvaluationSpanProcessor(
            evaluator=my_custom_evaluator,
            metrics=["custom_metric"],
        )
    """

    def __init__(
        self,
        metrics: Optional[List[str]] = None,
        evaluator: Optional[EvaluatorFn] = None,
        sample_rate: float = 1.0,
        async_evaluation: bool = True,
        timeout_ms: int = 5000,
        cache_enabled: bool = True,
        cache_ttl_seconds: int = 3600,
        max_workers: int = 4,
        evaluator_model: Optional[str] = None,
        on_evaluation_complete: Optional[Callable[[str, List[EvaluationResult]], None]] = None,
        enabled: bool = True,
    ):
        """
        Initialize the evaluation processor.

        Args:
            metrics: List of metrics to evaluate (e.g., ["relevance", "coherence"])
            evaluator: Custom evaluator function, or None to use default
            sample_rate: Fraction of spans to evaluate (0.0 to 1.0)
            async_evaluation: Whether to evaluate asynchronously
            timeout_ms: Timeout for evaluation in milliseconds
            cache_enabled: Whether to cache evaluation results
            cache_ttl_seconds: Cache TTL in seconds
            max_workers: Max threads for async evaluation
            evaluator_model: Model to use for LLM-based evaluation
            on_evaluation_complete: Callback when evaluation completes
            enabled: Whether processor is active
        """
        super().__init__(enabled=enabled)
        self._metrics = metrics or ["relevance", "coherence"]
        self._evaluator = evaluator
        self._sample_rate = max(0.0, min(1.0, sample_rate))
        self._async_evaluation = async_evaluation
        self._timeout_ms = timeout_ms
        self._cache_enabled = cache_enabled
        self._cache_ttl_seconds = cache_ttl_seconds
        self._max_workers = max_workers
        self._evaluator_model = evaluator_model
        self._on_evaluation_complete = on_evaluation_complete

        # Internal state
        self._executor: Optional[ThreadPoolExecutor] = None
        self._cache: Dict[str, tuple[float, List[EvaluationResult]]] = {}
        self._pending_evaluations: Dict[str, Future] = {}


    def shutdown(self) -> None:
        """Shutdown the processor."""
        super().shutdown()

        # Wait for pending evaluations
        for span_id, future in list(self._pending_evaluations.items()):
            try:
                future.result(timeout=self._timeout_ms / 1000)
            except Exception as e:
                logger.warning(f"Pending evaluation {span_id} failed: {e}")

        self._pending_evaluations.clear()

        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

        # Clear cache
        self._cache.clear()


class BatchEvaluationProcessor(EvaluationSpanProcessor):
    """
    Evaluation processor that batches evaluations for efficiency.

    Collects spans and evaluates them in batches rather than
    one at a time, which can be more efficient for some evaluators.

    Example:
        processor = BatchEvaluationProcessor(
            batch_size=10,
            batch_timeout_ms=1000,
        )
    """

    def __init__(
        self,
        batch_size: int = 10,
        batch_timeout_ms: int = 1000,
        **kwargs,
    ):
        """
        Initialize batch evaluation processor.

        Args:
            batch_size: Maximum batch size
            batch_timeout_ms: Max time to wait for batch
            **kwargs: Additional args for EvaluationSpanProcessor
        """
        super().__init__(**kwargs)
        self._batch_size = batch_size
        self._batch_timeout_ms = batch_timeout_ms
        self._batch: List[tuple[str, str, str, Optional[str]]] = []
        self._last_batch_time = time.time()

    def on_end(self, span: ReadableSpan) -> None:
        """Add span to batch for evaluation."""
        if not self.should_process(span):
            return

        try:
            attrs = self._get_attributes(span)
            span_id = self._get_span_id(span)
            prompt = self._extract_prompt(attrs)
            completion = self._extract_completion(attrs)
            model = attrs.get(GenAIAttributes.REQUEST_MODEL)

            if not prompt or not completion:
                return

            # Add to batch
            self._batch.append((span_id, prompt, completion, model))

            # Check if we should process batch
            if len(self._batch) >= self._batch_size:
                self._process_batch()
            elif (time.time() - self._last_batch_time) * 1000 >= self._batch_timeout_ms:
                self._process_batch()

        except Exception as e:
            logger.warning(f"Batch evaluation error: {e}")

    def _process_batch(self) -> None:
        """Process the accumulated batch."""
        if not self._batch:
            return

        batch = self._batch
        self._batch = []
        self._last_batch_time = time.time()

        # Evaluate each item in the batch
        for span_id, prompt, completion, model in batch:
            cache_key = self._compute_cache_key(prompt, completion, self._metrics)
            cached = self._get_cached_results(cache_key)

            if cached is not None:
                self._handle_results(span_id, cached)
            else:
                results = self._evaluate_sync(prompt, completion, model)
                self._cache_results(cache_key, results)
                self._handle_results(span_id, results)

    def shutdown(self) -> None:
        """Process remaining batch and shutdown."""
        self._process_batch()
        super().shutdown()


__all__ = [
    "EvaluationSpanProcessor",
    "BatchEvaluationProcessor",
]
