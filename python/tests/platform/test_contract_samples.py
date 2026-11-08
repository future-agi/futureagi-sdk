"""Contract examples support object and scalar composition without runtime tables."""
import pytest

from ._gates_support import load


@pytest.mark.parametrize("wrapped", [False, True])
def test_request_and_response_examples_respect_direction(wrapped):
    module = load("direction_samples", "scripts/platform/contract_samples.py")
    schema = {"type": "object", "required": ["name", "id", "secret"], "properties": {
        "name": {"type": "string"}, "id": {"type": "integer", "readOnly": True},
        "secret": {"type": "string", "writeOnly": True}}}
    doc = {"components": {"schemas": {"Value": schema}}}
    ref = {"$ref": "#/components/schemas/Value"}
    node = {"allOf": [{"type": "array", "items": ref}]} if wrapped else ref
    op = {"requestBody": {"content": {"application/json": {"schema": node}}},
          "responses": {"200": {"content": {"application/json": {"schema": node}}}}}
    examples = module.examples(doc, op)
    request, response = {"name": "fixture", "secret": "fixture"}, {"name": "fixture", "id": 1}
    assert examples["request_example"] == ([request] if wrapped else request)
    assert examples["response_example"] == ([response] if wrapped else response)


def test_allof_supports_annotated_objects_and_scalars():
    module = load("contract_sample_shapes", "scripts/platform/contract_samples.py")
    assert module.sample({}, {"allOf": [
        {"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]},
        {"description": "Additional documentation"}
    ]}) == {"value": 1}
    assert module.sample({}, {"allOf": [{"type": "string", "enum": ["ready"]}]}) == "ready"
