"""FunctionCallExactMatch metric name operations."""
from __future__ import annotations

from fi.evals.metrics.function_calling.metrics import (Any, Dict, FunctionCallInput)


class _FunctionCallExactMatchMetricNameMethods:
    __slots__ = ()

    @property
    def metric_name(self) -> str:
        return "function_call_exact_match"


    def compute_one(self, inputs: FunctionCallInput) -> Dict[str, Any]:
        from fi.evals.metrics.function_calling.metrics import (
            Any, Dict, FunctionCallInput, _parse_function_call, _values_equal,
        )
        actual = _parse_function_call(inputs.response)
        expected = _parse_function_call(inputs.expected_response)

        if actual is None:
            return {
                "output": 0.0,
                "reason": "Could not parse actual function call."
            }

        if expected is None:
            return {
                "output": 0.0,
                "reason": "Could not parse expected function call."
            }

        # Compare name
        if actual.name != expected.name:
            return {
                "output": 0.0,
                "reason": f"Function name mismatch: '{actual.name}' vs '{expected.name}'"
            }

        # Compare arguments
        if set(actual.arguments.keys()) != set(expected.arguments.keys()):
            missing = set(expected.arguments.keys()) - set(actual.arguments.keys())
            extra = set(actual.arguments.keys()) - set(expected.arguments.keys())
            parts = []
            if missing:
                parts.append(f"missing: {missing}")
            if extra and not inputs.ignore_extra_params:
                parts.append(f"extra: {extra}")
            if parts:
                return {
                    "output": 0.0,
                    "reason": f"Parameter mismatch: {', '.join(parts)}"
                }

        # Compare values
        for key, expected_value in expected.arguments.items():
            if key not in actual.arguments:
                continue
            actual_value = actual.arguments[key]
            if not _values_equal(actual_value, expected_value, inputs.strict_type_check):
                return {
                    "output": 0.0,
                    "reason": f"Value mismatch for '{key}': got {actual_value!r}, expected {expected_value!r}"
                }

        return {
            "output": 1.0,
            "reason": f"Function call matches: {actual.name}({', '.join(f'{k}={v!r}' for k, v in actual.arguments.items())})"
        }
