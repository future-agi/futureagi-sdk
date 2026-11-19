"""
Function Calling Evaluation Metrics.

AST-based, deterministic evaluation of LLM function calling.
Provides sub-10ms evaluation latency without LLM-as-judge dependency.
"""

import ast
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..base_metric import BaseMetric
from .types import FunctionCallInput, FunctionCall, FunctionDefinition, ParameterSpec


def _parse_function_call(call: Union[FunctionCall, Dict, str, None]) -> Optional[FunctionCall]:
    """Parse various input formats into a FunctionCall object."""
    if call is None:
        return None
    if isinstance(call, FunctionCall):
        return call
    if isinstance(call, dict):
        # Get arguments, handling both dict and JSON string formats (OpenAI-style)
        arguments = call.get("arguments", call.get("parameters", call.get("input", {})))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        return FunctionCall(
            name=call.get("name", call.get("function", "")),
            arguments=arguments if isinstance(arguments, dict) else {}
        )
    if isinstance(call, str):
        try:
            parsed = json.loads(call)
            return _parse_function_call(parsed)
        except json.JSONDecodeError:
            # Try to parse as Python AST (e.g., "get_weather(city='NYC')")
            return _parse_ast_call(call)
    return None


def _parse_ast_call(call_str: str) -> Optional[FunctionCall]:
    """Parse a function call string using AST."""
    try:
        # Wrap in expression for parsing
        tree = ast.parse(call_str.strip(), mode='eval')
        if isinstance(tree.body, ast.Call):
            call_node = tree.body
            func_name = ""
            if isinstance(call_node.func, ast.Name):
                func_name = call_node.func.id
            elif isinstance(call_node.func, ast.Attribute):
                func_name = call_node.func.attr

            # Extract arguments
            arguments = {}

            # Handle positional arguments
            for i, arg in enumerate(call_node.args):
                arguments[f"__positional_{i}"] = _ast_to_value(arg)

            # Handle keyword arguments
            for kw in call_node.keywords:
                if kw.arg:
                    arguments[kw.arg] = _ast_to_value(kw.value)

            return FunctionCall(name=func_name, arguments=arguments)
    except (SyntaxError, ValueError):
        pass
    return None


def _ast_to_value(node: ast.expr) -> Any:
    """Convert an AST node to a Python value."""
    # ast.Constant handles strings, numbers, booleans, None in Python 3.8+
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_ast_to_value(elt) for elt in node.elts]
    if isinstance(node, ast.Dict):
        return {
            _ast_to_value(k): _ast_to_value(v)
            for k, v in zip(node.keys, node.values)
            if k is not None
        }
    if isinstance(node, ast.Name):
        # Handle True, False, None as names (fallback)
        if node.id == "True":
            return True
        elif node.id == "False":
            return False
        elif node.id == "None":
            return None
        return node.id
    if isinstance(node, ast.Tuple):
        return tuple(_ast_to_value(elt) for elt in node.elts)
    if isinstance(node, ast.Set):
        return {_ast_to_value(elt) for elt in node.elts}
    return str(node)


def _parse_function_calls(
    calls: Union[FunctionCall, List[FunctionCall], Dict, str, List[Dict], None]
) -> List[FunctionCall]:
    """Parse various input formats into a list of FunctionCall objects."""
    if calls is None:
        return []
    if isinstance(calls, list):
        return [_parse_function_call(c) for c in calls if _parse_function_call(c)]
    parsed = _parse_function_call(calls)
    return [parsed] if parsed else []


def _types_compatible(actual: Any, expected: Any, strict: bool = False) -> bool:
    """Check if types are compatible."""
    if strict:
        return type(actual) == type(expected)

    # Flexible type checking
    if actual is None or expected is None:
        return actual == expected

    # Bool guard: bool is a subclass of int in Python, so must check before numeric
    if isinstance(actual, bool) or isinstance(expected, bool):
        return isinstance(actual, bool) and isinstance(expected, bool)

    # Numeric compatibility (int/float)
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return True

    # String compatibility
    if isinstance(actual, str) and isinstance(expected, str):
        return True

    # List compatibility
    if isinstance(actual, list) and isinstance(expected, list):
        return True

    # Dict compatibility
    if isinstance(actual, dict) and isinstance(expected, dict):
        return True

    return type(actual) == type(expected)


def _values_equal(actual: Any, expected: Any, strict_type: bool = False) -> bool:
    """Check if values are equal with optional type flexibility."""
    if not _types_compatible(actual, expected, strict_type):
        return False

    # For numeric types, allow float/int comparison
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return float(actual) == float(expected)

    # For strings, exact match (case-sensitive)
    if isinstance(actual, str) and isinstance(expected, str):
        return actual == expected

    # For lists, recursive comparison
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return False
        return all(_values_equal(a, e, strict_type) for a, e in zip(actual, expected))

    # For dicts, recursive comparison
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual.keys()) != set(expected.keys()):
            return False
        return all(
            _values_equal(actual[k], expected[k], strict_type)
            for k in expected.keys()
        )

    return actual == expected


class FunctionNameMatch(BaseMetric[FunctionCallInput]):
    """
    Evaluates if the function name matches the expected name.

    Returns 1.0 if names match, 0.0 otherwise.
    Fast, deterministic metric (~1ms).
    """

    @property
    def metric_name(self) -> str:
        return "function_name_match"

    def compute_one(self, inputs: FunctionCallInput) -> Dict[str, Any]:
        actual = _parse_function_call(inputs.response)
        expected = _parse_function_call(inputs.expected_response)

        if actual is None:
            return {
                "output": 0.0,
                "reason": "Could not parse actual function call from response."
            }

        if expected is None:
            return {
                "output": 0.0,
                "reason": "Could not parse expected function call. 'expected_response' is required."
            }

        if actual.name == expected.name:
            return {
                "output": 1.0,
                "reason": f"Function name '{actual.name}' matches expected."
            }

        return {
            "output": 0.0,
            "reason": f"Function name mismatch: got '{actual.name}', expected '{expected.name}'."
        }


from ._metrics_parameter_validation_metric_name import _ParameterValidationMetricNameMethods

class ParameterValidation(_ParameterValidationMetricNameMethods, BaseMetric[FunctionCallInput]):
    """
    Validates function call parameters against a schema.

    Checks:
    - Required parameters are present
    - Parameter types match specification
    - Enum constraints are satisfied

    Returns score from 0.0 to 1.0 based on validation success.
    """


from ._metrics_function_call_accuracy_metric_name import _FunctionCallAccuracyMetricNameMethods

class FunctionCallAccuracy(_FunctionCallAccuracyMetricNameMethods, BaseMetric[FunctionCallInput]):
    """
    Comprehensive function call accuracy evaluation.

    Evaluates:
    - Function name match (weighted 40%)
    - Parameter presence (weighted 30%)
    - Parameter value accuracy (weighted 30%)

    Returns overall score from 0.0 to 1.0.
    """


    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.name_weight = self.config.get("name_weight", 0.4)
        self.presence_weight = self.config.get("presence_weight", 0.3)
        self.value_weight = self.config.get("value_weight", 0.3)


from ._metrics_function_call_exact_match_metric_name import _FunctionCallExactMatchMetricNameMethods

class FunctionCallExactMatch(
    _FunctionCallExactMatchMetricNameMethods,
    BaseMetric[FunctionCallInput],
):
    """
    AST-based exact match evaluation.

    Parses function calls as AST and compares structure.
    Useful for evaluating code-style function calls.

    Returns 1.0 for exact match, 0.0 otherwise.
    """
