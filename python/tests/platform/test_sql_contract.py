"""Contract shape tests, independent of a running backend."""

import copy
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sdkgen.generator.catalog import CatalogError, load  # noqa: E402


def sql_contract():
    spec = json.loads((ROOT / "sdkgen/contracts/swagger.json").read_text())
    catalog = yaml.safe_load((ROOT / "sdkgen/catalog/operations.yaml").read_text())
    return spec, {**catalog, "operations": [e for e in catalog["operations"] if e["id"].startswith("sql.")]}


def test_four_public_mappings_preserve_distinct_rest_and_mcp_limits():
    spec, catalog = sql_contract()
    ops = {op.surfaces["mcp"]["name"]: op for op in load(spec, catalog)}
    expected = {
        "cancel_sql": ("POST", "/tracer/sql-query/{id}/cancel/", "SQLExecution"),
        "get_sql_catalog": ("GET", "/tracer/sql-query/catalog/", "SQLCatalog"),
        "get_sql_result": ("GET", "/tracer/sql-query/{id}/", "SQLExecution"),
        "run_sql": ("POST", "/tracer/sql-query/run/", "SQLExecution"),
    }
    assert {name: (op.method, op.path, op.returns["$ref"].split("/")[-1]) for name, op in ops.items()} == expected
    for op in ops.values():
        assert op.unwrap is None and op.pagination is None
        assert op.surfaces["mcp"]["group"] == "observability" and op.surfaces["mcp"]["access"] == "read"
    read = ops["get_sql_result"]
    query = {p.name: p for p in read.params_in("query")}
    assert query["project_id"].required and not query["limit"].required
    assert (query["limit"].schema["minimum"], query["limit"].schema["maximum"]) == (1, 1000)
    assert (query["offset"].schema["default"], query["offset"].schema["maximum"]) == (0, 10000)
    assert read.surfaces["mcp"]["max_page_size"] == {"limit": 100}
    run = {p.name: p for p in ops["run_sql"].params_in("body")}
    assert {key for key, p in run.items() if p.required} == {"project_id", "sql", "start", "end"}
    assert run["sql"].schema["maxLength"] == 32768 and run["reuse"].schema["default"] is True


def test_accepted_response_selection_is_explicit_and_fails_on_removed_status():
    spec, catalog = sql_contract()
    entry = copy.deepcopy(next(e for e in catalog["operations"] if e["id"] == "sql.run"))
    del entry["operation"]["response_status"]
    entry["surfaces"]["sdk"] = {}
    assert load(spec, {"operations": [entry]})[0].returns is None
    del spec["paths"]["/tracer/sql-query/run/"]["post"]["responses"]["202"]
    with pytest.raises(CatalogError, match="requires a declared 202 response"):
        load(spec, catalog)


@pytest.fixture
def scoped_sync(monkeypatch):
    """Exercise the two-input gate without depending on Git history in a shallow CI checkout."""
    import hashlib

    monkeypatch.syspath_prepend(str(ROOT / "sdkgen"))
    import sync_sql_contract as sync

    spec, sql = sql_contract()
    baseline = {**spec, "paths": {p: v for p, v in spec["paths"].items() if not p.startswith("/tracer/sql-query/")},
                "definitions": {k: v for k, v in spec["definitions"].items() if not k.startswith("SQL")},
                "x-source-sha256": "baseline-hash"}
    source = json.dumps(spec).encode()
    manifest = {"tool_count": 4, "source_contract_sha256": hashlib.sha256(source).hexdigest(), "tools": []}
    projections = {
        "run_sql": ([], [], ["project_id", "sql", "start", "end", "reuse"], ["project_id", "sql", "start", "end"]),
        "get_sql_result": (["id"], ["project_id", "offset", "limit"], [], ["id", "project_id"]),
        "cancel_sql": (["id"], [], ["project_id"], ["id", "project_id"]),
        "get_sql_catalog": ([], ["project_id"], [], ["project_id"]),
    }
    for entry in sql["operations"]:
        operation = entry["operation"]
        path, method = operation["path"], operation["method"]
        tool_name = entry["surfaces"]["mcp"]["name"]
        path_names, query, body, required = projections[tool_name]
        props = {k: {} for k in path_names + query + body}
        if "limit" in props:
            props["limit"]["maximum"] = 100
        manifest["tools"].append({
            "name": tool_name, "group": "observability", "response": {"unwrap": None},
            "request": {"method": method, "path": path, "parameters": {"path": path_names, "query": query, "body": body}},
            "source": {"operationId": spec["paths"][path][method.lower()]["operationId"]},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False, "idempotentHint": method == "GET"},
            "inputSchema": {"properties": props, "required": required},
        })

    def blob(_repo, _commit, path):
        return {"sdkgen/contracts/swagger.json": json.dumps(baseline).encode(), sync.SWAGGER: source,
                sync.MCP: json.dumps(manifest).encode()}[path]

    monkeypatch.setattr(sync, "_blob", blob)
    return lambda: sync.compose(ROOT, "0" * 40, "1" * 40), baseline, manifest


def test_scoped_sync_rejects_mismatched_source_bytes_and_shared_definitions(scoped_sync):
    compose, baseline, manifest = scoped_sync
    baseline["definitions"]["ManagementAPIErrorResponse"]["title"] = "conflicting baseline shape"
    with pytest.raises(ValueError, match="collides"):
        compose()
    manifest["source_contract_sha256"] = "wrong"
    with pytest.raises(ValueError, match="hashes disagree"):
        compose()


@pytest.mark.parametrize("drift, message", [
    ("move_path", "placement"), ("move_query", "placement"), ("move_body", "placement"),
    ("missing_required", "required"), ("extra_required", "required"), ("extra_property", "properties"),
])
def test_scoped_sync_rejects_mcp_input_projection_drift(scoped_sync, drift, message):
    compose, _, manifest = scoped_sync
    tools = {tool["name"]: tool for tool in manifest["tools"]}
    reader = tools["get_sql_result"]
    params = reader["request"]["parameters"]
    if drift == "move_path":
        params["query"].append(params["path"].pop())
    elif drift == "move_query":
        params["body"].append(params["query"].pop())
    elif drift == "move_body":
        params = tools["run_sql"]["request"]["parameters"]
        params["query"].append(params["body"].pop())
    elif drift == "missing_required":
        reader["inputSchema"]["required"].remove("project_id")
    elif drift == "extra_required":
        reader["inputSchema"]["required"].append("offset")
    else:
        reader["inputSchema"]["properties"]["unknown"] = {}
    with pytest.raises(ValueError, match=message):
        compose()


def test_optional_input_nullability_comes_from_the_schema_only_when_opted_in():
    spec, catalog = sql_contract()
    ops = load(spec, catalog)
    assert {(op.id, p.name) for op in ops for p in op.params if op.rejects_optional_null(p)} == {
        ("sql.run", "reuse"), ("sql.get_result", "limit"), ("sql.get_result", "offset"),
    }
    run = next(e for e in catalog["operations"] if e["id"] == "sql.run")

    def rejects_reuse():
        op, = load(spec, {"operations": [run]})
        return op.rejects_optional_null(next(p for p in op.params if p.name == "reuse"))

    # A later schema may explicitly allow clearing a field without making it required.
    prop = spec["definitions"]["SQLRun"]["properties"]["reuse"]
    prop["x-nullable"] = True
    assert not rejects_reuse()
    del prop["x-nullable"]
    del run["surfaces"]["sdk"]["declared_optional_nullability"]
    assert not rejects_reuse()  # old, non-opted-in operations keep accepting null
