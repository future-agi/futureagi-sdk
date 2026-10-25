"""Utility for converting Python functions to OpenAI-compatible tool schemas."""

from __future__ import annotations

import inspect
from typing import Any, Callable, get_type_hints

# Mapping of Python types to JSON Schema types.
_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _python_type_to_json_schema(annotation: Any) -> dict[str, Any]:
    """Convert a Python type annotation to a JSON Schema type descriptor."""
    if annotation is inspect.Parameter.empty or annotation is Any:
        return {"type": "string"}

    json_type = _TYPE_MAP.get(annotation)
    if json_type is not None:
        return {"type": json_type}

    # Fallback for unrecognised types
    return {"type": "string"}


def function_to_dict(func: Callable[..., Any]) -> dict[str, Any]:
    """Convert a Python function to an OpenAI function-calling tool schema.

    Inspects the function's signature, type annotations, and docstring
    to build a valid OpenAI tools entry.

    Returns:
        Dict matching OpenAI's tool schema:
        {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
    """
    sig = inspect.signature(func)

    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        annotation = hints.get(name, param.annotation)
        properties[name] = _python_type_to_json_schema(annotation)

        # Parameters without a default value are required.
        if param.default is inspect.Parameter.empty:
            required.append(name)

    parameters: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        parameters["required"] = required

    description = inspect.getdoc(func) or ""

    function_def: dict[str, Any] = {
        "name": func.__name__,
        "parameters": parameters,
    }
    if description:
        function_def["description"] = description

    return {
        "type": "function",
        "function": function_def,
    }
