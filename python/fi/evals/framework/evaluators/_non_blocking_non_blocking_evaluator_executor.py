"""NonBlockingEvaluator executor operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.framework.evaluators.non_blocking import (
    Any, BaseEvaluation, BatchEvalFuture, Callable, ContextCarrier, Dict, EvalContext, EvalFuture,
    EvalResult, List, Optional, ThreadPoolExecutor,
)

if TYPE_CHECKING:
    from fi.evals.framework.evaluators.non_blocking import NonBlockingEvaluator


class _NonBlockingEvaluatorExecutorMethods:
    __slots__ = ()

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Get or create the thread pool executor."""
        from fi.evals.framework.evaluators.non_blocking import (ThreadPoolExecutor)
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(
                        max_workers=self.max_workers,
                        thread_name_prefix="eval_worker_",
                    )
        return self._executor


    def add_evaluation(self, evaluation: BaseEvaluation) -> "NonBlockingEvaluator":
        """
        Add an evaluation to run.

        Args:
            evaluation: The evaluation to add

        Returns:
            Self for chaining
        """
        from fi.evals.framework.evaluators.non_blocking import (BaseEvaluation)
        self.evaluations.append(evaluation)
        return self


    def evaluate(
        self,
        inputs: Dict[str, Any],
        evaluations: Optional[List[BaseEvaluation]] = None,
        context: Optional[EvalContext] = None,
        callback: Optional[Callable[[EvalResult], None]] = None,
    ) -> BatchEvalFuture:
        """
        Run evaluations in background, returning immediately.

        Args:
            inputs: Input data for evaluations
            evaluations: Override evaluations (uses instance evals if None)
            context: Trace context for span enrichment
            callback: Optional callback for each result

        Returns:
            BatchEvalFuture to track/retrieve results

        Raises:
            ValueError: If no evaluations configured
        """
        from fi.evals.framework.evaluators.non_blocking import (
            Any, BaseEvaluation, BatchEvalFuture, Callable, ContextCarrier, Dict, EvalContext,
            EvalResult, List, Optional, register_current_span,
        )
        evals_to_run = evaluations if evaluations is not None else self.evaluations
        if not evals_to_run:
            raise ValueError("No evaluations to run")

        # Capture context for span enrichment
        carrier = ContextCarrier.capture() if context is None else ContextCarrier(context)

        # Register current span if enrichment enabled
        if self.auto_enrich_span:
            register_current_span()

        # Submit all evaluations
        futures = []
        for evaluation in evals_to_run:
            future = self._submit_evaluation(
                evaluation=evaluation,
                inputs=inputs,
                carrier=carrier,
                callback=callback,
            )
            futures.append(future)

        return BatchEvalFuture(futures=futures)


    def evaluate_single(
        self,
        evaluation: BaseEvaluation,
        inputs: Dict[str, Any],
        context: Optional[EvalContext] = None,
        callback: Optional[Callable[[EvalResult], None]] = None,
    ) -> EvalFuture:
        """
        Run a single evaluation in background.

        Args:
            evaluation: The evaluation to run
            inputs: Input data
            context: Trace context
            callback: Optional result callback

        Returns:
            EvalFuture to track/retrieve result
        """
        from fi.evals.framework.evaluators.non_blocking import (
            Any, BaseEvaluation, Callable, ContextCarrier, Dict, EvalContext, EvalFuture,
            EvalResult, Optional, register_current_span,
        )
        carrier = ContextCarrier.capture() if context is None else ContextCarrier(context)

        if self.auto_enrich_span:
            register_current_span()

        return self._submit_evaluation(
            evaluation=evaluation,
            inputs=inputs,
            carrier=carrier,
            callback=callback,
        )


    def _submit_evaluation(
        self,
        evaluation: BaseEvaluation,
        inputs: Dict[str, Any],
        carrier: ContextCarrier,
        callback: Optional[Callable[[EvalResult], None]] = None,
    ) -> EvalFuture:
        """Submit a single evaluation to the thread pool."""
        from fi.evals.framework.evaluators.non_blocking import (
            Any, BaseEvaluation, Callable, ContextCarrier, Dict, EvalFuture, EvalResult, Optional,
        )
        eval_name = getattr(evaluation, "name", evaluation.__class__.__name__)
        eval_version = getattr(evaluation, "version", "1.0.0")

        future = self.executor.submit(
            self._run_evaluation,
            evaluation=evaluation,
            inputs=inputs,
            carrier=carrier,
            callback=callback,
        )

        return EvalFuture(
            future=future,
            eval_name=eval_name,
            eval_version=eval_version,
            context=carrier.context,
        )


    def _run_evaluation(
        self,
        evaluation: BaseEvaluation,
        inputs: Dict[str, Any],
        carrier: ContextCarrier,
        callback: Optional[Callable[[EvalResult], None]] = None,
    ) -> EvalResult:
        """
        Run evaluation in background thread.

        Handles:
        - Input validation
        - Timing
        - Error handling
        - Span enrichment
        - Callback invocation
        """
        from fi.evals.framework.evaluators.non_blocking import (
            Any, BaseEvaluation, Callable, ContextCarrier, Dict, EvalResult, EvalStatus, Optional,
            time,
        )
        eval_name = getattr(evaluation, "name", evaluation.__class__.__name__)
        eval_version = getattr(evaluation, "version", "1.0.0")

        start_time = time.perf_counter()

        try:
            # Validate inputs if enabled
            if self.validate_inputs:
                validate = getattr(evaluation, "validate_inputs", None)
                if validate:
                    errors = validate(inputs)
                    if errors:
                        return EvalResult.failure(
                            eval_name=eval_name,
                            eval_version=eval_version,
                            error=f"Validation errors: {errors}",
                        )

            # Run the evaluation
            value = evaluation.evaluate(inputs)

            latency_ms = (time.perf_counter() - start_time) * 1000

            result = EvalResult(
                value=value,
                eval_name=eval_name,
                eval_version=eval_version,
                latency_ms=latency_ms,
                status=EvalStatus.COMPLETED,
            )

            # Enrich span with results
            if self.auto_enrich_span:
                self._enrich_span(evaluation, result, carrier)

            # Invoke callback
            if callback:
                try:
                    callback(result)
                except Exception:
                    pass  # Don't fail evaluation for callback errors

            return result

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000

            result = EvalResult.failure(
                eval_name=eval_name,
                eval_version=eval_version,
                error=str(e),
            )
            result.latency_ms = latency_ms

            # Enrich span with failure
            if self.auto_enrich_span:
                self._enrich_span_failure(eval_name, result, carrier)

            # Invoke callback even on failure
            if callback:
                try:
                    callback(result)
                except Exception:
                    pass

            return result


    def _enrich_span(
        self,
        evaluation: BaseEvaluation,
        result: EvalResult,
        carrier: ContextCarrier,
    ) -> bool:
        """Enrich the original span with evaluation results."""
        from fi.evals.framework.evaluators.non_blocking import (
            BaseEvaluation, ContextCarrier, EvalResult,
        )
        eval_name = result.eval_name.replace("-", "_").replace(" ", "_")
        prefix = f"eval.{eval_name}"

        # Get span attributes from evaluation
        get_attrs = getattr(evaluation, "get_span_attributes", None)
        if get_attrs:
            try:
                eval_attrs = get_attrs(result.value)
            except Exception:
                eval_attrs = {}
        else:
            eval_attrs = {}

        # Build attributes
        attributes = {
            f"{prefix}.status": result.status.value,
            f"{prefix}.latency_ms": result.latency_ms,
            f"{prefix}.version": result.eval_version,
        }

        # Add eval-specific attributes
        for key, value in eval_attrs.items():
            if isinstance(value, (str, int, float, bool)):
                attributes[f"{prefix}.{key}"] = value

        return carrier.enrich_span(attributes)


    def _enrich_span_failure(
        self,
        eval_name: str,
        result: EvalResult,
        carrier: ContextCarrier,
    ) -> bool:
        """Enrich span with failure information."""
        from fi.evals.framework.evaluators.non_blocking import (ContextCarrier, EvalResult)
        safe_name = eval_name.replace("-", "_").replace(" ", "_")
        prefix = f"eval.{safe_name}"

        attributes = {
            f"{prefix}.status": result.status.value,
            f"{prefix}.latency_ms": result.latency_ms,
            f"{prefix}.error": result.error or "Unknown error",
        }

        return carrier.enrich_span(attributes)


    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the executor.

        Args:
            wait: Whether to wait for pending tasks to complete
        """
        if self._executor and self._owns_executor:
            self._executor.shutdown(wait=wait)
            self._executor = None
