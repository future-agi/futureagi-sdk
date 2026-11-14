#!/usr/bin/env python3
"""The catalog's MCP names match the monorepo's MCP tool list.

    python sdkgen/check_mcp_parity.py                      against the tool list of the pinned backend
                                                           release (sdkgen/contracts/BACKEND_VERSION)
    python sdkgen/check_mcp_parity.py --ref dev            against a branch or tag of future-agi/future-agi
    python sdkgen/check_mcp_parity.py --tools tools.json   against a local tools.generated.json

Every catalog operation with an `mcp` surface names the MCP tool it corresponds to
(`surfaces.mcp.name`, else the id with dots as underscores). The tool list itself is
generated in the monorepo (futureagi/mcp_server/catalog/tools.generated.json). The two must
agree at the backend release the SDK is synced to, so CI runs this against that release: a
backend sync that brings new tools fails here until the catalog gets their entries, and a
catalog entry for a tool the backend does not have fails too. The monorepo's E2E job runs
the same comparison against its own tree, as a warning.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "sdkgen" / "catalog" / "operations.yaml"
BACKEND_VERSION = ROOT / "sdkgen" / "contracts" / "BACKEND_VERSION"
TOOLS_URL = "https://raw.githubusercontent.com/future-agi/future-agi/{ref}/futureagi/mcp_server/catalog/tools.generated.json"


def catalog_mcp_names(catalog: dict) -> set[str]:
    out = set()
    for entry in catalog["operations"]:
        mcp = entry.get("surfaces", {}).get("mcp")
        if mcp in (None, False):
            continue
        out.add((mcp or {}).get("name") or entry["id"].replace(".", "_"))
    return out


def tool_names(tools: dict) -> set[str]:
    return {t["name"] for t in tools["tools"]}


def compare(tools: dict, catalog: dict) -> list[str]:
    """Problems, in plain words; empty when the two lists agree."""
    have, want = tool_names(tools), catalog_mcp_names(catalog)
    problems = []
    if have - want:
        problems.append("MCP tools without a catalog entry (add them to sdkgen/catalog/operations.yaml): " + ", ".join(sorted(have - want)))
    if want - have:
        problems.append("catalog entries whose MCP tool the backend does not have: " + ", ".join(sorted(want - have)))
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--ref", help="branch or tag of future-agi/future-agi (default: the pinned backend release)")
    src.add_argument("--tools", type=Path, help="a local tools.generated.json")
    args = ap.parse_args(argv)
    if args.tools:
        tools = json.loads(args.tools.read_text())
        where = str(args.tools)
    else:
        ref = args.ref or BACKEND_VERSION.read_text().strip()
        where = f"future-agi/future-agi@{ref}"
        with urllib.request.urlopen(TOOLS_URL.format(ref=ref), timeout=30) as r:
            tools = json.load(r)
    catalog = yaml.safe_load(CATALOG.read_text())
    problems = compare(tools, catalog)
    for p in problems:
        print(f"mcp parity: {p}", file=sys.stderr)
    if problems:
        return 1
    print(f"mcp parity: {len(tool_names(tools))} tools in {where}, same names in the catalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
