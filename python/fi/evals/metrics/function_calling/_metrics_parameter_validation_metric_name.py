"""ParameterValidation metric name operations."""
from __future__ import annotations

from fi.evals.metrics.function_calling.metrics import (Any, Dict, FunctionCallInput)


class _ParameterValidationMetricNameMethods:
    __slots__ = ()

    @property
    def metric_name(self) -> str:
        return "parameter_validation"


    def compute_one(self, inputs: FunctionCallInput) -> Dict[str, Any]:
        from fi.evals.metrics.function_calling.metrics import (
            Any, Dict, FunctionCallInput, _parse_function_call,
        )
        actual = _parse_function_call(inputs.response)

        if actual is None:
            return {
                "output": 0.0,
                "reason": "Could not parse function call from response."
            }

        if not inputs.function_definitions:
            return {
                "output": 0.0,
                "reason": "No function definitions provided for validation."
            }

        # Find the matching function definition
        func_def = None
        for fd in inputs.function_definitions:
            if fd.name == actual.name:
                func_def = fd
                break

        if func_def is None:
            return {
                "output": 0.0,
                "reason": f"Function '{actual.name}' not found in definitions."
            }

        errors = []
        total_checks = 0
        passed_checks = 0

        for param_spec in func_def.parameters:
            total_checks += 1

            # Check required parameters
            if param_spec.required and param_spec.name not in actual.arguments:
                errors.append(f"Missing required parameter: {param_spec.name}")
                continue

            if param_spec.name in actual.arguments:
                value = actual.arguments[param_spec.name]

                # Type checking
                if not self._check_type(value, param_spec.type, inputs.strict_type_check):
                    errors.append(
                        f"Parameter '{param_spec.name}' has wrong type: "
                        f"expected {param_spec.type}, got {type(value).__name__}"
                    )
                    continue

                # Enum checking
                if param_spec.enum and value not in param_spec.enum:
                    errors.append(
                        f"Parameter '{param_spec.name}' value '{value}' not in allowed values: {param_spec.enum}"
                    )
                    continue

                passed_checks += 1
            else:
                # Optional parameter not provided - that's fine
                passed_checks += 1

        # Check for extra parameters
        if not inputs.ignore_extra_params:
            expected_params = {p.name for p in func_def.parameters}
            extra_params = set(actual.arguments.keys()) - expected_params
            if extra_params:
                total_checks += len(extra_params)
                errors.append(f"Unexpected parameters: {', '.join(extra_params)}")

        if total_checks == 0:
            return {"output": 1.0, "reason": "No parameters to validate."}

        score = passed_checks / total_checks if total_checks > 0 else 1.0

        if errors:
            return {
                "output": round(score, 4),
                "reason": "; ".join(errors)
            }

        return {
            "output": 1.0,
            "reason": f"All {total_checks} parameter checks passed."
        }


    def _check_type(self, value: Any, expected_type: str, strict: bool) -> bool:
        """Check if a value matches the expected type."""
        from fi.evals.metrics.function_calling.metrics import (Any)
        type_map = {
            "string": (str,),
            "integer": (int,) if strict else (int, float),
            "number": (int, float),
            "boolean": (bool,),
            "array": (list,),
            "object": (dict,),
            "null": (type(None),),
        }

        expected_types = type_map.get(expected_type.lower(), (str,))

        # Special case: strict integer check
        if expected_type.lower() == "integer" and strict:
            return isinstance(value, int) and not isinstance(value, bool)

        # Boolean should not match int in Python
        if isinstance(value, bool) and expected_type.lower() != "boolean":
            return False

        return isinstance(value, expected_types)
