"""Utility for converting Python functions to OpenAI-compatible tool schemas."""

from __future__ import annotations

import inspect
from types import UnionType
from typing import Any, Callable, Literal, Union, get_args, get_origin, get_type_hints

# Mapping of Python types to JSON Schema types.
_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}


def _python_type_to_json_schema(annotation: Any) -> dict[str, Any]:
    """Convert a supported Python annotation without changing its argument type."""
    if annotation is inspect.Parameter.empty:
        return {"type": "string"}
    if annotation is Any:
        return {}

    json_type = _TYPE_MAP.get(annotation)
    if json_type is not None:
        return {"type": json_type}

    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is list:
        schema: dict[str, Any] = {"type": "array"}
        if args:
            schema["items"] = _python_type_to_json_schema(args[0])
        return schema
    if origin is dict:
        if not args:
            return {"type": "object"}
        if args[0] is str:
            return {
                "type": "object",
                "additionalProperties": _python_type_to_json_schema(args[1]),
            }
    if origin in (Union, UnionType):
        return {"anyOf": [_python_type_to_json_schema(arg) for arg in args]}
    if origin is Literal:
        value_types = {type(value) for value in args}
        if value_types and value_types <= {str, int, bool, type(None)}:
            schema = {"enum": list(args)}
            if len(value_types) == 1:
                schema["type"] = _TYPE_MAP[value_types.pop()]
            return schema

    raise TypeError(f"Unsupported tool parameter annotation: {annotation!r}")


def function_to_dict(func: Callable[..., Any]) -> dict[str, Any]:
    """Convert a Python function to an OpenAI function-calling tool schema.

    Inspects the function's signature, type annotations, and docstring
    to build a valid OpenAI tools entry. Supports primitives, lists,
    string-keyed dictionaries, unions (including optional types), and literals.
    Any is unconstrained; unannotated parameters retain the string default.

    Raises:
        TypeError: A parameter annotation cannot be represented by this converter.

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
