#!/usr/bin/env python3
"""The catalog's descriptions of scoped MCP groups match the product's tools.yaml byte for byte.

    python sdkgen/check_mcp_descriptions.py                    against tools.yaml at the product commit
                                                               recorded in contracts/swagger.json
                                                               x-contract-sources (sha256 checked)
    python sdkgen/check_mcp_descriptions.py --ref FULL_SHA     against tools.yaml at another product commit
    python sdkgen/check_mcp_descriptions.py --tools-yaml FILE  against a local tools.yaml (sha256 checked)

For the groups in GROUPS (today `epoch`), each catalog entry's `description` is the product
tool's description: the SDK docstring, the docs and the MCP tool say the same thing. Every tool
of such a group in tools.yaml needs exactly one catalog entry, and the strings are compared as
UTF-8 bytes after YAML parsing. sync_scoped_contract.py runs the same comparison before it writes
the contract slice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "sdkgen" / "catalog" / "operations.yaml"
CONTRACT = ROOT / "sdkgen" / "contracts" / "swagger.json"
TOOLS_YAML = "futureagi/mcp_server/catalog/tools.yaml"
TOOLS_URL = "https://raw.githubusercontent.com/future-agi/future-agi/{ref}/" + TOOLS_YAML
GROUPS = ("epoch",)


def yaml_tools(raw: bytes) -> dict[str, dict]:
    tools = yaml.safe_load(raw)["tools"]
    by_name = {tool["name"]: tool for tool in tools}
    if len(by_name) != len(tools):
        raise ValueError("product tools.yaml repeats a tool name")
    return by_name


def compare(catalog: dict, tools: dict[str, dict], groups: tuple[str, ...] = GROUPS) -> list[str]:
    """Problems, in plain words; empty when every description in the groups matches."""
    problems = []
    seen: dict[str, str] = {}
    for entry in catalog["operations"]:
        mapping = entry.get("surfaces", {}).get("mcp")
        if mapping in (None, False) or mapping.get("group") not in groups:
            continue
        name = mapping.get("name") or entry["id"].replace(".", "_")
        if name in seen:
            problems.append(f"{entry['id']}: MCP tool {name} is already mapped by {seen[name]}")
            continue
        seen[name] = entry["id"]
        tool = tools.get(name)
        if tool is None or tool.get("group") != mapping["group"]:
            problems.append(f"{entry['id']}: product tools.yaml has no {mapping['group']} tool {name}")
            continue
        want, have = tool["description"].encode("utf-8"), str(entry.get("description", "")).encode("utf-8")
        if want != have:
            at = next((i for i, (a, b) in enumerate(zip(want, have)) if a != b), min(len(want), len(have)))
            problems.append(f"{entry['id']}: description differs from product tool {name} at byte {at}")
    missing = sorted(name for name, tool in tools.items() if tool.get("group") in groups and name not in seen)
    if missing:
        problems.append("product tools without a catalog entry: " + ", ".join(missing))
    return problems


def recorded_source(contract: dict) -> dict:
    """The product commit and tools.yaml hash the described groups were synced from."""
    sources = contract.get("x-contract-sources", {})
    records = [sources.get(group) for group in GROUPS]
    if any(not record for record in records):
        raise ValueError(f"contracts/swagger.json x-contract-sources records no {', '.join(GROUPS)} source")
    if len({(r["backend_commit"], r["tools_yaml_sha256"]) for r in records}) != 1:
        raise ValueError("the described groups were synced from different product commits")
    return records[0]


def fetch(ref: str, attempts: int = 3) -> bytes:
    if not re.fullmatch(r"[a-f0-9]{40}", ref):
        raise ValueError("--ref must be a full product commit hash")
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(TOOLS_URL.format(ref=ref), timeout=30) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--ref", help="full commit of future-agi/future-agi (default: the recorded one)")
    src.add_argument("--tools-yaml", type=Path, help="a local tools.yaml, checked against the recorded sha256")
    args = ap.parse_args(argv)
    record = recorded_source(json.loads(CONTRACT.read_text()))
    if args.tools_yaml:
        raw, where = args.tools_yaml.read_bytes(), str(args.tools_yaml)
    else:
        ref = args.ref or record["backend_commit"]
        raw, where = fetch(ref), f"future-agi/future-agi@{ref}"
    if (args.tools_yaml or not args.ref or args.ref == record["backend_commit"]) and (
        hashlib.sha256(raw).hexdigest() != record["tools_yaml_sha256"]
    ):
        print(f"mcp descriptions: {where} is not the tools.yaml recorded in x-contract-sources", file=sys.stderr)
        return 1
    problems = compare(yaml.safe_load(CATALOG.read_text()), yaml_tools(raw))
    for problem in problems:
        print(f"mcp descriptions: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"mcp descriptions: {', '.join(GROUPS)} descriptions match {where} byte for byte")
    return 0


if __name__ == "__main__":
    sys.exit(main())
