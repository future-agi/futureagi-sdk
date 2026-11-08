"""
Non-blocking evaluation executor.

Provides async/background evaluation with zero latency impact on the main thread.
Uses thread pools for local execution with context propagation.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading
import uuid
import time

from ..types import FrameworkEvalResult as EvalResult, EvalStatus, BatchEvalResult
from ..context import EvalContext
from ..protocols import BaseEvaluation
from ..registry import register_span, get_span, register_current_span
from ..propagation import ContextCarrier, enrich_span_by_context


@dataclass
class EvalFuture:
    """
    Future representing a pending evaluation.

    Wraps the underlying executor future and provides convenience methods.

    Example:
        future = evaluator.evaluate(inputs)
        # Do other work...
        result = future.result()  # Block until complete
    """

    future: Future
    eval_name: str
    eval_version: str
    context: Optional[EvalContext] = None
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def done(self) -> bool:
        """Check if evaluation is complete."""
        return self.future.done()

    def result(self, timeout: Optional[float] = None) -> EvalResult:
        """
        Get the evaluation result, blocking if necessary.

        Args:
            timeout: Maximum seconds to wait (None = wait forever)

        Returns:
            EvalResult from the evaluation

        Raises:
            TimeoutError: If timeout exceeded
            Exception: If evaluation raised an exception
        """
        return self.future.result(timeout=timeout)

    def cancel(self) -> bool:
        """
        Attempt to cancel the evaluation.

        Returns:
            True if cancelled, False if already running/complete
        """
        return self.future.cancel()

    def cancelled(self) -> bool:
        """Check if evaluation was cancelled."""
        return self.future.cancelled()

    def add_done_callback(self, fn: Callable[["EvalFuture"], None]) -> None:
        """
        Add callback to run when evaluation completes.

        Args:
            fn: Callback function taking this EvalFuture
        """

        def wrapper(f):
            fn(self)

        self.future.add_done_callback(wrapper)


@dataclass
class BatchEvalFuture:
    """Future representing a batch of evaluations."""

    futures: List[EvalFuture]
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def done(self) -> bool:
        """Check if all evaluations are complete."""
        return all(f.done() for f in self.futures)

    def results(self, timeout: Optional[float] = None) -> BatchEvalResult:
        """
        Get all results, blocking if necessary.

        Args:
            timeout: Maximum seconds to wait for ALL results

        Returns:
            BatchEvalResult with all evaluation results
        """
        results = []
        for f in self.futures:
            try:
                results.append(f.result(timeout=timeout))
            except Exception as e:
                # Create failure result for exceptions
                results.append(
                    EvalResult.failure(
                        eval_name=f.eval_name,
                        eval_version=f.eval_version,
                        error=str(e),
                    )
                )
        return BatchEvalResult.from_results(results)

    def cancel_all(self) -> int:
        """
        Cancel all pending evaluations.

        Returns:
            Number of successfully cancelled evaluations
        """
        return sum(1 for f in self.futures if f.cancel())


from fi.evals._extracted import bind_owner as _bind_owner
from ._non_blocking_non_blocking_evaluator_executor import _NonBlockingEvaluatorExecutorMethods
from ._non_blocking_non_blocking_evaluator_enter import _NonBlockingEvaluatorEnterMethods

class NonBlockingEvaluator(_NonBlockingEvaluatorExecutorMethods, _NonBlockingEvaluatorEnterMethods):
    """
    Non-blocking evaluation executor using thread pool.

    Runs evaluations in background threads with zero latency impact.
    Automatically enriches spans with results when complete.

    Example:
        evaluator = NonBlockingEvaluator(
            evaluations=[ToxicityEval(), BiasEval()],
            max_workers=4,
        )

        # Returns immediately
        future = evaluator.evaluate({"response": "..."})

        # Later, check results
        if future.done():
            result = future.result()

        # Or wait for result
        result = future.result(timeout=5.0)

    Thread Safety:
        This class is thread-safe. Multiple threads can call evaluate()
        concurrently.
    """

    def __init__(
        self,
        evaluations: Optional[List[BaseEvaluation]] = None,
        max_workers: int = 4,
        auto_enrich_span: bool = True,
        fail_fast: bool = False,
        validate_inputs: bool = True,
        executor: Optional[ThreadPoolExecutor] = None,
    ):
        """
        Initialize the non-blocking evaluator.

        Args:
            evaluations: List of evaluations to run
            max_workers: Maximum concurrent evaluations
            auto_enrich_span: Whether to auto-enrich spans with results
            fail_fast: Stop on first failure (for batch operations)
            validate_inputs: Whether to validate inputs before evaluation
            executor: Custom executor (uses internal pool if None)
        """
        self.evaluations = list(evaluations) if evaluations else []
        self.max_workers = max_workers
        self.auto_enrich_span = auto_enrich_span
        self.fail_fast = fail_fast
        self.validate_inputs = validate_inputs

        # Use provided executor or create our own
        self._executor = executor
        self._owns_executor = executor is None
        self._lock = threading.Lock()


_bind_owner(NonBlockingEvaluator)


def non_blocking_evaluate(
    inputs: Dict[str, Any],
    *evaluations: BaseEvaluation,
    max_workers: int = 4,
    auto_enrich_span: bool = True,
    callback: Optional[Callable[[EvalResult], None]] = None,
) -> BatchEvalFuture:
    """
    Convenience function for non-blocking evaluation.

    Runs evaluations in background and returns immediately.
    The internal executor is automatically shut down when all futures complete.

    Args:
        inputs: Input data for evaluations
        *evaluations: Evaluations to run
        max_workers: Maximum concurrent evaluations
        auto_enrich_span: Whether to enrich spans with results
        callback: Optional callback for each result

    Returns:
        BatchEvalFuture to track/retrieve results

    Example:
        future = non_blocking_evaluate(
            {"response": "..."},
            ToxicityEval(),
            BiasEval(),
        )
        # Do other work...
        results = future.results()
    """
    evaluator = NonBlockingEvaluator(
        evaluations=list(evaluations),
        max_workers=max_workers,
        auto_enrich_span=auto_enrich_span,
    )
    batch_future = evaluator.evaluate(inputs, callback=callback)

    # Auto-shutdown executor when all futures complete
    pending = [f.future for f in batch_future.futures]
    remaining = {id(f) for f in pending}

    def _on_done(f):
        remaining.discard(id(f))
        if not remaining:
            evaluator.shutdown(wait=False)

    for f in pending:
        f.add_done_callback(_on_done)

    return batch_future


class EvalResultAggregator:
    """
    Aggregates results from multiple async evaluations.

    Useful for collecting results from different evaluation runs.

    Example:
        aggregator = EvalResultAggregator()

        # Add results as they come in
        aggregator.add(future1.result())
        aggregator.add(future2.result())

        # Get aggregated results
        batch = aggregator.to_batch()
        print(f"Success rate: {batch.success_rate}")
    """

    def __init__(self):
        self._results: List[EvalResult] = []
        self._lock = threading.Lock()

    def add(self, result: EvalResult) -> None:
        """Add a result to the aggregator."""
        with self._lock:
            self._results.append(result)

    def add_all(self, results: List[EvalResult]) -> None:
        """Add multiple results."""
        with self._lock:
            self._results.extend(results)

    def to_batch(self) -> BatchEvalResult:
        """Get aggregated results as a batch."""
        with self._lock:
            return BatchEvalResult.from_results(list(self._results))

    def clear(self) -> int:
        """Clear all results and return count cleared."""
        with self._lock:
            count = len(self._results)
            self._results.clear()
            return count

    @property
    def count(self) -> int:
        """Get current result count."""
        with self._lock:
            return len(self._results)
