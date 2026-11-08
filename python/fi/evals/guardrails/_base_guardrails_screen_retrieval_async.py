"""Guardrails screen retrieval async operations."""
from __future__ import annotations

from fi.evals.guardrails.base import (
    Any, Dict, GuardrailsResponse, List, Optional, RailType, _trace_guardrail,
)


class _GuardrailsScreenRetrievalAsyncMethods:
    __slots__ = ()

    async def screen_retrieval_async(
        self,
        chunks: List[str],
        query: Optional[str] = None,
    ) -> List[GuardrailsResponse]:
        """Async version of screen_retrieval."""
        from fi.evals.guardrails.base import (GuardrailsResponse, List, Optional, RailType, asyncio)
        tasks = [
            self._screen_async(
                chunk,
                RailType.RETRIEVAL,
                metadata={"query": query} if query else None,
            )
            for chunk in chunks
        ]
        return await asyncio.gather(*tasks)


    async def screen_batch_async(
        self,
        contents: List[str],
        rail_type: RailType = RailType.INPUT,
    ) -> List[GuardrailsResponse]:
        """Process multiple inputs in parallel."""
        from fi.evals.guardrails.base import (GuardrailsResponse, List, RailType, asyncio)
        tasks = [self._screen_async(c, rail_type) for c in contents]
        return await asyncio.gather(*tasks)


    @_trace_guardrail
    def _screen_sync(
        self,
        content: str,
        rail_type: RailType,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GuardrailsResponse:
        """
        Synchronous screening using scanners and backends.

        Flow:
        1. Run fast scanners first (<10ms each)
        2. If scanners block, optionally skip slow model backends
        3. Run model backends
        4. Aggregate all results

        Args:
            content: Content to screen
            rail_type: Type of rail
            context: Optional context
            metadata: Optional metadata

        Returns:
            Aggregated GuardrailsResponse
        """
        from fi.evals.guardrails.base import (
            AggregationStrategy, Any, Dict, FuturesTimeoutError, GuardrailResult,
            GuardrailsResponse, Optional, RailType, ThreadPoolExecutor, _trace_guardrail,
            as_completed, time,
        )
        start_time = time.time()

        # Handle empty content
        if not content or not content.strip():
            return GuardrailsResponse.create_passed(
                content=content,
                latency_ms=(time.time() - start_time) * 1000,
                models_used=[m.value for m in self.backends.keys()],
            )

        all_results: List[GuardrailResult] = []
        errors: List[str] = []
        scanner_blocked = False

        # Step 1: Run fast scanners first
        if self.scanner_pipeline:
            try:
                pipeline_result = self.scanner_pipeline.scan(content, context)

                # Convert scanner results to GuardrailResults
                for scan_result in pipeline_result.results:
                    guardrail_result = GuardrailResult(
                        category=scan_result.category,
                        score=scan_result.score,
                        passed=scan_result.passed,
                        model=f"scanner:{scan_result.scanner_name}",
                        reason=scan_result.reason,
                        latency_ms=scan_result.latency_ms,
                    )
                    all_results.append(guardrail_result)

                scanner_blocked = not pipeline_result.passed

                # If fail_fast is enabled and scanners blocked, skip model backends
                if scanner_blocked and self.config.scanners and self.config.scanners.fail_fast:
                    elapsed_ms = (time.time() - start_time) * 1000
                    return self._aggregate_results(content, all_results, elapsed_ms)

            except Exception as e:
                errors.append(f"scanner_pipeline: {str(e)}")

        # Step 2: Run model backends
        use_weighted_early_exit = (
            self.config.aggregation == AggregationStrategy.WEIGHTED
            and len(self.backends) > 1
        )

        if self.config.parallel and len(self.backends) > 1:
            # Run backends in parallel
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_model = {
                    executor.submit(
                        backend.classify,
                        content,
                        rail_type,
                        context,
                        metadata,
                    ): model
                    for model, backend in self.backends.items()
                }

                timeout_seconds = self.config.timeout_ms / 1000.0
                weights = self.config.model_weights
                total_weight = sum(
                    weights.get(m.value, 1.0) for m in self.backends
                )
                failed_weight = 0.0
                passed_weight = 0.0

                try:
                    for future in as_completed(future_to_model, timeout=timeout_seconds):
                        model = future_to_model[future]
                        try:
                            results = future.result()
                            all_results.extend(results)

                            # Early exit for WEIGHTED: if accumulated weight
                            # already decides the outcome, cancel remaining futures
                            if use_weighted_early_exit:
                                w = weights.get(model.value, 1.0)
                                has_fail = any(not r.passed for r in results)
                                if has_fail:
                                    failed_weight += w
                                else:
                                    passed_weight += w
                                threshold = self.config.weighted_threshold
                                if failed_weight > threshold * total_weight:
                                    # Enough weight to block — cancel the rest
                                    for f in future_to_model:
                                        f.cancel()
                                    break
                                if passed_weight >= (1 - threshold) * total_weight:
                                    # Remaining models can't tip the balance — pass early
                                    for f in future_to_model:
                                        f.cancel()
                                    break

                        except Exception as e:
                            errors.append(f"{model.value}: {str(e)}")
                except FuturesTimeoutError:
                    errors.append("Timeout waiting for backends")
        else:
            # Run backends sequentially
            weights = self.config.model_weights
            total_weight = sum(
                weights.get(m.value, 1.0) for m in self.backends
            )
            failed_weight = 0.0
            passed_weight = 0.0

            for model, backend in self.backends.items():
                try:
                    results = backend.classify(content, rail_type, context, metadata)
                    all_results.extend(results)

                    # Early exit for WEIGHTED sequential
                    if use_weighted_early_exit:
                        w = weights.get(model.value, 1.0)
                        has_fail = any(not r.passed for r in results)
                        if has_fail:
                            failed_weight += w
                        else:
                            passed_weight += w
                        threshold = self.config.weighted_threshold
                        if failed_weight > threshold * total_weight:
                            break
                        if passed_weight >= (1 - threshold) * total_weight:
                            break

                except Exception as e:
                    errors.append(f"{model.value}: {str(e)}")

        elapsed_ms = (time.time() - start_time) * 1000

        # Handle errors
        if not all_results and errors:
            return GuardrailsResponse.create_error(
                content=content,
                error="; ".join(errors),
                fail_open=self.config.fail_open,
            )

        # Aggregate results
        return self._aggregate_results(content, all_results, elapsed_ms)
