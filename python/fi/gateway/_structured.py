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
            "schema": strict_schema(schema),
            "strict": True,
        },
    }


def _nullable(prop: dict[str, Any]) -> dict[str, Any]:
    """The property's schema, also accepting null."""
    if "anyOf" in prop:
        if any(isinstance(o, dict) and o.get("type") == "null" for o in prop["anyOf"]):
            return prop
        return {**prop, "anyOf": [*prop["anyOf"], {"type": "null"}]}
    if "$ref" in prop:
        rest = {k: v for k, v in prop.items() if k != "$ref"}
        return {"anyOf": [{"$ref": prop["$ref"]}, {"type": "null"}], **rest}
    kind = prop.get("type")
    if isinstance(kind, str) and kind != "null":
        return {**prop, "type": [kind, "null"]}
    if isinstance(kind, list) and "null" not in kind:
        return {**prop, "type": [*kind, "null"]}
    return prop


def strict_schema(schema: Any) -> Any:
    """A JSON Schema in the form OpenAI's strict structured output accepts.

    Pydantic's schema is not that form: strict mode needs ``additionalProperties: false`` on
    every object and every property listed in ``required``, and it rejects ``default``. A field
    Pydantic left optional (it has a default) stays optional for the caller by becoming
    nullable: the model may answer null where it has nothing to say. Nested models in
    ``$defs`` get the same treatment.
    """
    if isinstance(schema, list):
        return [strict_schema(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    out = {key: strict_schema(value) for key, value in schema.items() if key != "default"}
    props = out.get("properties")
    if isinstance(props, dict):
        required = set(out.get("required") or [])
        out["properties"] = {name: prop if name in required or not isinstance(prop, dict) else _nullable(prop) for name, prop in props.items()}
        out["required"] = list(out["properties"])
        out["additionalProperties"] = False
    return out


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
