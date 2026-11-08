"""
Unified Evaluator API.

Provides a single interface for running evaluations in any mode:
- Blocking: Synchronous execution, waits for results
- Non-blocking: Background execution, zero latency
- Distributed: Scalable execution via pluggable backends

Example:
    from fi.evals.framework import Evaluator, ExecutionMode

    # Create evaluator
    evaluator = Evaluator(
        evaluations=[ToxicityEval(), BiasEval()],
        mode=ExecutionMode.NON_BLOCKING,
    )

    # Run evaluations (returns immediately in non-blocking mode)
    result = evaluator.run({"response": "..."})

    # Get results when needed
    if result.is_future:
        batch = result.wait()
    else:
        batch = result.batch
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .types import ExecutionMode, FrameworkEvalResult, BatchEvalResult, EvalStatus

# Internal alias for brevity — this is the framework-level EvalResult
EvalResult = FrameworkEvalResult
from .context import EvalContext
from .protocols import BaseEvaluation, EvalRegistry
from .evaluators.blocking import BlockingEvaluator
from .evaluators.non_blocking import (
    NonBlockingEvaluator,
    BatchEvalFuture,
    EvalFuture,
)
from .backends import Backend, ThreadPoolBackend, ThreadPoolConfig

logger = logging.getLogger(__name__)


@dataclass
class EvaluatorResult:
    """
    Result from an evaluator run.

    Wraps either immediate results (blocking) or futures (non-blocking).

    Attributes:
        batch: Immediate BatchEvalResult (blocking mode)
        future: BatchEvalFuture for async results (non-blocking mode)
        mode: The execution mode used
        submitted_at: When the evaluation was submitted
    """

    batch: Optional[BatchEvalResult] = None
    future: Optional[BatchEvalFuture] = None
    mode: ExecutionMode = ExecutionMode.BLOCKING
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_future(self) -> bool:
        """Whether this result is a future (non-blocking)."""
        return self.future is not None

    @property
    def is_ready(self) -> bool:
        """Whether results are ready."""
        if self.batch is not None:
            return True
        if self.future is not None:
            return self.future.done()
        return False

    def wait(self, timeout: Optional[float] = None) -> BatchEvalResult:
        """
        Wait for and return results.

        Args:
            timeout: Maximum seconds to wait (non-blocking only)

        Returns:
            BatchEvalResult with all evaluation results
        """
        if self.batch is not None:
            return self.batch
        if self.future is not None:
            return self.future.results(timeout=timeout)
        raise ValueError("No results available")

    @property
    def results(self) -> List[EvalResult]:
        """Get individual results (waits if necessary)."""
        return self.wait().results

    @property
    def success_rate(self) -> float:
        """Get success rate (waits if necessary)."""
        return self.wait().success_rate


from fi.evals._extracted import bind_owner as _bind_owner
from ._evaluator_framework_evaluator_add import _FrameworkEvaluatorAddMethods

class FrameworkEvaluator(_FrameworkEvaluatorAddMethods):
    """
    Unified evaluator for all execution modes.

    Provides a consistent interface regardless of how evaluations are executed.
    Supports blocking, non-blocking, and distributed modes with automatic
    span enrichment.

    Example:
        # Simple blocking usage
        evaluator = FrameworkEvaluator([ToxicityEval()])
        result = evaluator.run({"response": "..."})
        print(f"Score: {result.results[0].value}")

        # Non-blocking for production
        evaluator = FrameworkEvaluator(
            [ToxicityEval(), BiasEval()],
            mode=ExecutionMode.NON_BLOCKING,
        )
        result = evaluator.run({"response": "..."})  # Returns immediately
        # ... do other work ...
        batch = result.wait()  # Get results when needed

        # With custom backend
        evaluator = FrameworkEvaluator(
            [ToxicityEval()],
            mode=ExecutionMode.NON_BLOCKING,
            backend=MyTemporalBackend(),
        )

    Thread Safety:
        This class is thread-safe. Multiple threads can call run() concurrently.
    """

    def __init__(
        self,
        evaluations: Optional[List[BaseEvaluation]] = None,
        mode: ExecutionMode = ExecutionMode.BLOCKING,
        auto_enrich_span: bool = True,
        fail_fast: bool = False,
        validate_inputs: bool = True,
        max_workers: int = 4,
        backend: Optional[Backend] = None,
    ):
        """
        Initialize the evaluator.

        Args:
            evaluations: List of evaluations to run
            mode: Execution mode (BLOCKING, NON_BLOCKING, DISTRIBUTED)
            auto_enrich_span: Whether to automatically enrich OTEL spans
            fail_fast: Stop on first failure
            validate_inputs: Whether to validate inputs before evaluation
            max_workers: Max concurrent workers (non-blocking/distributed)
            backend: Custom backend for execution (uses ThreadPool if None)
        """
        self.evaluations = list(evaluations) if evaluations else []
        self.mode = mode
        self.auto_enrich_span = auto_enrich_span
        self.fail_fast = fail_fast
        self.validate_inputs = validate_inputs
        self.max_workers = max_workers
        self._backend = backend

        # Internal evaluators (created lazily)
        self._blocking: Optional[BlockingEvaluator] = None
        self._non_blocking: Optional[NonBlockingEvaluator] = None


_bind_owner(FrameworkEvaluator)


# Factory functions for common configurations


from ._evaluator_factories import blocking_evaluator
blocking_evaluator.__module__ = __name__


from ._evaluator_factories import async_evaluator
async_evaluator.__module__ = __name__


from ._evaluator_factories import distributed_evaluator
distributed_evaluator.__module__ = __name__


def _execute_single_evaluation(
    evaluation: BaseEvaluation,
    inputs: Dict[str, Any],
    validate: bool = True,
) -> EvalResult:
    """
    Execute a single evaluation, suitable for submission to any backend.

    Handles validation, timing, and error capture.

    Args:
        evaluation: The evaluation to run
        inputs: Input data
        validate: Whether to validate inputs

    Returns:
        EvalResult with value or error
    """
    eval_name = getattr(evaluation, "name", evaluation.__class__.__name__)
    eval_version = getattr(evaluation, "version", "1.0.0")

    # Validate inputs if enabled
    if validate and hasattr(evaluation, "validate_inputs"):
        try:
            errors = evaluation.validate_inputs(inputs)
            if errors:
                error_msg = "; ".join(str(e) for e in errors) if isinstance(errors, list) else str(errors)
                return EvalResult(
                    value=None,
                    eval_name=eval_name,
                    eval_version=eval_version,
                    latency_ms=0.0,
                    status=EvalStatus.FAILED,
                    error=f"Validation error: {error_msg}",
                )
        except Exception as e:
            return EvalResult(
                value=None,
                eval_name=eval_name,
                eval_version=eval_version,
                latency_ms=0.0,
                status=EvalStatus.FAILED,
                error=f"Validation exception: {e}",
            )

    start = time.perf_counter()
    try:
        value = evaluation.evaluate(inputs)
        latency_ms = (time.perf_counter() - start) * 1000
        return EvalResult(
            value=value,
            eval_name=eval_name,
            eval_version=eval_version,
            latency_ms=latency_ms,
            status=EvalStatus.COMPLETED,
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return EvalResult(
            value=None,
            eval_name=eval_name,
            eval_version=eval_version,
            latency_ms=latency_ms,
            status=EvalStatus.FAILED,
            error=str(e),
        )


from ._evaluator_factories import resilient_evaluator
resilient_evaluator.__module__ = __name__
