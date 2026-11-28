"""HybridEvaluator set local llm operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.local.evaluator import (Any, Dict, List, LocalEvaluationResult, Optional, RoutingMode)

if TYPE_CHECKING:
    from .llm import OllamaLLM


class _HybridEvaluatorSetLocalLlmMethods:
    __slots__ = ()

    def set_local_llm(self, llm: "OllamaLLM") -> None:
        """Set the local LLM instance.

        Args:
            llm: OllamaLLM instance to use for LLM-based evaluations.
        """
        self.local_llm = llm


    def set_cloud_evaluator(self, evaluator: Any) -> None:
        """Set the cloud evaluator instance.

        Args:
            evaluator: Cloud Evaluator instance for API-based evaluations.
        """
        from fi.evals.local.evaluator import (Any)
        self.cloud_evaluator = evaluator


    def can_use_local_llm(self, metric_name: str) -> bool:
        """Check if a metric can use the local LLM.

        Args:
            metric_name: The name of the metric.

        Returns:
            True if the metric can use local LLM.
        """
        if self.local_llm is None:
            return False
        if not self.local_llm.is_available():
            return False
        return metric_name.lower() in self.LLM_BASED_METRICS


    def route_evaluation(
        self,
        metric_name: str,
        force_local: bool = False,
        force_cloud: bool = False,
    ) -> RoutingMode:
        """Determine the execution mode for a metric.

        Args:
            metric_name: The name of the metric.
            force_local: Force local execution.
            force_cloud: Force cloud execution.

        Returns:
            The recommended execution mode.
        """
        from fi.evals.local.evaluator import (RoutingMode, can_run_locally)
        if force_cloud and not self.offline_mode:
            return RoutingMode.CLOUD
        if force_local:
            return RoutingMode.LOCAL

        # Check if it's a heuristic metric that can run locally
        if can_run_locally(metric_name):
            return RoutingMode.LOCAL

        # Check if it's an LLM metric and we have local LLM
        if self.can_use_local_llm(metric_name) and self.prefer_local:
            return RoutingMode.LOCAL

        # Default to cloud unless in offline mode
        if self.offline_mode:
            raise ValueError(
                f"Metric '{metric_name}' requires cloud execution but offline_mode is enabled"
            )
        return RoutingMode.CLOUD


    def partition_evaluations(
        self, evaluations: List[Dict[str, Any]]
    ) -> Dict[RoutingMode, List[Dict[str, Any]]]:
        """Partition evaluations by execution mode.

        Args:
            evaluations: List of evaluation specifications.

        Returns:
            Dictionary mapping execution modes to their evaluations.
        """
        from fi.evals.local.evaluator import (Any, Dict, List, RoutingMode, logger)
        partitions: Dict[RoutingMode, List[Dict[str, Any]]] = {
            RoutingMode.LOCAL: [],
            RoutingMode.CLOUD: [],
        }

        for eval_spec in evaluations:
            metric_name = eval_spec.get("metric_name", "")
            force_local = eval_spec.get("force_local", False)
            force_cloud = eval_spec.get("force_cloud", False)

            try:
                mode = self.route_evaluation(metric_name, force_local, force_cloud)
                partitions[mode].append(eval_spec)
            except ValueError as e:
                # Offline mode violation - add to errors
                logger.error(f"Routing error for {metric_name}: {e}")
                partitions[RoutingMode.CLOUD].append(eval_spec)

        return partitions


    def evaluate_local_partition(
        self, evaluations: List[Dict[str, Any]]
    ) -> LocalEvaluationResult:
        """Evaluate the local partition of evaluations.

        This handles both heuristic metrics (via LocalEvaluator) and
        LLM-based metrics (via local LLM).

        Args:
            evaluations: List of evaluation specifications to run locally.

        Returns:
            LocalEvaluationResult with results.
        """
        from fi.evals.local.evaluator import (
            Any, Dict, List, LocalEvaluationResult, can_run_locally,
        )
        heuristic_evals = []
        llm_evals = []

        # Separate heuristic and LLM evaluations
        for eval_spec in evaluations:
            metric_name = eval_spec.get("metric_name", "")
            if can_run_locally(metric_name):
                heuristic_evals.append(eval_spec)
            elif self.can_use_local_llm(metric_name):
                llm_evals.append(eval_spec)
            else:
                heuristic_evals.append(eval_spec)  # Will be skipped

        # Run heuristic evaluations
        result = self.local_evaluator.evaluate_batch(heuristic_evals)

        # Run LLM evaluations if we have a local LLM
        if llm_evals and self.local_llm:
            llm_results = self._evaluate_with_local_llm(llm_evals)
            result.results.eval_results.extend(llm_results.results.eval_results)
            result.executed_locally.update(llm_results.executed_locally)
            result.skipped.update(llm_results.skipped)
            result.errors.update(llm_results.errors)

        return result


    def _evaluate_with_local_llm(
        self, evaluations: List[Dict[str, Any]]
    ) -> LocalEvaluationResult:
        """Run evaluations using the local LLM.

        Args:
            evaluations: List of LLM-based evaluation specifications.

        Returns:
            LocalEvaluationResult with LLM evaluation results.
        """
        from fi.evals.local.evaluator import (
            Any, BatchRunResult, Dict, EvalResult, List, LocalEvaluationResult, time,
        )
        result = LocalEvaluationResult(results=BatchRunResult(eval_results=[]))

        if not self.local_llm:
            for eval_spec in evaluations:
                metric_name = eval_spec.get("metric_name", "")
                result.skipped.add(metric_name)
                for _ in eval_spec.get("inputs", []):
                    result.results.eval_results.append(
                        EvalResult(
                            name=metric_name,
                            output=None,
                            reason="No local LLM configured",
                            runtime=0,
                        )
                    )
            return result

        for eval_spec in evaluations:
            metric_name = eval_spec.get("metric_name", "")
            inputs = eval_spec.get("inputs", [])
            config = eval_spec.get("config", {})

            for input_data in inputs:
                start_time = time.time()
                try:
                    # Build evaluation from input
                    judge_result = self.local_llm.judge(
                        query=input_data.get("input", input_data.get("query", "")),
                        response=input_data.get("response", input_data.get("output", "")),
                        criteria=config.get("criteria", f"Evaluate based on {metric_name}"),
                        context=input_data.get("context", input_data.get("contexts", "")),
                    )

                    runtime = int((time.time() - start_time) * 1000)
                    result.results.eval_results.append(
                        EvalResult(
                            name=metric_name,
                            output=judge_result.get("score", 0.0),
                            reason=judge_result.get("reason", ""),
                            runtime=runtime,
                            metrics=[{
                                "name": metric_name,
                                "value": judge_result.get("score", 0.0),
                            }],
                        )
                    )
                    result.executed_locally.add(metric_name)

                except Exception as e:
                    runtime = int((time.time() - start_time) * 1000)
                    result.errors[metric_name] = str(e)
                    result.results.eval_results.append(
                        EvalResult(
                            name=metric_name,
                            output=0.0,
                            reason=f"Local LLM error: {str(e)}",
                            runtime=runtime,
                        )
                    )

        return result


    def evaluate(
        self,
        template: str,
        inputs: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> LocalEvaluationResult:
        """Evaluate a single template with automatic routing.

        Args:
            template: The evaluation template/metric name.
            inputs: List of input dictionaries.
            config: Optional configuration for the evaluation.

        Returns:
            LocalEvaluationResult with evaluation results.
        """
        from fi.evals.local.evaluator import (
            Any, Dict, List, LocalEvaluationResult, Optional, RoutingMode,
        )
        eval_spec = {
            "metric_name": template,
            "inputs": inputs,
            "config": config or {},
        }

        mode = self.route_evaluation(template)

        if mode == RoutingMode.LOCAL:
            result = self.evaluate_local_partition([eval_spec])
        else:
            result = self._evaluate_cloud([eval_spec])

        # Automatically enrich current span with evaluation results
        try:
            from fi.evals.otel.enrichment import enrich_span_with_batch_result, is_auto_enrichment_enabled
            if is_auto_enrichment_enabled():
                enrich_span_with_batch_result(result.results)
        except ImportError:
            pass
        except Exception:
            pass

        return result
