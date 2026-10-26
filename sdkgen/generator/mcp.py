"""MCP emitter: the tool manifest, in the same shape the monorepo's MCP server consumes."""

from __future__ import annotations

import json

from .catalog import Op


def json_schema(spec: dict, schema: dict) -> dict:
    """Swagger 2.0 schema -> JSON Schema (x-nullable -> null union), refs inlined one level as objects."""
    schema = dict(schema)
    nullable = schema.pop("x-nullable", False)
    if "$ref" in schema:
        schema = {"type": "object"}
    schema.pop("title", None)
    if schema.get("type") == "array" and "items" in schema:
        schema["items"] = json_schema(spec, schema["items"])
    if nullable and "type" in schema:
        schema["type"] = [schema["type"], "null"]
    return schema


def _tool(spec: dict, op: Op) -> dict:
    mcp = op.surfaces["mcp"]
    props, required = {}, []
    for p in op.params:
        props[p.name] = json_schema(spec, p.schema)
        if p.description:
            props[p.name]["description"] = p.description
        if p.name in mcp.get("max_page_size", {}):
            props[p.name]["maximum"] = min(mcp["max_page_size"][p.name], props[p.name].get("maximum", float("inf")))
        if p.required:
            required.append(p.name)
    return {
        "name": mcp["name"],
        "description": op.description,
        "group": mcp["group"],
        "stability": mcp["stability"],
        "inputSchema": {"type": "object", "properties": props, "required": required, "additionalProperties": False},
        "annotations": {
            "readOnlyHint": mcp["access"] == "read",
            "destructiveHint": mcp["access"] == "destructive",
            "idempotentHint": op.method in ("GET", "PUT", "DELETE"),
            "openWorldHint": bool(mcp.get("open_world")),
        },
        "request": {
            "method": op.method,
            "path": op.path,
            "parameters": {loc: [p.name for p in op.params if p.location == loc] for loc in ("path", "query", "body")},
        },
        "response": {"unwrap": op.unwrap},
        "source": {"catalogId": op.id, "operationId": op.operation_id},
    }


def emit_mcp(spec: dict, ops: list[Op], contract_sha: str) -> str:
    tools = [_tool(spec, op) for op in ops if "mcp" in op.surfaces]
    manifest = {"schema_version": 1, "source_contract_sha256": contract_sha, "tool_count": len(tools), "tools": tools}
    return json.dumps(manifest, indent=2) + "\n"
