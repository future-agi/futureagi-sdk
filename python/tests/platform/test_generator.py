"""The catalog is the source of truth: these tests show what it guarantees (no backend needed)."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
spec_ = importlib.util.spec_from_file_location("generate", ROOT / "sdkgen" / "generate.py")
generate = importlib.util.module_from_spec(spec_)
sys.modules["generate"] = generate
spec_.loader.exec_module(generate)

CONTRACT = json.loads((ROOT / "sdkgen" / "contracts" / "swagger.json").read_text())
CATALOG = yaml.safe_load((ROOT / "sdkgen" / "catalog" / "operations.yaml").read_text())
MCP = json.loads((ROOT / "sdkgen" / "mcp" / "tools.generated.json").read_text())


def _with(op_id: str, **changes) -> dict:
    catalog = copy.deepcopy(CATALOG)
    next(e for e in catalog["operations"] if e["id"] == op_id).update(changes)
    return catalog


def test_committed_outputs_are_up_to_date():
    stale = [str(p.relative_to(ROOT)) for p, text in generate.build().items() if p.read_text() != text]
    assert not stale, f"run python sdkgen/generate.py: {stale}"


def test_surfaces_ship_independently():
    from fi.platform import Client

    mcp_ids = {t["source"]["catalogId"] for t in MCP["tools"]}
    sdk_ids = {e["id"] for e in CATALOG["operations"] if e["surfaces"].get("sdk") is not False}
    assert "datasets.columns.add" in sdk_ids - mcp_ids  # SDK-only
    client = Client(api_key="k", secret_key="s", base_url="http://unused")
    assert callable(client.datasets.columns.add)


def test_mcp_names_keep_existing_tools_or_follow_the_id():
    # Every catalog entry keeps the monorepo's MCP tool name: 105 tools, same names.
    assert MCP["tool_count"] == 105
    names = {t["source"]["catalogId"]: t["name"] for t in MCP["tools"]}
    assert names["datasets.list"] == "list_datasets"
    assert names["traces.list"] == "search_traces"
    # Without an override the name follows the id.
    catalog = _with("datasets.columns.add", surfaces={"sdk": {}, "mcp": {"group": "datasets", "access": "write"}})
    op = next(o for o in generate.load(CONTRACT, catalog) if o.id == "datasets.columns.add")
    assert op.surfaces["mcp"]["name"] == "datasets_columns_add"


def test_mcp_input_schema_comes_from_the_contract():
    tool = next(t for t in MCP["tools"] if t["name"] == "create_dataset")
    assert tool["inputSchema"]["required"] == ["new_dataset_name"]
    assert tool["request"] == {"method": "POST", "path": "/model-hub/develops/create-empty-dataset/",
                               "parameters": {"path": [], "query": [], "body": ["new_dataset_name", "model_type", "is_sdk", "row"]}}


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"surfaces": {"sdk": {}, "web": {}}}, "unknown surface"),
        ({"surfaces": {"mcp": {"access": "read"}}}, "mcp.group is required"),
        ({"surfaces": {"sdk": {"stability": "alpha"}}}, "stability"),
        ({"surfaces": {"sdk": False, "mcp": False}}, "ships to no surface"),
        ({"operation": {"method": "GET", "path": "/nope/"}}, "not in the contract"),
        ({"pagination": {"page_param": "cursor", "size_param": "page_size", "first_page": 1,
                         "items": "datasets", "total_pages": "total_pages"}}, "not a query param"),
        ({"surfaces": {"mcp": {"name": "create_dataset", "group": "d", "access": "read"}}}, "already used"),
    ],
)
def test_catalog_mistakes_fail_the_build(changes, message):
    with pytest.raises(generate.CatalogError, match=message):
        generate.load(CONTRACT, _with("datasets.list", **changes))


def test_pagination_needs_first_page_and_items():
    with pytest.raises(generate.CatalogError, match="first_page is required"):
        generate.load(CONTRACT, _with("datasets.list", pagination={"page_param": "page", "size_param": "page_size", "items": "datasets", "total_pages": "total_pages"}))


def test_body_params_on_a_paginated_op_fail_the_build():
    # evals.templates.list is a POST with body params; paginating it would drop them silently.
    catalog = _with("evals.templates.list", pagination={"page_param": "page", "size_param": "page_size", "first_page": 1, "items": "items", "total_items": "total"})
    with pytest.raises(generate.CatalogError, match="sends no body"):
        generate.load(CONTRACT, catalog)
