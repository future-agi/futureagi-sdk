"""Check the committed contract slice against one product commit and record the pairing.

    python sdkgen/pair_check.py --product future-agi --sha <40-hex> --branch dev --out pair.json

Dev and pull-request CI pairs the SDK with a product commit
(.github/scripts/resolve_product_ref.py). This script reads that commit's
contract, MCP tool list and tool catalog by Git object ID (never from the working
tree), and fails unless the scoped part of sdkgen/contracts/swagger.json is what
the commit serves:

  sql    the catalog operations with ids under `sql.`;
  epoch  the catalog operations whose MCP surface is in group `epoch`.

For both scopes, the operations and every definition they reach must project
identically from the product contract and from the committed slice; drift
outside the scopes is ignored (the release sync owns it). For `epoch`, the
catalog's MCP names must be exactly the product's group `epoch` tools, and each
description must equal the product tools.yaml text byte for byte. Every scoped MCP
mapping must name the product tool's method and path.

pair.json records the product commit, the branch it was resolved from, the
sha256 of the product swagger.json, tools.generated.json and tools.yaml, the
committed slice's sha256 and x-contract-sources record, and the outcome. It is
written even when the check fails. `--extra-json` merges a JSON object (the E2E
job's image digest and bootstrap helper hash) under "stack".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import sync_contract
import yaml

ROOT = sync_contract.ROOT
SLICE = sync_contract.OUT
CATALOG = sync_contract.CATALOG
BACKEND_VERSION = sync_contract.VERSION_FILE
PRODUCT_REPOSITORY = "future-agi/future-agi"
SWAGGER = "api_contracts/openapi/swagger.json"
MCP = "futureagi/mcp_server/catalog/tools.generated.json"
TOOLS_YAML = "futureagi/mcp_server/catalog/tools.yaml"
SCOPES = ("epoch", "sql")
FULL_SHA = re.compile(r"[0-9a-f]{40}")


def scope_of(entry: dict) -> str | None:
    if entry["id"].startswith("sql."):
        return "sql"
    mcp = (entry.get("surfaces") or {}).get("mcp")
    if isinstance(mcp, dict) and mcp.get("group") == "epoch":
        return "epoch"
    return None


def mcp_name(entry: dict) -> str | None:
    mcp = (entry.get("surfaces") or {}).get("mcp")
    if mcp in (None, False):
        return None
    return (mcp or {}).get("name") or entry["id"].replace(".", "_")


def scoped(catalog: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {scope: [] for scope in SCOPES}
    for entry in catalog["operations"]:
        scope = scope_of(entry)
        if scope:
            out[scope].append(entry)
    return out


def _project(spec: dict, entries: list[dict], where: str) -> tuple[dict, dict]:
    try:
        return sync_contract.project(spec, entries)
    except SystemExit as exc:  # project() reports a missing operation this way
        raise ValueError(f"{where}: {exc}") from None
    except KeyError as exc:
        raise ValueError(f"{where}: unresolved definition {exc}") from None


def compare_projection(product: dict, committed: dict, entries: list[dict], scope: str) -> list[str]:
    """Problems where the scoped operations or their definitions differ."""
    if not entries:
        return []
    problems = []
    try:
        theirs = _project(product, entries, "product contract")
        ours = _project(committed, entries, "committed slice")
    except ValueError as exc:
        return [f"{scope}: {exc}"]
    (their_paths, their_defs), (our_paths, our_defs) = theirs, ours
    for path in sorted(set(their_paths) | set(our_paths)):
        a, b = their_paths.get(path, {}), our_paths.get(path, {})
        for key in sorted(set(a) | set(b)):
            if a.get(key) != b.get(key):
                problems.append(f"{scope}: {key} {path} differs from the product contract")
    for name in sorted(set(their_defs) | set(our_defs)):
        if their_defs.get(name) != our_defs.get(name):
            state = "missing from the slice" if name not in our_defs else (
                "no longer reached on the product" if name not in their_defs else "differs from the product contract")
            problems.append(f"{scope}: definition {name} {state}")
    return problems


def compare_mcp(manifest: dict, tools_yaml: dict, entries: dict[str, list[dict]]) -> list[str]:
    problems = []
    listed = manifest.get("tools") or []
    tools = {tool["name"]: tool for tool in listed}
    if len(tools) != len(listed) or manifest.get("tool_count") != len(listed):
        problems.append("product MCP manifest has duplicate tools or a wrong tool_count")
    for scope in SCOPES:
        for entry in entries[scope]:
            name = mcp_name(entry)
            if name is None:
                continue
            tool = tools.get(name)
            if tool is None:
                problems.append(f"{scope}: {entry['id']} maps to MCP tool {name}, which the product does not have")
                continue
            want = (entry["operation"]["method"].upper(), entry["operation"]["path"])
            have = (str(tool["request"]["method"]).upper(), tool["request"]["path"])
            if want != have:
                problems.append(f"{scope}: {entry['id']} is {want[0]} {want[1]}, product {name} is {have[0]} {have[1]}")
    product_epoch = {name for name, tool in tools.items() if tool.get("group") == "epoch"}
    catalog_epoch = {mcp_name(entry) for entry in entries["epoch"]} - {None}
    if product_epoch - catalog_epoch:
        problems.append("epoch: product tools without an epoch catalog entry: " + ", ".join(sorted(product_epoch - catalog_epoch)))
    if catalog_epoch - product_epoch:
        problems.append("epoch: catalog entries outside the product's epoch group: " + ", ".join(sorted(catalog_epoch - product_epoch)))
    texts = {tool["name"]: tool.get("description") for tool in tools_yaml.get("tools") or []}
    for entry in entries["epoch"]:
        name = mcp_name(entry)
        if name in texts and entry.get("description") != texts[name]:
            problems.append(f"epoch: {entry['id']} description differs from product tools.yaml {name}")
    return problems


def _git(product: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(product), *args])


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def check(product: Path, sha: str) -> tuple[list[str], dict]:
    """(problems, facts) for the committed slice and catalog at product commit `sha`."""
    head = _git(product, "rev-parse", "HEAD").decode().strip()
    if head != sha:
        raise ValueError(f"product checkout is at {head}, not {sha}")
    raw = {path: _git(product, "show", f"{sha}:{path}") for path in (SWAGGER, MCP, TOOLS_YAML)}
    slice_raw = SLICE.read_bytes()
    catalog_raw = CATALOG.read_bytes()
    product_spec = json.loads(raw[SWAGGER])
    manifest = json.loads(raw[MCP])
    tools_yaml = yaml.safe_load(raw[TOOLS_YAML])
    committed = json.loads(slice_raw)
    catalog = yaml.safe_load(catalog_raw)
    entries = scoped(catalog)
    problems = []
    for scope in SCOPES:
        problems += compare_projection(product_spec, committed, entries[scope], scope)
    problems += compare_mcp(manifest, tools_yaml, entries)
    facts = {
        "hashes": {
            "openapi_sha256": _sha256(raw[SWAGGER]),
            "mcp_sha256": _sha256(raw[MCP]),
            "tools_yaml_sha256": _sha256(raw[TOOLS_YAML]),
            "sdk_slice_sha256": _sha256(slice_raw),
            "sdk_catalog_sha256": _sha256(catalog_raw),
        },
        "mcp": {"tool_count": manifest.get("tool_count"), "tool_names_sha256": manifest.get("tool_names_sha256")},
        "scope": {scope: sorted(entry["id"] for entry in entries[scope]) for scope in SCOPES},
        "contract_sources": committed.get("x-contract-sources"),
    }
    return problems, facts


def _sdk_sha() -> str | None:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--product", type=Path, required=True, help="a future-agi checkout that contains --sha")
    parser.add_argument("--sha", required=True, help="the full 40-hex product commit to pair with")
    parser.add_argument("--branch", default="", help="the product branch the commit was resolved from")
    parser.add_argument("--mode", default="paired", choices=["paired"], help="recorded as-is")
    parser.add_argument("--out", type=Path, required=True, help="where to write pair.json")
    parser.add_argument("--extra-json", type=Path, help="a JSON object to record under \"stack\"")
    args = parser.parse_args(argv)
    if not FULL_SHA.fullmatch(args.sha):
        parser.error("--sha must be a full lowercase 40-hex commit")
    record: dict = {
        "schema": 1,
        "mode": args.mode,
        "product": {"repository": PRODUCT_REPOSITORY, "sha": args.sha, "resolved_branch": args.branch},
        "sdk": {"sha": _sdk_sha(), "backend_version": BACKEND_VERSION.read_text().strip()},
        "scope_groups": list(SCOPES),
    }
    try:
        problems, facts = check(args.product, args.sha)
        record.update(facts)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        problems = [f"could not read the pairing inputs: {exc}"]
    if args.extra_json:
        try:
            extra = json.loads(args.extra_json.read_text())
            if not isinstance(extra, dict):
                raise ValueError("not a JSON object")
            record["stack"] = extra
        except (OSError, ValueError) as exc:
            problems.append(f"--extra-json {args.extra_json}: {exc}")
    record["slice_matches"] = not problems
    record["problems"] = problems
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    for problem in problems:
        print(f"pair check: {problem}", file=sys.stderr)
    if problems:
        return 1
    counts = ", ".join(f"{len(record['scope'][scope])} {scope}" for scope in SCOPES)
    print(f"pair check: {counts} operations match {PRODUCT_REPOSITORY}@{args.sha} ({args.branch or 'explicit'}); wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
