"""Copy the slice of the monorepo contract that the catalog uses into contracts/.

    python sdkgen/sync_contract.py /path/to/future-agi/api_contracts/openapi/swagger.json
    python sdkgen/sync_contract.py swagger.json --backend-version v1.54.0   # also pin the release

Only the operations the catalog names, plus every definition they reach, are
kept, so the slice is small enough to read and its diff shows the API change.
`--backend-version` records the backend release the slice came from in
contracts/BACKEND_VERSION; .github/workflows/e2e.yml tests against that image.
The monorepo's sdk-sync workflow runs both on every backend release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "sdkgen" / "catalog" / "operations.yaml"
OUT = ROOT / "sdkgen" / "contracts" / "swagger.json"
VERSION_FILE = ROOT / "sdkgen" / "contracts" / "BACKEND_VERSION"


def _refs(node, found: set[str]) -> None:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/definitions/"):
            found.add(ref.rsplit("/", 1)[-1])
        for value in node.values():
            _refs(value, found)
    elif isinstance(node, list):
        for value in node:
            _refs(value, found)


def _project(spec: dict, entries: list[dict]) -> tuple[dict, dict]:
    """Keep the selected HTTP operations, inherited parameters and their closed model graph."""
    paths: dict = {}
    for entry in entries:
        method = entry["operation"]["method"].lower()
        path = entry["operation"]["path"]
        item = spec["paths"][path]
        selected = paths.setdefault(path, {})
        if "parameters" in item:
            selected["parameters"] = item["parameters"]
        selected[method] = item[method]
    wanted: set[str] = set()
    _refs(paths, wanted)
    definitions: dict = {}
    while wanted - definitions.keys():
        name = (wanted - definitions.keys()).pop()
        definitions[name] = spec["definitions"][name]
        _refs(definitions[name], wanted)
    return paths, definitions


def _union(left: dict, right: dict, what: str) -> dict:
    conflicts = sorted(k for k in left.keys() & right.keys() if left[k] != right[k])
    if conflicts:
        raise SystemExit(f"Skills and baseline {what} disagree: {', '.join(conflicts)}")
    return {**left, **right}


def sync(source: Path, *, baseline: dict | None = None, baseline_hash: str | None = None) -> str:
    spec = json.loads(source.read_text())
    catalog = yaml.safe_load(CATALOG.read_text())

    # Fail closed, and say why, when the backend dropped or moved an endpoint the
    # SDK exposes: that is a breaking change for SDK users and needs a person to
    # retire or remap the catalog entry (sdkgen/catalog/operations.yaml), never a
    # silent sync. sdk-sync in the monorepo surfaces this message as the job error.
    gone = [
        f"{entry['id']}: {entry['operation']['method'].upper()} {entry['operation']['path']}"
        for entry in catalog["operations"]
        if entry["operation"]["method"].lower()
        not in spec["paths"].get(entry["operation"]["path"], {})
    ]
    if gone:
        raise SystemExit(
            "the backend contract no longer has these catalog operations (a breaking "
            "change; retire or remap them in sdkgen/catalog/operations.yaml before "
            "syncing):\n  " + "\n  ".join(gone)
        )

    entries = catalog["operations"]
    schemes = spec.get("securityDefinitions", {})
    if baseline is None:
        paths, definitions = _project(spec, entries)
    else:
        # This is a scoped Preview sync, not an update to the released backend pin.
        # Compare both public path and SDK namespace, so a typo cannot silently
        # move an unrelated operation into either provenance group.
        skills, existing = [], []
        for entry in entries:
            is_skill = entry["operation"]["path"].startswith("/model-hub/skills/")
            if is_skill != (entry["id"].split(".")[0] in {
                "skills", "skill_consumption", "contexts", "context_credentials"
            }):
                raise SystemExit(f"Skills source classification mismatch: {entry['id']}")
            (skills if is_skill else existing).append(entry)
        old_paths, old_defs = _project(baseline, existing)
        new_paths, new_defs = _project(spec, skills)
        paths = _union(old_paths, new_paths, "routes")
        definitions = _union(old_defs, new_defs, "definitions")
        schemes = _union(baseline.get("securityDefinitions", {}), schemes, "auth schemes")
        if spec.get("security", []) != baseline.get("security", []) or spec["swagger"] != baseline["swagger"]:
            raise SystemExit("baseline default auth or OpenAPI dialect differs from the product")

    out = {
        "swagger": spec["swagger"],
        "info": spec["info"],
        "securityDefinitions": schemes,
        "security": spec.get("security", []),
        "x-source-sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "paths": dict(sorted(paths.items())),
        "definitions": dict(sorted(definitions.items())),
    }
    if baseline is not None:
        out["x-skills-only-baseline-sha256"] = baseline_hash
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    return f"wrote {OUT.relative_to(ROOT)}: {len(paths)} paths, {len(definitions)} definitions"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy the catalog's slice of the monorepo contract into contracts/."
    )
    parser.add_argument(
        "source", help="path to future-agi/api_contracts/openapi/swagger.json"
    )
    parser.add_argument(
        "--backend-version",
        help="backend release tag (vX.Y.Z) to record in contracts/BACKEND_VERSION",
    )
    parser.add_argument("--backend-commit", help="exact product commit for an unreleased contract")
    parser.add_argument("--mcp-tools", type=Path, help="tools.generated.json from that same product commit")
    parser.add_argument("--skills-baseline-sdk", help="full SDK commit supplying unchanged non-Skills contracts")
    args = parser.parse_args()
    if args.skills_baseline_sdk and (not re.fullmatch(r"[0-9a-f]{40}", args.skills_baseline_sdk)
                                     or not args.backend_commit or args.backend_version):
        parser.error("--skills-baseline-sdk needs a full SDK SHA and a commit-pinned (not release) sync")
    if bool(args.backend_commit) != bool(args.mcp_tools):
        parser.error("--backend-commit and --mcp-tools must be supplied together")
    if args.backend_commit and not re.fullmatch(r"[0-9a-f]{40}", args.backend_commit):
        parser.error("--backend-commit must be a full lowercase commit SHA")
    if args.backend_version and not re.fullmatch(
        r"v\d+\.\d+\.\d+", args.backend_version
    ):
        parser.error("--backend-version must look like v1.54.0")

    tools_snapshot = OUT.parent / "mcp-tools.json"
    provenance = OUT.parent / "SOURCE.json"
    # Validate all supplied inputs before updating the contract slice.
    tools = json.loads(args.mcp_tools.read_bytes()) if args.mcp_tools else None
    if tools is not None:
        names = sorted(tool["name"] for tool in tools["tools"])
        if len(set(names)) != len(names) or not all(isinstance(n, str) and n for n in names):
            parser.error("MCP source has invalid or duplicate names")
    baseline_raw = None
    baseline_hash = None
    if args.skills_baseline_sdk:
        baseline_raw = subprocess.check_output([
            "git", "-C", str(ROOT), "show", args.skills_baseline_sdk + ":sdkgen/contracts/swagger.json"
        ])
        baseline_hash = hashlib.sha256(baseline_raw).hexdigest()
    print(sync(Path(args.source), baseline=json.loads(baseline_raw) if baseline_raw else None,
               baseline_hash=baseline_hash))
    if tools is not None:
        metadata = {
            "backend_commit": args.backend_commit,
            "openapi_sha256": hashlib.sha256(Path(args.source).read_bytes()).hexdigest(),
            "mcp_sha256": hashlib.sha256(args.mcp_tools.read_bytes()).hexdigest(),
        }
        if baseline_raw is not None:
            metadata["non_skills_sdk_commit"] = args.skills_baseline_sdk
            metadata["non_skills_slice_sha256"] = baseline_hash
        provenance.write_text(json.dumps(metadata, indent=2) + "\n")
        tools_snapshot.write_text(json.dumps({
            "x-source-sha256": metadata["mcp_sha256"],
            "tools": [{"name": name} for name in names],
        }, indent=2) + "\n")
    else:
        # A later released sync must not retain a different commit's MCP list.
        tools_snapshot.unlink(missing_ok=True)
        provenance.unlink(missing_ok=True)
    if args.backend_version:
        VERSION_FILE.write_text(args.backend_version + "\n")
        print(f"wrote {VERSION_FILE.relative_to(ROOT)}: {args.backend_version}")


if __name__ == "__main__":
    main()
