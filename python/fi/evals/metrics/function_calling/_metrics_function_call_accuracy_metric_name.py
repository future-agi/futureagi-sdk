"""FunctionCallAccuracy metric name operations."""
from __future__ import annotations

from fi.evals.metrics.function_calling.metrics import (
    Any, Dict, FunctionCall, FunctionCallInput, List,
)


class _FunctionCallAccuracyMetricNameMethods:
    __slots__ = ()

    @property
    def metric_name(self) -> str:
        return "function_call_accuracy"


    def compute_one(self, inputs: FunctionCallInput) -> Dict[str, Any]:
        from fi.evals.metrics.function_calling.metrics import (
            Any, Dict, FunctionCallInput, _parse_function_calls,
        )
        actual_calls = _parse_function_calls(inputs.response)
        expected_calls = _parse_function_calls(inputs.expected_response)

        if not actual_calls:
            return {
                "output": 0.0,
                "reason": "Could not parse any function calls from response."
            }

        if not expected_calls:
            return {
                "output": 0.0,
                "reason": "No expected function calls provided."
            }

        # Handle single vs multiple calls
        if len(expected_calls) == 1 and len(actual_calls) == 1:
            return self._evaluate_single(
                actual_calls[0], expected_calls[0], inputs
            )

        # Multiple calls - evaluate as set or sequence
        return self._evaluate_multiple(
            actual_calls, expected_calls, inputs
        )


    def _evaluate_single(
        self,
        actual: FunctionCall,
        expected: FunctionCall,
        inputs: FunctionCallInput
    ) -> Dict[str, Any]:
        """Evaluate a single function call pair."""
        from fi.evals.metrics.function_calling.metrics import (
            Any, Dict, FunctionCall, FunctionCallInput, _values_equal,
        )
        details = []

        # Name match (40%)
        name_score = 1.0 if actual.name == expected.name else 0.0
        details.append(f"name: {name_score:.0%}")

        # Parameter presence (30%)
        expected_params = set(expected.arguments.keys())
        actual_params = set(actual.arguments.keys())

        if expected_params:
            presence_score = len(expected_params & actual_params) / len(expected_params)
        else:
            presence_score = 1.0 if not actual_params or inputs.ignore_extra_params else 0.0

        details.append(f"params: {presence_score:.0%}")

        # Parameter values (30%)
        value_matches = 0
        value_total = len(expected.arguments)

        for param_name, expected_value in expected.arguments.items():
            if param_name in actual.arguments:
                actual_value = actual.arguments[param_name]
                if _values_equal(actual_value, expected_value, inputs.strict_type_check):
                    value_matches += 1

        value_score = value_matches / value_total if value_total > 0 else 1.0
        details.append(f"values: {value_score:.0%}")

        # Calculate weighted score
        total_score = (
            name_score * self.name_weight +
            presence_score * self.presence_weight +
            value_score * self.value_weight
        )

        return {
            "output": round(total_score, 4),
            "reason": f"Function call evaluation: {', '.join(details)}. Overall: {total_score:.1%}"
        }


    def _evaluate_multiple(
        self,
        actual_calls: List[FunctionCall],
        expected_calls: List[FunctionCall],
        inputs: FunctionCallInput
    ) -> Dict[str, Any]:
        """Evaluate multiple function calls (parallel calling)."""
        from fi.evals.metrics.function_calling.metrics import (
            Any, Dict, FunctionCall, FunctionCallInput, List,
        )
        if inputs.order_matters:
            # Sequence comparison
            if len(actual_calls) != len(expected_calls):
                return {
                    "output": 0.0,
                    "reason": f"Call count mismatch: got {len(actual_calls)}, expected {len(expected_calls)}"
                }

            scores = []
            for actual, expected in zip(actual_calls, expected_calls):
                result = self._evaluate_single(actual, expected, inputs)
                scores.append(result["output"])

            avg_score = sum(scores) / len(scores)
            return {
                "output": round(avg_score, 4),
                "reason": f"Sequence evaluation: {len(scores)} calls, avg score {avg_score:.1%}"
            }

        # Set comparison - find best match for each expected call
        matched_scores = []
        unmatched_expected = []

        for expected in expected_calls:
            best_score = 0.0
            for actual in actual_calls:
                result = self._evaluate_single(actual, expected, inputs)
                best_score = max(best_score, result["output"])

            if best_score > 0:
                matched_scores.append(best_score)
            else:
                unmatched_expected.append(expected.name)

        if not matched_scores:
            return {
                "output": 0.0,
                "reason": f"No expected calls matched. Expected: {[c.name for c in expected_calls]}"
            }

        # Penalize for missing calls
        coverage = len(matched_scores) / len(expected_calls)
        avg_match_score = sum(matched_scores) / len(matched_scores)
        final_score = coverage * avg_match_score

        reason = f"Matched {len(matched_scores)}/{len(expected_calls)} calls, avg accuracy {avg_match_score:.1%}"
        if unmatched_expected:
            reason += f". Missing: {unmatched_expected}"

        return {
            "output": round(final_score, 4),
            "reason": reason
        }
