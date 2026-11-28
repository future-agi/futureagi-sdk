"""EvaluationSpanProcessor should process operations."""
from __future__ import annotations

from fi.evals.otel.processors.evaluation import (
    Any, Dict, EvaluationResult, List, Optional, ReadableSpan,
)


class _EvaluationSpanProcessorShouldProcessMethods:
    __slots__ = ()

    def should_process(self, span: ReadableSpan) -> bool:
        """Determine if span should be evaluated."""
        from fi.evals.otel.processors.evaluation import (ReadableSpan, random)
        if not self.enabled:
            return False

        # Check if it's an LLM span
        attrs = self._get_attributes(span)
        if not self._is_llm_span(attrs):
            return False

        # Check sampling
        if self._sample_rate < 1.0:
            if random.random() > self._sample_rate:
                return False

        return True


    def _is_llm_span(self, attrs: Dict[str, Any]) -> bool:
        """Check if this is an LLM span worth evaluating."""
        from fi.evals.otel.processors.evaluation import (Any, Dict, GenAIAttributes)
        # Has GenAI provider attribute
        if GenAIAttributes.PROVIDER_NAME in attrs:
            return True

        # Has model attribute
        if GenAIAttributes.REQUEST_MODEL in attrs:
            return True

        # Has output messages
        if GenAIAttributes.OUTPUT_MESSAGES in attrs:
            return True

        # Check for common patterns
        for key in attrs:
            if any(pattern in str(key).lower() for pattern in ["llm", "gen_ai", "completion"]):
                return True

        return False


    def _get_attributes(self, span: ReadableSpan) -> Dict[str, Any]:
        """Get span attributes safely."""
        from fi.evals.otel.processors.evaluation import (Any, Dict, ReadableSpan)
        try:
            return dict(span.attributes or {})
        except Exception:
            return {}


    def _get_span_id(self, span: ReadableSpan) -> str:
        """Get unique span identifier."""
        from fi.evals.otel.processors.evaluation import (ReadableSpan)
        try:
            ctx = span.get_span_context()
            return f"{ctx.trace_id:032x}:{ctx.span_id:016x}"
        except Exception:
            return str(id(span))


    def on_end(self, span: ReadableSpan) -> None:
        """Evaluate the span and record results."""
        from fi.evals.otel.processors.evaluation import (GenAIAttributes, ReadableSpan, logger)
        if not self.should_process(span):
            return

        try:
            attrs = self._get_attributes(span)
            span_id = self._get_span_id(span)

            # Extract content for evaluation
            prompt = self._extract_prompt(attrs)
            completion = self._extract_completion(attrs)
            model = attrs.get(GenAIAttributes.REQUEST_MODEL)

            if not prompt or not completion:
                logger.debug(f"Skipping evaluation for span {span_id}: no content")
                return

            # Check cache
            cache_key = self._compute_cache_key(prompt, completion, self._metrics)
            cached_results = self._get_cached_results(cache_key)
            if cached_results is not None:
                logger.debug(f"Using cached evaluation for span {span_id}")
                self._handle_results(span_id, cached_results)
                return

            # Run evaluation
            if self._async_evaluation:
                self._evaluate_async(span_id, prompt, completion, model, cache_key)
            else:
                results = self._evaluate_sync(prompt, completion, model)
                self._cache_results(cache_key, results)
                self._handle_results(span_id, results)

        except Exception as e:
            logger.warning(f"Evaluation processing error: {e}")


    def _extract_prompt(self, attrs: Dict[str, Any]) -> Optional[str]:
        """Extract prompt from span attributes."""
        from fi.evals.otel.processors.evaluation import (Any, Dict, GenAIAttributes, Optional)
        for key in [
            GenAIAttributes.INPUT_MESSAGES,
            "llm.prompt",
            "prompt",
            "input",
        ]:
            if key in attrs:
                return str(attrs[key])
        return None


    def _extract_completion(self, attrs: Dict[str, Any]) -> Optional[str]:
        """Extract completion from span attributes."""
        from fi.evals.otel.processors.evaluation import (Any, Dict, GenAIAttributes, Optional)
        for key in [
            GenAIAttributes.OUTPUT_MESSAGES,
            "llm.completion",
            "completion",
            "output",
            "response",
        ]:
            if key in attrs:
                return str(attrs[key])
        return None


    def _evaluate_sync(
        self,
        prompt: str,
        completion: str,
        model: Optional[str] = None,
    ) -> List[EvaluationResult]:
        """Run evaluation synchronously."""
        from fi.evals.otel.processors.evaluation import (
            EvaluationResult, List, Optional, logger, time,
        )
        start_time = time.time()
        results: List[EvaluationResult] = []

        try:
            if self._evaluator:
                # Use custom evaluator
                results = self._evaluator(prompt, completion, model)
            else:
                # Use default evaluator (fi.evals)
                results = self._run_default_evaluator(prompt, completion, model)

            # Add latency to results
            latency_ms = (time.time() - start_time) * 1000
            for result in results:
                if result.latency_ms is None:
                    result.latency_ms = latency_ms / len(results)

        except Exception as e:
            logger.warning(f"Evaluation failed: {e}")
            # Return error result
            results = [
                EvaluationResult(
                    metric="error",
                    score=0.0,
                    reason=str(e),
                    latency_ms=(time.time() - start_time) * 1000,
                )
            ]

        return results


    def _run_default_evaluator(
        self,
        prompt: str,
        completion: str,
        model: Optional[str] = None,
    ) -> List[EvaluationResult]:
        """Run the default fi.evals evaluator."""
        from fi.evals.otel.processors.evaluation import (
            EvaluationResult, List, Optional, logger, time,
        )
        results: List[EvaluationResult] = []

        try:
            # Import here to avoid circular deps
            from fi.evals import Evaluator

            evaluator = Evaluator()

            for metric in self._metrics:
                start = time.time()
                try:
                    # Try to evaluate with the metric
                    eval_result = evaluator.evaluate(
                        metric=metric,
                        input=prompt,
                        output=completion,
                        model=self._evaluator_model,
                    )

                    results.append(EvaluationResult(
                        metric=metric,
                        score=float(eval_result.get("score", 0.0)),
                        reason=eval_result.get("reason"),
                        latency_ms=(time.time() - start) * 1000,
                    ))

                except Exception as e:
                    logger.warning(f"Metric '{metric}' evaluation failed: {e}")
                    results.append(EvaluationResult(
                        metric=metric,
                        score=0.0,
                        reason=f"Evaluation error: {e}",
                        latency_ms=(time.time() - start) * 1000,
                    ))

        except ImportError:
            logger.warning("fi.evals not available, skipping default evaluation")

        return results


    def _evaluate_async(
        self,
        span_id: str,
        prompt: str,
        completion: str,
        model: Optional[str],
        cache_key: str,
    ) -> None:
        """Run evaluation asynchronously."""
        from fi.evals.otel.processors.evaluation import (Optional, ThreadPoolExecutor)
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)

        def evaluate_task():
            results = self._evaluate_sync(prompt, completion, model)
            self._cache_results(cache_key, results)
            self._handle_results(span_id, results)
            return results

        future = self._executor.submit(evaluate_task)
        self._pending_evaluations[span_id] = future


    def _handle_results(
        self,
        span_id: str,
        results: List[EvaluationResult],
    ) -> None:
        """Handle evaluation results."""
        from fi.evals.otel.processors.evaluation import (EvaluationResult, List, logger)
        # Log results
        for result in results:
            logger.info(
                f"Evaluation [{span_id}] {result.metric}: "
                f"score={result.score:.3f}"
                + (f" reason={result.reason[:50]}..." if result.reason else "")
            )

        # Call callback if configured
        if self._on_evaluation_complete:
            try:
                self._on_evaluation_complete(span_id, results)
            except Exception as e:
                logger.warning(f"Evaluation callback error: {e}")

        # Clean up pending
        self._pending_evaluations.pop(span_id, None)


    def _compute_cache_key(
        self,
        prompt: str,
        completion: str,
        metrics: List[str],
    ) -> str:
        """Compute cache key for evaluation results."""
        from fi.evals.otel.processors.evaluation import (List, hashlib)
        content = f"{prompt}|{completion}|{','.join(sorted(metrics))}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
