"""Guardrails screen async operations."""
from __future__ import annotations

from fi.evals.guardrails.base import (
    Any, Dict, GuardrailResult, GuardrailsResponse, List, Optional, RailType,
)


class _GuardrailsScreenAsyncMethods:
    __slots__ = ()

    async def _screen_async(
        self,
        content: str,
        rail_type: RailType,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GuardrailsResponse:
        """
        Asynchronous screening using scanners and backends.

        Flow:
        1. Run fast scanners first (<10ms each)
        2. If scanners block, optionally skip slow model backends
        3. Run model backends in parallel
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
            Any, Dict, GuardrailResult, GuardrailsResponse, Optional, RailType, asyncio, time,
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
        scanner_blocked = False

        # Step 1: Run fast scanners first (sync, as they're already fast)
        if self.scanner_pipeline:
            try:
                pipeline_result = await self.scanner_pipeline.scan_async(content, context)

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

            except Exception:
                pass  # Continue with model backends even if scanners fail

        # Step 2: Run all backends in parallel
        tasks = [
            backend.classify_async(content, rail_type, context, metadata)
            for backend in self.backends.values()
        ]

        try:
            timeout_seconds = self.config.timeout_ms / 1000.0
            results_list = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            if self.config.fail_open:
                return GuardrailsResponse.create_passed(
                    content=content,
                    latency_ms=(time.time() - start_time) * 1000,
                    models_used=[m.value for m in self.backends.keys()],
                )
            else:
                return GuardrailsResponse.create_error(
                    content=content,
                    error="Timeout waiting for backends",
                    fail_open=False,
                )

        elapsed_ms = (time.time() - start_time) * 1000

        # Flatten backend results
        for result in results_list:
            if isinstance(result, Exception):
                continue
            all_results.extend(result)

        return self._aggregate_results(content, all_results, elapsed_ms)


    def _aggregate_results(
        self,
        content: str,
        results: List[GuardrailResult],
        elapsed_ms: float,
    ) -> GuardrailsResponse:
        """
        Aggregate results from multiple backends using configured strategy.

        Args:
            content: Original content
            results: Results from all backends
            elapsed_ms: Total elapsed time

        Returns:
            Aggregated GuardrailsResponse
        """
        from fi.evals.guardrails.base import (GuardrailResult, GuardrailsResponse, List)
        models_used = [m.value for m in self.backends.keys()]

        if not results:
            return GuardrailsResponse.create_passed(
                content=content,
                latency_ms=elapsed_ms,
                models_used=models_used,
            )

        # Check for error results - if all results are errors, fail closed (unless fail_open)
        error_results = [r for r in results if r.category == "error"]
        non_error_results = [r for r in results if r.category != "error"]

        if not non_error_results:
            # All results are errors
            if self.config.fail_open:
                return GuardrailsResponse.create_passed(
                    content=content,
                    latency_ms=elapsed_ms,
                    models_used=models_used,
                    results=results,
                )
            else:
                error_msg = "; ".join(r.reason or "Unknown error" for r in error_results)
                return GuardrailsResponse(
                    passed=False,
                    results=results,
                    blocked_categories=["error"],
                    original_content=content,
                    total_latency_ms=elapsed_ms,
                    models_used=models_used,
                    error=error_msg,
                )

        # Apply category thresholds
        processed_results = self._apply_thresholds(results)

        # Count total distinct models/scanners that produced results.
        # Models that didn't flag a category are implicit "pass" votes.
        all_model_names = set(r.model for r in processed_results)
        total_voters = len(all_model_names)

        # Group results by category
        category_results: Dict[str, List[GuardrailResult]] = {}
        for result in processed_results:
            if result.category not in category_results:
                category_results[result.category] = []
            category_results[result.category].append(result)

        # Apply aggregation strategy
        blocked_categories: List[str] = []
        flagged_categories: List[str] = []

        for category, cat_results in category_results.items():
            if category in ("safe", "empty", "error"):
                continue

            should_block = self._should_block(cat_results, total_voters)

            if should_block:
                category_config = self.config.categories.get(category)
                if category_config:
                    if category_config.action == "block":
                        blocked_categories.append(category)
                    elif category_config.action == "flag":
                        flagged_categories.append(category)
                else:
                    blocked_categories.append(category)

        # Create response
        passed = len(blocked_categories) == 0
        models_used = [m.value for m in self.backends.keys()]

        return GuardrailsResponse(
            passed=passed,
            results=processed_results,
            blocked_categories=blocked_categories,
            flagged_categories=flagged_categories,
            original_content=content,
            total_latency_ms=elapsed_ms,
            models_used=models_used,
        )


    def _apply_thresholds(
        self,
        results: List[GuardrailResult],
    ) -> List[GuardrailResult]:
        """
        Apply category-specific thresholds to results.

        Args:
            results: Raw results from backends

        Returns:
            Results with thresholds applied
        """
        from fi.evals.guardrails.base import (GuardrailResult, List)
        processed = []
        for result in results:
            category_config = self.config.categories.get(result.category)
            if category_config and category_config.enabled:
                if result.score >= category_config.threshold:
                    result.passed = False
                    result.action = category_config.action
                else:
                    result.passed = True
                    result.action = "pass"
            processed.append(result)
        return processed


    def _should_block(self, cat_results: List[GuardrailResult], total_voters: int = 0) -> bool:
        """
        Determine if content should be blocked based on aggregation strategy.

        Args:
            cat_results: Results for a single category from all models.
            total_voters: Total distinct models/scanners that ran.
                Models that didn't flag this category are implicit passes.

        Returns:
            True if content should be blocked
        """
        from fi.evals.guardrails.base import (AggregationStrategy, GuardrailResult, List)
        if not cat_results:
            return False

        failed_count = sum(1 for r in cat_results if not r.passed)
        # Use total_voters (all models that ran) as denominator, not just
        # models that flagged this specific category. Models that returned
        # "safe" instead are implicit passes for any category they didn't flag.
        total_count = max(total_voters, len(cat_results))
        strategy = self.config.aggregation

        if strategy == AggregationStrategy.ANY:
            return failed_count > 0
        elif strategy == AggregationStrategy.ALL:
            return failed_count == total_count
        elif strategy == AggregationStrategy.MAJORITY:
            return failed_count > total_count / 2
        elif strategy == AggregationStrategy.WEIGHTED:
            weights = self.config.model_weights
            # Total weight includes ALL models that ran (from backends dict),
            # not just those that flagged this specific category.
            total_weight = sum(
                weights.get(m.value, 1.0) for m in self.backends
            )
            if total_weight == 0:
                # Fallback: just use weights from cat_results
                total_weight = sum(weights.get(r.model, 1.0) for r in cat_results)
            if total_weight == 0:
                return False
            failed_weight = 0.0
            for r in cat_results:
                if not r.passed:
                    failed_weight += weights.get(r.model, 1.0)
            return failed_weight > self.config.weighted_threshold * total_weight
        else:
            return failed_count > 0


    def __repr__(self) -> str:
        models = [m.value for m in self.config.models]
        return f"Guardrails(models={models}, aggregation={self.config.aggregation.value})"
