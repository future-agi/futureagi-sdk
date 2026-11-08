"""LocalEvaluator can run locally operations."""
from __future__ import annotations

from fi.evals.local.evaluator import (Any, Dict, List, LocalEvaluationResult, Optional)


class _LocalEvaluatorCanRunLocallyMethods:
    __slots__ = ()

    def can_run_locally(self, metric_name: str) -> bool:
        """Check if a metric can be run locally.

        Args:
            metric_name: The name of the metric.

        Returns:
            True if the metric can run locally.
        """
        from fi.evals.local.evaluator import can_run_locally

        return can_run_locally(metric_name) and self.registry.is_registered(metric_name)


    def evaluate(
        self,
        metric_name: str,
        inputs: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> LocalEvaluationResult:
        """Evaluate a single metric on a batch of inputs.

        Args:
            metric_name: The name of the metric to run.
            inputs: List of input dictionaries for the metric.
            config: Optional configuration for the metric.

        Returns:
            LocalEvaluationResult with results and metadata.

        Raises:
            ValueError: If fail_on_unsupported is True and metric can't run locally.
        """
        from fi.evals.local.evaluator import (
            Any, BatchRunResult, Dict, EvalResult, List, LocalEvaluationResult, Optional,
        )
        result = LocalEvaluationResult(results=BatchRunResult(eval_results=[]))

        if not self.can_run_locally(metric_name):
            if self.config.fail_on_unsupported:
                raise ValueError(
                    f"Metric '{metric_name}' cannot run locally. "
                    f"Available local metrics: {self.registry.list_metrics()}"
                )
            result.skipped.add(metric_name)
            # Return empty results for skipped metrics
            for _ in inputs:
                result.results.eval_results.append(
                    EvalResult(
                        name=metric_name,
                        output=None,
                        reason=f"Metric '{metric_name}' cannot run locally",
                        runtime=0,
                    )
                )
            return result

        try:
            metric = self.registry.create(metric_name, config)
            if metric is None:
                raise ValueError(f"Failed to create metric '{metric_name}'")

            batch_result = metric.evaluate(inputs)
            result.results = batch_result
            result.executed_locally.add(metric_name)

        except Exception as e:
            result.errors[metric_name] = str(e)
            # Fill with error results
            for _ in inputs:
                result.results.eval_results.append(
                    EvalResult(
                        name=metric_name,
                        output=None,
                        reason=f"Error: {str(e)}",
                        runtime=0,
                    )
                )

        # Automatically enrich current span with evaluation results
        try:
            from fi.evals.otel.enrichment import enrich_span_with_batch_result, is_auto_enrichment_enabled
            if is_auto_enrichment_enabled():
                enriched_count = enrich_span_with_batch_result(result.results)
                if enriched_count > 0:
                    import logging
                    logging.debug(f"Enriched active span with {enriched_count} evaluation results")
        except ImportError:
            pass  # OTEL enrichment not available
        except Exception:
            pass  # Silently fail enrichment

        return result


    def evaluate_batch(
        self,
        evaluations: List[Dict[str, Any]],
    ) -> LocalEvaluationResult:
        """Evaluate multiple metrics on their respective inputs.

        Args:
            evaluations: List of evaluation specifications, each containing:
                - metric_name: Name of the metric
                - inputs: List of input dictionaries
                - config: Optional metric configuration

        Returns:
            LocalEvaluationResult with combined results.

        Example:
            >>> evaluator = LocalEvaluator()
            >>> result = evaluator.evaluate_batch([
            ...     {
            ...         "metric_name": "contains",
            ...         "inputs": [{"response": "hello world"}],
            ...         "config": {"keyword": "world"}
            ...     },
            ...     {
            ...         "metric_name": "is_json",
            ...         "inputs": [{"response": '{"key": "value"}'}]
            ...     }
            ... ])
        """
        from fi.evals.local.evaluator import (
            Any, BatchRunResult, Dict, List, LocalEvaluationResult,
        )
        combined_result = LocalEvaluationResult(
            results=BatchRunResult(eval_results=[])
        )

        for eval_spec in evaluations:
            metric_name = eval_spec.get("metric_name")
            inputs = eval_spec.get("inputs", [])
            config = eval_spec.get("config")

            if not metric_name:
                continue

            single_result = self.evaluate(metric_name, inputs, config)

            # Merge results
            combined_result.results.eval_results.extend(
                single_result.results.eval_results
            )
            combined_result.executed_locally.update(single_result.executed_locally)
            combined_result.skipped.update(single_result.skipped)
            combined_result.errors.update(single_result.errors)

        return combined_result


    def list_available_metrics(self) -> List[str]:
        """List all metrics available for local execution.

        Returns:
            Sorted list of available metric names.
        """
        from fi.evals.local.evaluator import (List)
        return self.registry.list_metrics()
