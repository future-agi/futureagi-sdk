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


def sync(source: Path) -> str:
    spec = json.loads(source.read_text())
    catalog = yaml.safe_load(CATALOG.read_text())

    paths: dict = {}
    for entry in catalog["operations"]:
        method = entry["operation"]["method"].lower()
        path = entry["operation"]["path"]
        item = spec["paths"][path]
        sliced = paths.setdefault(path, {})
        if "parameters" in item:
            sliced["parameters"] = item["parameters"]
        sliced[method] = item[method]

    # Pull in every definition reachable from the selected operations.
    wanted: set[str] = set()
    _refs(paths, wanted)
    done: set[str] = set()
    while wanted - done:
        name = (wanted - done).pop()
        done.add(name)
        _refs(spec["definitions"][name], wanted)

    out = {
        "swagger": spec["swagger"],
        "info": spec["info"],
        "securityDefinitions": spec.get("securityDefinitions", {}),
        "security": spec.get("security", []),
        "x-source-sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "paths": dict(sorted(paths.items())),
        "definitions": {name: spec["definitions"][name] for name in sorted(done)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    return f"wrote {OUT.relative_to(ROOT)}: {len(paths)} paths, {len(done)} definitions"


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy the catalog's slice of the monorepo contract into contracts/.")
    parser.add_argument("source", help="path to future-agi/api_contracts/openapi/swagger.json")
    parser.add_argument("--backend-version", help="backend release tag (vX.Y.Z) to record in contracts/BACKEND_VERSION")
    args = parser.parse_args()
    if args.backend_version and not re.fullmatch(r"v\d+\.\d+\.\d+", args.backend_version):
        parser.error("--backend-version must look like v1.54.0")

    print(sync(Path(args.source)))
    if args.backend_version:
        VERSION_FILE.write_text(args.backend_version + "\n")
        print(f"wrote {VERSION_FILE.relative_to(ROOT)}: {args.backend_version}")


if __name__ == "__main__":
    main()
