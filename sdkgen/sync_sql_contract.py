"""Sync the four SQL operations from an immutable product commit without upgrading other SDK operations.

    python sdkgen/sync_sql_contract.py /path/to/product PRODUCT_COMMIT BASELINE_SDK_COMMIT

Both inputs are read by Git object ID, not from a working tree. The normal release sync
supersedes this mixed-source slice; BACKEND_VERSION is not a claim that the old image has SQL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import sync_contract
import yaml
from generator.catalog import Op, load

TOOLS = {"run_sql", "get_sql_result", "cancel_sql", "get_sql_catalog"}
SWAGGER = "api_contracts/openapi/swagger.json"
MCP = "futureagi/mcp_server/catalog/tools.generated.json"


def _blob(repo: Path, commit: str, path: str) -> bytes:
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("contract sources require full commit hashes")
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{commit}:{path}"])


def _check_mcp_parameters(op: Op, tool: dict) -> None:
    """Compare the generated SDK inputs to the MCP wire mapping, not just its route."""
    expected = {loc: sorted(p.name for p in op.params_in(loc)) for loc in ("path", "query", "body")}
    actual = tool["request"]["parameters"]
    if {loc: sorted(names) for loc, names in actual.items()} != expected:
        raise ValueError(f"SQL MCP parameter placement mismatch: {op.id}")
    schema = tool["inputSchema"]
    if set(schema["properties"]) != {p.name for p in op.params}:
        raise ValueError(f"SQL MCP input properties mismatch: {op.id}")
    if sorted(schema.get("required", [])) != sorted(p.name for p in op.params if p.required):
        raise ValueError(f"SQL MCP required parameters mismatch: {op.id}")


def compose(product: Path, commit: str, baseline_sdk: str) -> dict:
    old_raw = _blob(sync_contract.ROOT, baseline_sdk, "sdkgen/contracts/swagger.json")
    source_raw = _blob(product, commit, SWAGGER)
    tools_raw = _blob(product, commit, MCP)
    old, source, manifest = map(json.loads, (old_raw, source_raw, tools_raw))
    source_hash = hashlib.sha256(source_raw).hexdigest()
    if manifest["source_contract_sha256"] != source_hash:
        raise ValueError("product MCP and OpenAPI hashes disagree")
    tools = {t["name"]: t for t in manifest["tools"]}
    if len(tools) != len(manifest["tools"]) or len(tools) != manifest["tool_count"]:
        raise ValueError("invalid product MCP manifest")
    entries = yaml.safe_load(sync_contract.CATALOG.read_text())["operations"]
    sql, existing = [], []
    for entry in entries:
        method = entry["operation"]["method"]
        path = entry["operation"]["path"]
        is_sql = entry["id"].startswith("sql.")
        if is_sql != path.startswith("/tracer/sql-query/"):
            raise ValueError(f"SQL scope mismatch: {entry['id']}")
        if method.lower() not in source["paths"].get(path, {}):
            raise ValueError(f"selected operation missing on product: {method} {path}")
        if is_sql:
            mapping = entry["surfaces"]["mcp"]
            tool = tools[mapping["name"]]
            hints = tool["annotations"]
            if (mapping["group"] != tool["group"] or mapping["access"] != "read"
                    or not hints["readOnlyHint"] or hints["destructiveHint"] or hints["openWorldHint"]
                    or hints["idempotentHint"] != (method == "GET") or tool["response"]["unwrap"] is not None):
                raise ValueError(f"SQL MCP exposure mismatch: {entry['id']}")
            for field, cap in mapping.get("max_page_size", {}).items():
                if tool["inputSchema"]["properties"][field].get("maximum") != cap:
                    raise ValueError(f"SQL MCP page limit mismatch: {entry['id']}.{field}")
            if (tool["request"]["method"], tool["request"]["path"], tool["source"]["operationId"]) != (
                method, path, source["paths"][path][method.lower()]["operationId"]
            ):
                raise ValueError(f"SQL MCP operation mismatch: {entry['id']}")
        (sql if is_sql else existing).append(entry)
    if len(sql) != len(TOOLS) or {e["surfaces"]["mcp"]["name"] for e in sql} != TOOLS:
        raise ValueError("expected exactly four public SQL mappings")
    for op in load(source, {"operations": sql}):
        _check_mcp_parameters(op, tools[op.surfaces["mcp"]["name"]])
    old_paths, old_defs = sync_contract.project(old, existing)
    if old_paths != old["paths"] or old_defs != old["definitions"]:
        raise ValueError("SQL projection would alter the SDK baseline")
    new_paths, new_defs = sync_contract.project(source, sql)
    if old_paths.keys() & new_paths.keys() or any(old_defs[k] != new_defs[k] for k in old_defs.keys() & new_defs.keys()):
        raise ValueError("SQL projection collides with baseline routes or definitions")
    if any(old[key] != source[key] for key in ("swagger", "securityDefinitions", "security")):
        raise ValueError("product and SDK baseline dialect/auth differ")
    return {
        **{key: old[key] for key in ("swagger", "info", "securityDefinitions", "security")},
        "x-contract-sources": {
            "sql": {"backend_commit": commit, "openapi_sha256": source_hash,
                    "mcp_sha256": hashlib.sha256(tools_raw).hexdigest(), "tools": sorted(TOOLS)},
            "other": {"sdk_commit": baseline_sdk, "slice_sha256": hashlib.sha256(old_raw).hexdigest(),
                      "openapi_sha256": old["x-source-sha256"]},
        },
        "paths": dict(sorted({**old_paths, **new_paths}.items())),
        "definitions": dict(sorted({**old_defs, **new_defs}.items())),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product", type=Path)
    parser.add_argument("commit")
    parser.add_argument("baseline_sdk")
    args = parser.parse_args()
    result = compose(args.product, args.commit, args.baseline_sdk)
    sync_contract.OUT.write_text(json.dumps(result, indent=2) + "\n")
