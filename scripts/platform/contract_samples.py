"""Deterministic schema-shaped inputs for public-wrapper transport contracts."""
from __future__ import annotations

import copy

UUID = "00000000-0000-4000-8000-000000000001"


def sample(doc, schema, seen=(), *, direction=None):
    if not isinstance(schema, dict):
        return None
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"non-local sample reference: {ref}")
        if ref in seen:
            return None
        node = doc
        for part in ref[2:].split("/"):
            node = node[part.replace("~1", "/").replace("~0", "~")]
        return sample(doc, node, (*seen, ref), direction=direction)
    for key in ("example", "default", "const"):
        if key in schema:
            return copy.deepcopy(schema[key])
    if schema.get("enum"):
        return schema["enum"][0]
    for key in ("oneOf", "anyOf"):
        if schema.get(key):
            return sample(doc, schema[key][0], seen, direction=direction)
    if schema.get("allOf"):
        values = [sample(doc, part, seen, direction=direction) for part in schema["allOf"]]
        result = {}
        for value in values:
            if isinstance(value, dict):
                result.update(value)
            elif value is not None:
                # allOf also composes scalar schemas, not only object inheritance.
                return value
        return result
    kind = schema.get("type", "object")
    if kind == "object":
        properties = schema.get("properties", {})
        excluded = {"request": "readOnly", "response": "writeOnly"}.get(direction)
        return {k: sample(doc, properties[k], seen, direction=direction)
                for k in schema.get("required", []) if k in properties
                and not (excluded and resolve(doc, properties[k]).get(excluded))}
    if kind == "array":
        return [sample(doc, schema.get("items", {}), seen, direction=direction)] * max(1, schema.get("minItems", 0))
    if kind in ("integer", "number"):
        return max(1, schema.get("minimum", 1))
    if kind == "boolean":
        return True
    if kind == "null":
        return None
    return {"uuid": UUID, "date-time": "2026-01-01T00:00:00+00:00", "date": "2026-01-01",
            "email": "fixture@example.invalid", "uri": "http://127.0.0.1:9/fixture"}.get(schema.get("format"), "fixture")


def resolve(doc, value):
    seen = set()
    while "$ref" in value:
        ref = value["$ref"]
        if not ref.startswith("#/") or ref in seen:
            raise ValueError(f"unsupported sample reference: {ref}")
        seen.add(ref)
        value = doc
        for part in ref[2:].split("/"):
            value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def payload(doc, node, *, direction=None):
    node = resolve(doc, node)
    if "schema" in node:
        return sample(doc, node["schema"], direction=direction)
    content = node.get("content", {})
    media = content.get("application/json", next(iter(content.values()), {}))
    return sample(doc, media["schema"], direction=direction) if "schema" in media else {}


def examples(doc, op):
    body = op.get("requestBody", {})
    if not body:
        body = next((p for p in op.get("parameters", []) if p.get("in") == "body"), {})
    response = next((v for k, v in op.get("responses", {}).items() if str(k).startswith("2")), {})
    query, path_values = {}, {}
    for parameter in op.get("parameters", []):
        parameter = resolve(doc, parameter)
        schema = parameter.get("schema", parameter)
        if parameter.get("in") == "query" and parameter.get("required"):
            query[parameter["name"]] = sample(doc, schema)
        if parameter.get("in") == "path" and schema.get("type") in ("integer", "number"):
            path_values[parameter["name"]] = sample(doc, schema)
    return {"request_example": payload(doc, body, direction="request"),
            "response_example": payload(doc, response, direction="response"),
            "query_example": query, "path_values": path_values}
