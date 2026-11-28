"""EvaluationSpanProcessor get cached results operations."""
from __future__ import annotations

from fi.evals.otel.processors.evaluation import (Any, Dict, EvaluationResult, List, Optional)


class _EvaluationSpanProcessorGetCachedResultsMethods:
    __slots__ = ()

    def _get_cached_results(self, cache_key: str) -> Optional[List[EvaluationResult]]:
        """Get cached results if valid."""
        from fi.evals.otel.processors.evaluation import (EvaluationResult, List, Optional, time)
        if not self._cache_enabled:
            return None

        if cache_key not in self._cache:
            return None

        timestamp, results = self._cache[cache_key]
        if time.time() - timestamp > self._cache_ttl_seconds:
            # Expired
            del self._cache[cache_key]
            return None

        return results


    def _cache_results(self, cache_key: str, results: List[EvaluationResult]) -> None:
        """Cache evaluation results."""
        from fi.evals.otel.processors.evaluation import (EvaluationResult, List, time)
        if not self._cache_enabled:
            return

        self._cache[cache_key] = (time.time(), results)

        # Cleanup old entries if cache is too large
        if len(self._cache) > 10000:
            self._cleanup_cache()


    def _cleanup_cache(self) -> None:
        """Remove expired cache entries."""
        from fi.evals.otel.processors.evaluation import (time)
        current_time = time.time()
        expired = [
            key for key, (ts, _) in self._cache.items()
            if current_time - ts > self._cache_ttl_seconds
        ]
        for key in expired:
            del self._cache[key]


    def get_evaluation_attributes(
        self,
        results: List[EvaluationResult],
    ) -> Dict[str, Any]:
        """
        Convert evaluation results to span attributes.

        Uses gen_ai.evaluation.* namespace.

        Args:
            results: List of evaluation results

        Returns:
            Dictionary of OTEL-compliant attributes
        """
        from fi.evals.otel.processors.evaluation import (
            Any, Dict, EvaluationResult, List, create_evaluation_attributes,
        )
        attrs: Dict[str, Any] = {}

        for result in results:
            # Dual-write via helper
            result_attrs = create_evaluation_attributes(
                metric=result.metric,
                score=result.score,
                reason=result.reason,
                latency_ms=result.latency_ms,
            )
            attrs.update(result_attrs)

        return attrs


    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Wait for pending evaluations."""
        success = True
        per_eval_timeout = timeout_millis / 1000 / max(len(self._pending_evaluations), 1)

        for span_id, future in list(self._pending_evaluations.items()):
            try:
                future.result(timeout=per_eval_timeout)
            except Exception:
                success = False

        return success
