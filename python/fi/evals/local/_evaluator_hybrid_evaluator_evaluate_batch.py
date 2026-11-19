"""HybridEvaluator evaluate batch operations."""
from __future__ import annotations

from fi.evals.local.evaluator import (Any, Dict, List, LocalEvaluationResult)


class _HybridEvaluatorEvaluateBatchMethods:
    __slots__ = ()

    def evaluate_batch(
        self,
        evaluations: List[Dict[str, Any]],
    ) -> LocalEvaluationResult:
        """Evaluate multiple templates with automatic routing.

        Args:
            evaluations: List of evaluation specifications.

        Returns:
            Combined LocalEvaluationResult from all evaluations.
        """
        from fi.evals.local.evaluator import (Any, Dict, List, LocalEvaluationResult, RoutingMode)
        partitions = self.partition_evaluations(evaluations)

        # Run local evaluations
        local_result = self.evaluate_local_partition(partitions[RoutingMode.LOCAL])

        # Run cloud evaluations
        if partitions[RoutingMode.CLOUD]:
            cloud_result = self._evaluate_cloud(partitions[RoutingMode.CLOUD])

            # Merge results
            local_result.results.eval_results.extend(cloud_result.results.eval_results)
            local_result.executed_locally.update(cloud_result.executed_locally)
            local_result.skipped.update(cloud_result.skipped)
            local_result.errors.update(cloud_result.errors)

        return local_result


    def _evaluate_cloud(
        self, evaluations: List[Dict[str, Any]]
    ) -> LocalEvaluationResult:
        """Run evaluations via cloud API.

        Args:
            evaluations: List of evaluation specifications for cloud.

        Returns:
            LocalEvaluationResult with cloud evaluation results.
        """
        from fi.evals.local.evaluator import (
            Any, BatchRunResult, Dict, EvalResult, List, LocalEvaluationResult, logger, time,
        )
        result = LocalEvaluationResult(results=BatchRunResult(eval_results=[]))

        if self.offline_mode:
            for eval_spec in evaluations:
                metric_name = eval_spec.get("metric_name", "")
                result.skipped.add(metric_name)
                for _ in eval_spec.get("inputs", []):
                    result.results.eval_results.append(
                        EvalResult(
                            name=metric_name,
                            output=None,
                            reason="Offline mode - cloud execution disabled",
                            runtime=0,
                        )
                    )
            return result

        if not self.cloud_evaluator:
            for eval_spec in evaluations:
                metric_name = eval_spec.get("metric_name", "")
                result.skipped.add(metric_name)
                for _ in eval_spec.get("inputs", []):
                    result.results.eval_results.append(
                        EvalResult(
                            name=metric_name,
                            output=None,
                            reason="No cloud evaluator configured",
                            runtime=0,
                        )
                    )
            return result

        # Route through fi.evals.evaluate() with Turing engine
        try:
            from fi.evals import evaluate as core_evaluate

            for eval_spec in evaluations:
                metric_name = eval_spec.get("metric_name", "")
                inputs_list = eval_spec.get("inputs", [])

                for input_data in inputs_list:
                    start_time = time.time()
                    try:
                        eval_result = core_evaluate(
                            metric_name,
                            engine="turing",
                            output=input_data.get("response", input_data.get("output", "")),
                            input=input_data.get("input", input_data.get("query", "")),
                            context=input_data.get("context", input_data.get("contexts", "")),
                        )

                        runtime = int((time.time() - start_time) * 1000)
                        result.results.eval_results.append(
                            EvalResult(
                                name=metric_name,
                                output=eval_result.score if hasattr(eval_result, "score") else eval_result.output,
                                reason=getattr(eval_result, "reason", ""),
                                runtime=runtime,
                                metrics=[{
                                    "name": metric_name,
                                    "value": eval_result.score if hasattr(eval_result, "score") else 0.0,
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
                                output=None,
                                reason=f"Cloud evaluation error: {e}",
                                runtime=runtime,
                            )
                        )

        except ImportError:
            logger.error("fi.evals.evaluate not available for cloud routing")
            for eval_spec in evaluations:
                metric_name = eval_spec.get("metric_name", "")
                result.skipped.add(metric_name)
                result.errors[metric_name] = "fi.evals.evaluate not available"
        except Exception as e:
            logger.error(f"Cloud evaluation failed: {e}")
            for eval_spec in evaluations:
                result.errors[eval_spec.get("metric_name", "")] = str(e)

        return result
