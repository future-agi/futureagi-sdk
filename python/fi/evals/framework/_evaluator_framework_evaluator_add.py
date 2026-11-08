"""FrameworkEvaluator add operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.framework.evaluator import (
    Any, BaseEvaluation, BlockingEvaluator, Callable, Dict, EvalContext, EvalResult,
    EvaluatorResult, NonBlockingEvaluator, Optional,
)

if TYPE_CHECKING:
    from fi.evals.framework.evaluator import FrameworkEvaluator


class _FrameworkEvaluatorAddMethods:
    __slots__ = ()

    def add(self, evaluation: BaseEvaluation) -> "FrameworkEvaluator":
        """
        Add an evaluation to run.

        Args:
            evaluation: The evaluation to add

        Returns:
            Self for chaining
        """
        from fi.evals.framework.evaluator import (BaseEvaluation)
        self.evaluations.append(evaluation)
        return self


    def add_by_name(self, name: str, version: str = "latest") -> "FrameworkEvaluator":
        """
        Add an evaluation by name from the registry.

        Args:
            name: Evaluation name
            version: Version (default: latest)

        Returns:
            Self for chaining

        Raises:
            KeyError: If evaluation not found
        """
        from fi.evals.framework.evaluator import (EvalRegistry)
        eval_class = EvalRegistry.get(name, version)
        if eval_class is None:
            raise KeyError(f"Evaluation not found: {name}@{version}")
        self.evaluations.append(eval_class())
        return self


    def run(
        self,
        inputs: Dict[str, Any],
        context: Optional[EvalContext] = None,
        callback: Optional[Callable[[EvalResult], None]] = None,
    ) -> EvaluatorResult:
        """
        Run all evaluations on the given inputs.

        Args:
            inputs: Input data for evaluations
            context: Optional trace context for span enrichment
            callback: Optional callback for each result (non-blocking only)

        Returns:
            EvaluatorResult wrapping results or future

        Raises:
            ValueError: If no evaluations configured
        """
        from fi.evals.framework.evaluator import (
            Any, Callable, Dict, EvalContext, EvalResult, EvaluatorResult, ExecutionMode, Optional,
        )
        if not self.evaluations:
            raise ValueError("No evaluations configured")

        if self.mode == ExecutionMode.BLOCKING:
            return self._run_blocking(inputs, context)
        elif self.mode == ExecutionMode.NON_BLOCKING:
            return self._run_non_blocking(inputs, context, callback)
        elif self.mode == ExecutionMode.DISTRIBUTED:
            return self._run_distributed(inputs, context, callback)
        else:
            raise ValueError(f"Unknown execution mode: {self.mode}")


    def run_single(
        self,
        evaluation: BaseEvaluation,
        inputs: Dict[str, Any],
        context: Optional[EvalContext] = None,
    ) -> EvalResult:
        """
        Run a single evaluation.

        Always runs in blocking mode for simplicity.

        Args:
            evaluation: The evaluation to run
            inputs: Input data
            context: Optional trace context

        Returns:
            Single EvalResult
        """
        from fi.evals.framework.evaluator import (
            Any, BaseEvaluation, Dict, EvalContext, EvalResult, Optional,
        )
        evaluator = self._get_blocking_evaluator()
        results = evaluator.evaluate(inputs, evaluations=[evaluation], context=context)
        return results[0]


    def _run_blocking(
        self,
        inputs: Dict[str, Any],
        context: Optional[EvalContext],
    ) -> EvaluatorResult:
        """Run evaluations in blocking mode."""
        from fi.evals.framework.evaluator import (
            Any, BatchEvalResult, Dict, EvalContext, EvaluatorResult, ExecutionMode, Optional,
        )
        evaluator = self._get_blocking_evaluator()
        results = evaluator.evaluate(inputs, context=context)
        batch = BatchEvalResult.from_results(results)

        return EvaluatorResult(
            batch=batch,
            mode=ExecutionMode.BLOCKING,
        )


    def _run_non_blocking(
        self,
        inputs: Dict[str, Any],
        context: Optional[EvalContext],
        callback: Optional[Callable[[EvalResult], None]],
    ) -> EvaluatorResult:
        """Run evaluations in non-blocking mode."""
        from fi.evals.framework.evaluator import (
            Any, Callable, Dict, EvalContext, EvalResult, EvaluatorResult, ExecutionMode, Optional,
        )
        evaluator = self._get_non_blocking_evaluator()
        future = evaluator.evaluate(inputs, context=context, callback=callback)

        return EvaluatorResult(
            future=future,
            mode=ExecutionMode.NON_BLOCKING,
        )


    def _run_distributed(
        self,
        inputs: Dict[str, Any],
        context: Optional[EvalContext],
        callback: Optional[Callable[[EvalResult], None]],
    ) -> EvaluatorResult:
        """
        Run evaluations in distributed mode.

        Uses the configured backend for execution. Submits each evaluation
        as a task to the backend, collects results, and returns a BatchEvalResult.
        Falls back to non-blocking if no backend is configured.
        """
        from fi.evals.framework.evaluator import (
            Any, BatchEvalResult, Callable, Dict, EvalContext, EvalResult, EvalStatus,
            EvaluatorResult, ExecutionMode, Optional, _execute_single_evaluation,
        )
        if self._backend is None:
            return self._run_non_blocking(inputs, context, callback)

        context_dict = None
        if context and hasattr(context, "to_dict"):
            context_dict = context.to_dict()

        # Submit each evaluation as a task to the backend, collecting handles
        # or immediate failure results
        handles = []  # List of (index, handle) for successful submissions
        results = [None] * len(self.evaluations)  # Pre-allocate result slots

        for i, evaluation in enumerate(self.evaluations):
            eval_name = getattr(evaluation, "name", evaluation.__class__.__name__)
            eval_version = getattr(evaluation, "version", "1.0.0")
            try:
                handle = self._backend.submit(
                    _execute_single_evaluation,
                    args=(evaluation, inputs, self.validate_inputs),
                    context=context_dict,
                )
                handles.append((i, handle))
            except Exception as e:
                error_result = EvalResult(
                    value=None,
                    eval_name=eval_name,
                    eval_version=eval_version,
                    latency_ms=0.0,
                    status=EvalStatus.FAILED,
                    error=str(e),
                )
                results[i] = error_result
                if callback:
                    callback(error_result)

        # Collect results from successful submissions
        timeout = self._backend_timeout
        for i, handle in handles:
            evaluation = self.evaluations[i]
            eval_name = getattr(evaluation, "name", evaluation.__class__.__name__)
            eval_version = getattr(evaluation, "version", "1.0.0")
            try:
                result = self._backend.get_result(handle, timeout=timeout)
                results[i] = result
                if callback:
                    callback(result)
            except Exception as e:
                error_result = EvalResult(
                    value=None,
                    eval_name=eval_name,
                    eval_version=eval_version,
                    latency_ms=0.0,
                    status=EvalStatus.FAILED,
                    error=str(e),
                )
                results[i] = error_result
                if callback:
                    callback(error_result)

        batch = BatchEvalResult.from_results(results)
        return EvaluatorResult(
            batch=batch,
            mode=ExecutionMode.DISTRIBUTED,
        )


    @property
    def _backend_timeout(self) -> float:
        """Get timeout from backend config, defaulting to 300s."""
        if self._backend and hasattr(self._backend, "config"):
            config = self._backend.config
            if hasattr(config, "timeout_seconds"):
                return config.timeout_seconds
        return 300.0


    def _get_blocking_evaluator(self) -> BlockingEvaluator:
        """Get or create the blocking evaluator."""
        from fi.evals.framework.evaluator import (BlockingEvaluator)
        if self._blocking is None:
            self._blocking = BlockingEvaluator(
                evaluations=self.evaluations,
                auto_enrich_span=self.auto_enrich_span,
                fail_fast=self.fail_fast,
                validate_inputs=self.validate_inputs,
            )
        return self._blocking


    def _get_non_blocking_evaluator(self) -> NonBlockingEvaluator:
        """Get or create the non-blocking evaluator."""
        from fi.evals.framework.evaluator import (NonBlockingEvaluator)
        if self._non_blocking is None:
            self._non_blocking = NonBlockingEvaluator(
                evaluations=self.evaluations,
                max_workers=self.max_workers,
                auto_enrich_span=self.auto_enrich_span,
                fail_fast=self.fail_fast,
                validate_inputs=self.validate_inputs,
            )
        return self._non_blocking


    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the evaluator and release resources.

        Args:
            wait: Whether to wait for pending evaluations
        """
        if self._non_blocking:
            self._non_blocking.shutdown(wait=wait)
            self._non_blocking = None
        if self._backend:
            self._backend.shutdown(wait=wait)


    def __enter__(self) -> "FrameworkEvaluator":
        return self


    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown(wait=True)
