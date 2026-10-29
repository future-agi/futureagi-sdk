"""sdkgen/check_mcp_parity.py: the catalog's MCP names against a tool list."""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "sdkgen"))

import check_mcp_parity as parity  # noqa: E402

CATALOG = yaml.safe_load((Path(__file__).resolve().parents[3] / "sdkgen" / "catalog" / "operations.yaml").read_text())


def _tools(names):
    return {"tools": [{"name": n} for n in names]}


def test_the_committed_catalog_names_every_tool_once():
    names = parity.catalog_mcp_names(CATALOG)
    assert len(names) == sum(1 for e in CATALOG["operations"] if e["surfaces"].get("mcp") not in (None, False))
    assert parity.compare(_tools(names), CATALOG) == []


def test_a_new_tool_and_a_stale_entry_are_both_reported():
    names = parity.catalog_mcp_names(CATALOG)
    problems = parity.compare(_tools((names - {"list_datasets"}) | {"get_error_cluster_overview"}), CATALOG)
    assert problems == [
        "MCP tools without a catalog entry (add them to sdkgen/catalog/operations.yaml): get_error_cluster_overview",
        "catalog entries whose MCP tool the backend does not have: list_datasets",
    ]


def test_a_name_defaults_to_the_id_with_underscores():
    catalog = {"operations": [{"id": "datasets.rows.add", "surfaces": {"sdk": {}, "mcp": {"group": "d", "access": "write"}}},
                              {"id": "datasets.get", "surfaces": {"sdk": {}, "mcp": {"name": "get_dataset", "group": "d", "access": "read"}}},
                              {"id": "only.sdk", "surfaces": {"sdk": {}, "mcp": False}}]}
    assert parity.catalog_mcp_names(catalog) == {"datasets_rows_add", "get_dataset"}
