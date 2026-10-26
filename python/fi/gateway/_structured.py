"""Structured output helpers -- convert Pydantic models to OpenAI response_format dicts."""

from __future__ import annotations

import json
from typing import Any


def to_response_format(model_class: type) -> dict[str, Any]:
    """Convert a Pydantic model class to an OpenAI ``response_format`` dict.

    Usage::

        from pydantic import BaseModel

        class Event(BaseModel):
            name: str
            date: str

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[...],
            response_format=agentcc.to_response_format(Event),
        )

    Returns:
        A dict of the form::

            {
                "type": "json_schema",
                "json_schema": {
                    "name": "Event",
                    "schema": { ... },
                    "strict": True,
                },
            }

    Raises:
        TypeError: If *model_class* is not a Pydantic model class.
    """
    if hasattr(model_class, "model_json_schema"):
        schema = model_class.model_json_schema()
    else:
        raise TypeError(f"Expected a Pydantic model class, got {type(model_class)}")

    return {
        "type": "json_schema",
        "json_schema": {
            "name": model_class.__name__,
            "schema": schema,
            "strict": True,
        },
    }


def validate_json_response(response_text: str, schema: dict[str, Any]) -> bool:
    """Validate a JSON response against a JSON Schema.

    Args:
        response_text: Raw JSON string from an LLM response.
        schema: JSON Schema dict to validate against.

    Returns:
        ``True`` if the response is valid JSON matching the schema, ``False`` otherwise.

    Raises:
        ImportError: If ``jsonschema`` is not installed.
    """
    try:
        import jsonschema
    except ImportError:
        raise ImportError(
            "jsonschema is required for JSON validation. "
            "Install with: pip install agentcc[validation]"
        ) from None
    try:
        data = json.loads(response_text)
        jsonschema.validate(data, schema)
        return True
    except (json.JSONDecodeError, jsonschema.ValidationError):
        return False
