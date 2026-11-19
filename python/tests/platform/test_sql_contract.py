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
