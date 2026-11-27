"""sdkgen/check_mcp_descriptions.py: epoch-group catalog descriptions against the product's tools.yaml."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sdkgen"))

import check_mcp_descriptions as descriptions  # noqa: E402

CATALOG = yaml.safe_load((ROOT / "sdkgen" / "catalog" / "operations.yaml").read_text())
CONTRACT = json.loads((ROOT / "sdkgen" / "contracts" / "swagger.json").read_text())


def _product_tools(catalog: dict) -> dict:
    """tools.yaml as the product would write it for this catalog's epoch entries."""
    return {
        entry["surfaces"]["mcp"]["name"]: {"name": entry["surfaces"]["mcp"]["name"], "group": "epoch", "description": entry["description"]}
        for entry in catalog["operations"]
        if (entry["surfaces"].get("mcp") or {}).get("group") == "epoch"
    }


def test_the_recorded_product_tools_yaml_matches_byte_for_byte():
    """The real check: tools.yaml at the product commit recorded in x-contract-sources, its bytes
    verified against the recorded sha256, then every epoch description compared as UTF-8 bytes."""
    record = descriptions.recorded_source(CONTRACT)
    assert record["backend_commit"] == CONTRACT["x-contract-sources"]["sql"]["backend_commit"]
    raw = descriptions.fetch(record["backend_commit"])
    assert hashlib.sha256(raw).hexdigest() == record["tools_yaml_sha256"]
    product = descriptions.yaml_tools(raw)
    assert sum(1 for tool in product.values() if tool["group"] == "epoch") == 19
    assert descriptions.compare(CATALOG, product) == []


def test_one_changed_byte_is_reported_with_its_offset():
    tools = _product_tools(CATALOG)
    assert len(tools) == 19 and descriptions.compare(CATALOG, tools) == []
    catalog = copy.deepcopy(CATALOG)
    entry = next(e for e in catalog["operations"] if e["id"] == "simulation.epochs.stop")
    entry["description"] = entry["description"].replace("Stopped", "stopped")
    assert descriptions.compare(catalog, tools) == [
        "simulation.epochs.stop: description differs from product tool stop_epoch at byte 33"
    ]


def test_missing_and_unknown_tools_are_both_reported():
    tools = _product_tools(CATALOG)
    tools["get_epoch_tomorrow"] = {"name": "get_epoch_tomorrow", "group": "epoch", "description": "x"}
    del tools["list_epochs"]
    assert descriptions.compare(CATALOG, tools) == [
        "simulation.epochs.list: product tools.yaml has no epoch tool list_epochs",
        "product tools without a catalog entry: get_epoch_tomorrow",
    ]


def test_other_groups_are_not_compared():
    tools = _product_tools(CATALOG)
    tools["list_datasets"] = {"name": "list_datasets", "group": "datasets", "description": "not the catalog's text"}
    assert descriptions.compare(CATALOG, tools) == []
