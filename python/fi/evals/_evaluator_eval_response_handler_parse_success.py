"""EvalResponseHandler parse success operations."""
from __future__ import annotations

from fi.evals.evaluator import (Any, BatchRunResult, Dict, Response)


class _EvalResponseHandlerParseSuccessMethods:
    __slots__ = ()

    @classmethod
    def _parse_success(cls, response: Response) -> BatchRunResult:
        from fi.evals.evaluator import (BatchRunResult, Response)
        return cls.convert_to_batch_results(response.json())


    @classmethod
    def _handle_error(cls, response: Response) -> None:
        from fi.evals.evaluator import (InvalidAuthError, Response)
        if response.status_code == 400:
            raise Exception(
                f"Evaluation failed with a 400 Bad Request. Please check your input data and evaluation configuration. Response: {response.text}"
            )
        elif response.status_code == 403:
            raise InvalidAuthError()
        else:
            raise Exception(
                f"Error in evaluation: {response.status_code}, response: {response.text}"
            )


    @classmethod
    def convert_to_batch_results(cls, response: Dict[str, Any]) -> BatchRunResult:
        """
        Convert API response to BatchRunResult

        Args:
            response: Raw API response dictionary

        Returns:
            BatchRunResult containing evaluation results
        """
        from fi.evals.evaluator import (Any, BatchRunResult, Dict, EvalResult)
        eval_results = []

        # The revamped backend (post 2026-04-12) returns pure snake_case:
        #   {"result": [{"evaluations": [
        #       {"name", "reason", "runtime", "output", "output_type",
        #        "eval_id", "model"?, "error_localizer_enabled"?,
        #        "error_localizer"?}
        #   ]}]}
        # Async / error-localization paths may return the eval wrapped in
        # {"eval_status": "...", "result": <eval>} — handle that too.
        for result in response.get("result", []) or []:
            if isinstance(result, dict) and "evaluations" in result:
                entries = result.get("evaluations", []) or []
            else:
                entries = [result] if isinstance(result, dict) else []

            for evaluation in entries:
                if not isinstance(evaluation, dict):
                    continue
                eval_results.append(
                    EvalResult(
                        name=evaluation.get("name", ""),
                        output=evaluation.get("output", evaluation.get("value")),
                        reason=evaluation.get("reason", ""),
                        runtime=evaluation.get("runtime", 0),
                        output_type=evaluation.get("output_type", ""),
                        eval_id=evaluation.get("eval_id", ""),
                        model=evaluation.get("model"),
                        error_localizer_enabled=evaluation.get(
                            "error_localizer_enabled"
                        ),
                        error_localizer=evaluation.get("error_localizer"),
                    )
                )

        return BatchRunResult(eval_results=eval_results)
