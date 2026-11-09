"""Typed function parameters must retain their contract in generated tools."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, Union

import httpx
import jsonschema
import pytest

from fi.gateway import AgentCC, function_to_dict


def lookup(
    ids: list[int], limit: Optional[int] = None, mode: Literal["fast", "full"] = "fast"
):
    """Look up identifiers with optional pagination."""
    return ids


def parameter_schema(annotation):
    def tool(value):
        return value

    tool.__annotations__ = {"value": annotation}
    return function_to_dict(tool)["function"]["parameters"]["properties"]["value"]


def test_lookup_preserves_typed_parameters():
    tool = function_to_dict(lookup)
    assert tool == {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": "Look up identifiers with optional pagination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ids": {"type": "array", "items": {"type": "integer"}},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "mode": {"type": "string", "enum": ["fast", "full"]},
                },
                "required": ["ids"],
            },
        },
    }


@pytest.mark.parametrize(
    "arguments",
    [
        {"ids": [1, 2], "limit": 3, "mode": "fast"},
        {"ids": [], "limit": None, "mode": "full"},
        {"ids": [1]},
    ],
)
def test_lookup_accepts_valid_arguments(arguments):
    jsonschema.validate(arguments, function_to_dict(lookup)["function"]["parameters"])


@pytest.mark.parametrize(
    "arguments",
    [
        {"ids": "not an array", "limit": "not a number", "mode": "not a valid mode"},
        {"ids": ["1"], "limit": 3, "mode": "fast"},
        {"ids": [1], "limit": "3", "mode": "fast"},
        {"ids": [1], "limit": 3, "mode": "unknown"},
        {"ids": [True]},
        {"limit": 3, "mode": "fast"},
    ],
)
def test_lookup_rejects_invalid_arguments(arguments):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(arguments, function_to_dict(lookup)["function"]["parameters"])


def test_chat_sends_typed_tool_schema():
    captured = []

    def send(request):
        captured.append(json.loads(request.content)["tools"][0])
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-synthetic",
                "object": "chat.completion",
                "created": 0,
                "model": "synthetic-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "ok"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    tool = function_to_dict(lookup)
    with httpx.Client(transport=httpx.MockTransport(send)) as http:
        with AgentCC(
            api_key="synthetic-tool-schema-key",
            base_url="https://gateway.example.invalid/v1",
            http_client=http,
        ) as client:
            client.chat.completions.create(
                model="synthetic-model",
                messages=[{"role": "user", "content": "Look up identifiers."}],
                tools=[tool],
            )

    assert captured == [tool]
    schema = captured[0]["function"]["parameters"]
    jsonschema.validate({"ids": [1, 2], "limit": 3, "mode": "fast"}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"ids": "wrong", "limit": "wrong", "mode": "wrong"}, schema)


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        (list[int], {"type": "array", "items": {"type": "integer"}}),
        (List[str], {"type": "array", "items": {"type": "string"}}),
        (dict[str, int], {"type": "object", "additionalProperties": {"type": "integer"}}),
        (Dict[str, bool], {"type": "object", "additionalProperties": {"type": "boolean"}}),
        (Optional[int], {"anyOf": [{"type": "integer"}, {"type": "null"}]}),
        (int | None, {"anyOf": [{"type": "integer"}, {"type": "null"}]}),
        (Union[int, str], {"anyOf": [{"type": "integer"}, {"type": "string"}]}),
        (int | str, {"anyOf": [{"type": "integer"}, {"type": "string"}]}),
        (Literal["fast", "full"], {"type": "string", "enum": ["fast", "full"]}),
        (Literal[1, 2], {"type": "integer", "enum": [1, 2]}),
        (Literal[True, False], {"type": "boolean", "enum": [True, False]}),
        (Literal[None], {"type": "null", "enum": [None]}),
        (Literal["auto", 1, None], {"enum": ["auto", 1, None]}),
        (type(None), {"type": "null"}),
        (Any, {}),
        (list[Any], {"type": "array", "items": {}}),
        (dict[str, Any], {"type": "object", "additionalProperties": {}}),
        (str, {"type": "string"}),
        (int, {"type": "integer"}),
        (float, {"type": "number"}),
        (bool, {"type": "boolean"}),
        (list, {"type": "array"}),
        (dict, {"type": "object"}),
        (List, {"type": "array"}),
        (Dict, {"type": "object"}),
    ],
)
def test_annotation_schema(annotation, expected):
    schema = parameter_schema(annotation)
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema == expected


def test_nested_collections_and_unions_validate_recursively():
    schema = parameter_schema(dict[str, list[Optional[Literal["fast", "full"]]]])
    assert schema == {
        "type": "object",
        "additionalProperties": {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string", "enum": ["fast", "full"]},
                    {"type": "null"},
                ]
            },
        },
    }
    jsonschema.validate({"modes": ["fast", None, "full"]}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"modes": ["unknown"]}, schema)


def test_nullable_parameter_without_default_is_still_required():
    def tool(value: Optional[int]):
        return value

    schema = function_to_dict(tool)["function"]["parameters"]
    assert schema["required"] == ["value"]
    jsonschema.validate({"value": None}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({}, schema)


def test_unannotated_parameters_keep_string_default():
    def tool(value="default"):
        return value

    assert function_to_dict(tool)["function"]["parameters"] == {
        "type": "object",
        "properties": {"value": {"type": "string"}},
    }


class Unsupported:
    pass


@pytest.mark.parametrize(
    "annotation",
    [Unsupported, set[int], tuple[int, str], dict[int, str], list[Unsupported]],
)
def test_unsupported_annotations_raise_instead_of_becoming_strings(annotation):
    with pytest.raises(TypeError, match="Unsupported.*annotation"):
        parameter_schema(annotation)
