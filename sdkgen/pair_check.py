"""Check the committed contract slice against one product commit and record the pairing.

    python sdkgen/pair_check.py --product future-agi --sha <40-hex> --branch dev --out pair.json

Dev and pull-request CI pairs the SDK with a product commit
(.github/scripts/resolve_product_ref.py). This script reads that commit's
contract, MCP tool list and tool catalog by Git object ID (never from the working
tree), and fails unless the scoped part of sdkgen/contracts/swagger.json is what
the commit serves. The scopes and every per-tool rule are the ones the scoped
sync applies before it writes the slice (sync_scoped_contract.SCOPES and
check_scopes): today `sql` (the four SQL tools) and `epoch` (every product MCP
tool in group epoch), each mapped exactly once, with group, access, open-world,
method, path, operationId, inputs, page caps and unwrap matching the product
tool, and epoch descriptions equal to product tools.yaml byte for byte.

On top of that, each scope's operations and every definition they reach must
project identically (sync_contract.project) from the product contract and from
the committed slice. Drift outside the scopes is ignored; the release sync owns it.

pair.json records the product commit, the branch it was resolved from, the
sha256 of the product swagger.json, tools.generated.json and tools.yaml, the
committed slice's sha256 and x-contract-sources record, the live coverage table
(sdkgen/contracts/epoch-live-coverage.yaml, which must name exactly the epoch-group
operations), and the outcome. It is written even when the check fails. `--extra-json` merges a JSON object (the E2E
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
import sync_scoped_contract
import yaml
from generator.catalog import CatalogError

ROOT = sync_contract.ROOT
SLICE = sync_contract.OUT
CATALOG = sync_contract.CATALOG
COVERAGE = ROOT / "sdkgen" / "contracts" / "epoch-live-coverage.yaml"
BACKEND_VERSION = sync_contract.VERSION_FILE
PRODUCT_REPOSITORY = "future-agi/future-agi"
SWAGGER = sync_scoped_contract.SWAGGER
MCP = sync_scoped_contract.MCP
TOOLS_YAML = sync_scoped_contract.TOOLS_YAML
SCOPES = tuple(sorted(sync_scoped_contract.SCOPES))
FULL_SHA = re.compile(r"[0-9a-f]{40}")


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


def _git(product: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(product), *args])


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def check(product: Path, sha: str) -> tuple[list[str], dict]:
    """(problems, facts) for the committed slice and catalog at product commit `sha`.

    Raises only when the inputs cannot be read; a mismatch is a problem, and the facts
    (hashes, tool counts, the committed record) are returned either way."""
    head = _git(product, "rev-parse", "HEAD").decode().strip()
    if head != sha:
        raise ValueError(f"product checkout is at {head}, not {sha}")
    raw = {path: _git(product, "show", f"{sha}:{path}") for path in (SWAGGER, MCP, TOOLS_YAML)}
    slice_raw = SLICE.read_bytes()
    catalog_raw = CATALOG.read_bytes()
    product_spec = json.loads(raw[SWAGGER])
    manifest = json.loads(raw[MCP])
    committed = json.loads(slice_raw)
    entries = yaml.safe_load(catalog_raw)["operations"]
    facts = {
        "hashes": {
            "openapi_sha256": _sha256(raw[SWAGGER]),
            "mcp_sha256": _sha256(raw[MCP]),
            "tools_yaml_sha256": _sha256(raw[TOOLS_YAML]),
            "sdk_slice_sha256": _sha256(slice_raw),
            "sdk_catalog_sha256": _sha256(catalog_raw),
        },
        "mcp": {"tool_count": manifest.get("tool_count"), "tool_names_sha256": manifest.get("tool_names_sha256")},
        "contract_sources": committed.get("x-contract-sources"),
    }
    problems = []
    try:
        _names, in_scope, _unscoped = sync_scoped_contract.check_scopes(
            product_spec, raw[SWAGGER], manifest, raw[TOOLS_YAML], entries)
    except (ValueError, CatalogError, KeyError, TypeError, yaml.YAMLError) as exc:
        problems.append(f"scoped catalog check: {exc}")
        in_scope = None
    if in_scope is not None:
        facts["scope"] = {scope: sorted(entry["id"] for entry in in_scope[scope]) for scope in SCOPES}
        for scope in SCOPES:
            problems += compare_projection(product_spec, committed, in_scope[scope], scope)
    coverage, coverage_problems = live_coverage(entries)
    facts["live_coverage"] = coverage
    problems += coverage_problems
    return problems, facts


BUCKETS = {"a", "b", "c"}


def live_coverage(entries: list) -> tuple[dict | None, list[str]]:
    """The committed live coverage table, and what is wrong with it: it must name exactly
    the catalog's epoch-group operations, each in bucket a, b or c; a b entry carries the
    "refusal-only until PR2 <tracking>" status and a c entry its reason."""
    try:
        table = yaml.safe_load(COVERAGE.read_text())
    except (OSError, yaml.YAMLError) as exc:
        return None, [f"live coverage: cannot read {COVERAGE.name}: {exc}"]
    if not isinstance(table, dict) or not isinstance(table.get("operations"), dict):
        return None, [f"live coverage: {COVERAGE.name} has no operations mapping"]
    tracking = table.get("tracking", "")
    operations = table["operations"]
    epoch = {
        entry["id"]
        for entry in entries
        if isinstance(((entry.get("surfaces") or {}).get("mcp")), dict) and entry["surfaces"]["mcp"].get("group") == "epoch"
    }
    problems = []
    if set(operations) != epoch:
        missing, extra = sorted(epoch - set(operations)), sorted(set(operations) - epoch)
        problems.append(f"live coverage: table differs from the epoch-group catalog (missing {missing}, extra {extra})")
    for op, row in sorted(operations.items()):
        bucket = (row or {}).get("bucket")
        if bucket not in BUCKETS:
            problems.append(f"live coverage: {op} has bucket {bucket!r}, not a, b or c")
        elif bucket == "b" and row.get("status") != f"refusal-only until PR2 {tracking}":
            problems.append(f"live coverage: {op} is in bucket b without the status 'refusal-only until PR2 {tracking}'")
        elif bucket == "c" and not row.get("reason"):
            problems.append(f"live coverage: {op} is in bucket c without a reason")
    counts = {bucket: sum(1 for row in operations.values() if (row or {}).get("bucket") == bucket) for bucket in sorted(BUCKETS)}
    return {"tracking": tracking, "counts": counts, "operations": operations}, problems


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
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
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
