"""The catalog is the source of truth: these tests show what it guarantees (no backend needed)."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from sdkgen import generator as generate  # noqa: E402
from sdkgen.generator import python as pygen  # noqa: E402
from sdkgen.generator import typescript as tsgen  # noqa: E402

__all__ = ["CATALOG", "CONTRACT", "MCP_IDS", "ROOT", "_with", "generate", "pygen", "tsgen"]

CONTRACT = json.loads((ROOT / "sdkgen" / "contracts" / "swagger.json").read_text())
CATALOG = yaml.safe_load((ROOT / "sdkgen" / "catalog" / "operations.yaml").read_text())
# The MCP server and its manifest live in the monorepo (futureagi/mcp_server/catalog); the
# catalog here only records which MCP tool each operation corresponds to. The monorepo's
# E2E CI compares the two.
MCP_IDS = {
    e["id"]
    for e in CATALOG["operations"]
    if e["surfaces"].get("mcp") not in (None, False)
}


def _with(op_id: str, **changes) -> dict:
    catalog = copy.deepcopy(CATALOG)
    next(e for e in catalog["operations"] if e["id"] == op_id).update(changes)
    return catalog

