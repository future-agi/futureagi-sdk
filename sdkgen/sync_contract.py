"""Copy the slice of the monorepo contract that the catalog uses into contracts/.

In production the SDK repo would pull the whole (converted) contract from the
monorepo. The POC keeps a small slice so it is easy to read and diff.

    python sdkgen/sync_contract.py /path/to/future-agi/api_contracts/openapi/swagger.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "sdkgen" / "catalog" / "operations.yaml"
OUT = ROOT / "sdkgen" / "contracts" / "swagger.json"


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


def main(source: str) -> None:
    spec = json.loads(Path(source).read_text())
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
        "x-source-sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        "paths": dict(sorted(paths.items())),
        "definitions": {name: spec["definitions"][name] for name in sorted(done)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(paths)} paths, {len(done)} definitions")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
