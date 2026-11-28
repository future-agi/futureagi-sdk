"""A product commit built from the committed contract, for the scoped sync and pair_check tests.

The product's OpenAPI is the committed slice without its x-contract-sources record; its MCP
manifest and tools.yaml are what the product generator would write for the scoped catalog
entries, plus one unscoped tool. Tests edit the returned objects to make the product drift.
Import after sdkgen is on sys.path (generator.catalog is loaded lazily)."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
CATALOG = yaml.safe_load((ROOT / "sdkgen/catalog/operations.yaml").read_text())
SPEC = json.loads((ROOT / "sdkgen/contracts/swagger.json").read_text())

EPOCH_TOOLS = {
    "get_debug_failures", "run_debug_failures", "list_evidence_imports", "create_evidence_import",
    "get_evidence_import", "draft_evidence_import", "add_evidence_import_cases", "discard_evidence_import",
    "get_epoch_launch_options", "list_epochs", "get_epoch", "launch_epoch", "stop_epoch", "retry_epoch",
    "get_epoch_candidate_patch", "make_epoch_candidate_default", "open_epoch_candidate_pull_request",
    "get_epoch_coding_agent_brief", "get_epoch_attempt_verdict",
}
# The SQL tools' MCP inputs, written out rather than derived, so the gate is checked against an
# independent statement of the product shape: (path, query, body, required).
SQL_PROJECTIONS = {
    "run_sql": ([], [], ["project_id", "sql", "start", "end", "reuse"], ["project_id", "sql", "start", "end"]),
    "get_sql_result": (["id"], ["project_id", "offset", "limit"], [], ["id", "project_id"]),
    "cancel_sql": (["id"], [], ["project_id"], ["id", "project_id"]),
    "get_sql_catalog": ([], ["project_id"], [], ["project_id"]),
}


def mcp_name(entry: dict) -> str | None:
    mapping = entry["surfaces"].get("mcp")
    return None if mapping in (None, False) else mapping.get("name") or entry["id"].replace(".", "_")


def mcp_input(schema: dict) -> dict:
    """An OpenAPI input as the product's MCP generator writes it: x-nullable becomes a null union."""
    schema = {key: value for key, value in schema.items() if key != "description"}
    if schema.pop("x-nullable", False):
        return {"anyOf": [schema, {"type": "null"}]}
    return schema


def scoped_entries() -> list[dict]:
    return [e for e in CATALOG["operations"] if mcp_name(e) in EPOCH_TOOLS | set(SQL_PROJECTIONS)
            or e["operation"]["path"].startswith("/model-hub/skills/")]


def fingerprint(manifest: dict) -> None:
    """Make tool_count and tool_names_sha256 agree with the manifest's tools."""
    manifest["tool_count"] = len(manifest["tools"])
    manifest["tool_names_sha256"] = hashlib.sha256("\n".join(sorted(t["name"] for t in manifest["tools"])).encode()).hexdigest()


def product() -> dict:
    """{"source", "manifest", "tools" (by name, the same objects), "tools_yaml"} for one product commit."""
    from generator.catalog import load

    scoped = scoped_entries()
    source = copy.deepcopy({k: v for k, v in SPEC.items() if k != "x-contract-sources"})  # tests edit it
    tools, described = [], []
    for op, entry in zip(load(SPEC, {"operations": scoped}), scoped):
        if "mcp" not in op.surfaces:  # Skills has SDK-only operations.
            continue
        mapping = op.surfaces["mcp"]
        name = mapping["name"]
        placement = {loc: [p.name for p in op.params_in(loc)] for loc in ("path", "query", "body")}
        required = sorted(p.name for p in op.params if p.required)
        if name in SQL_PROJECTIONS:
            path_names, query, body, sql_required = SQL_PROJECTIONS[name]
            assert {loc: sorted(names) for loc, names in placement.items()} == {
                "path": sorted(path_names), "query": sorted(query), "body": sorted(body)}
            assert required == sorted(sql_required)
        props = {p.name: mcp_input(p.schema) for p in op.params}
        for field, cap in mapping.get("max_page_size", {}).items():
            props[field]["maximum"] = cap
        tools.append({
            "name": name, "group": mapping["group"], "description": op.description,
            "request": {"method": op.method, "path": op.path, "parameters": placement},
            "response": {"unwrap": None if name in SQL_PROJECTIONS else "result"},
            "source": {"operationId": op.operation_id},
            "annotations": {"readOnlyHint": mapping["access"] == "read",
                            "destructiveHint": mapping["access"] == "destructive",
                            "openWorldHint": bool(mapping.get("open_world")),
                            "idempotentHint": op.method == "GET"},
            "inputSchema": {"type": "object", "properties": props, "required": required},
        })
        if mapping["group"] == "epoch":
            described.append({"name": name, "group": "epoch", "description": entry["description"]})
    tools.append({"name": "an_unscoped_tool", "group": "datasets"})
    manifest = {"schema_version": 1, "tools": tools}
    fingerprint(manifest)
    tools_yaml = {"tools": described + [{"name": "an_unscoped_tool", "group": "datasets", "description": "x"}]}
    return {"source": source, "manifest": manifest, "tools": {t["name"]: t for t in tools}, "tools_yaml": tools_yaml}
