"""EvalDelegateScanner scan operations."""
from __future__ import annotations

from fi.evals.guardrails.scanners.eval_delegate import (Optional, ScanResult)


class _EvalDelegateScannerScanMethods:
    __slots__ = ()

    def scan(self, content: str, context: Optional[str] = None) -> ScanResult:
        """
        Scan content using delegated evaluations.

        Args:
            content: Content to scan
            context: Optional context

        Returns:
            ScanResult with aggregated results from all categories
        """
        from fi.evals.guardrails.scanners.eval_delegate import (
            EVAL_TEMPLATE_MAP, Optional, ScanMatch, ScanResult, time,
        )
        if not self.enabled:
            return self._create_result(
                passed=True,
                reason="Scanner disabled",
            )

        start_time = time.perf_counter()
        matches = []
        category_results = {}

        # Evaluate each category
        if self.parallel and len(self.categories) > 1:
            # Parallel execution
            from concurrent.futures import ThreadPoolExecutor, as_completed

            with ThreadPoolExecutor(max_workers=len(self.categories)) as executor:
                futures = {
                    executor.submit(self._evaluate_category, content, cat, context): cat
                    for cat in self.categories
                }

                for future in as_completed(futures, timeout=self.timeout):
                    cat = futures[future]
                    try:
                        category_results[cat] = future.result()
                    except Exception as e:
                        category_results[cat] = {
                            "passed": True,
                            "score": 0.0,
                            "reason": f"Timeout/error: {str(e)}",
                            "latency_ms": 0,
                            "source": "error",
                        }
        else:
            # Sequential execution
            for cat in self.categories:
                category_results[cat] = self._evaluate_category(content, cat, context)

        # Aggregate results
        failed_categories = []
        total_score = 0.0

        for cat, result in category_results.items():
            total_score += result["score"]

            if not result["passed"]:
                failed_categories.append(cat)
                template_info = EVAL_TEMPLATE_MAP[cat]
                matches.append(ScanMatch(
                    pattern_name=f"eval:{cat.value}",
                    matched_text=content[:100] + "..." if len(content) > 100 else content,
                    start=0,
                    end=len(content),
                    confidence=result["score"],
                    metadata={
                        "category": cat.value,
                        "eval_name": template_info["eval_name"],
                        "threshold": self._get_threshold(cat),
                        "source": result.get("source", "unknown"),
                    },
                ))

        # Determine overall pass/fail
        if self.aggregation == "any":
            passed = len(failed_categories) == 0
        else:  # "all"
            passed = len(failed_categories) < len(self.categories)

        # Calculate average score
        avg_score = total_score / len(self.categories) if self.categories else 0.0

        # Generate reason
        if passed:
            reason = f"All {len(self.categories)} eval checks passed"
        else:
            failed_names = [c.value for c in failed_categories]
            reason = f"Failed eval checks: {', '.join(failed_names)}"

        total_latency = (time.perf_counter() - start_time) * 1000

        return self._create_result(
            passed=passed,
            matches=matches,
            score=avg_score,
            reason=reason,
            latency_ms=total_latency,
            metadata={
                "categories_checked": [c.value for c in self.categories],
                "categories_failed": [c.value for c in failed_categories],
                "category_results": {
                    c.value: {
                        "passed": r["passed"],
                        "score": r["score"],
                        "source": r.get("source", "unknown"),
                    }
                    for c, r in category_results.items()
                },
            },
        )
