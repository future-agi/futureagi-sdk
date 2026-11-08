#!/usr/bin/env python3
"""Verify run module absence in a built wheel and npm tarball; fail closed on any residue.

Run this on an OFF release tree. Runtime import/client/CLI checks run separately in the
installed consumer so an editable source checkout cannot make an absent module appear.
"""
import argparse
import json
import tarfile
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--tarball", type=Path, required=True)
    parser.add_argument("--tree", type=Path, required=True)
    args = parser.parse_args()
    with zipfile.ZipFile(args.wheel) as wheel:
        files = wheel.namelist()
        assert not any(p.startswith("fi/agents/runs/") for p in files), "run files remain in the wheel"
        entries = [p for p in files if p.endswith(".dist-info/entry_points.txt")]
        assert all("fi.agents.runs" not in wheel.read(p).decode() for p in entries), "run CLI plugin remains"
    with tarfile.open(args.tarball, "r:gz") as package:
        assert not any("/agents/runs/" in p.name for p in package.getmembers()), "run files remain in the tarball"
        manifest_file = package.extractfile("package/package.json")
        assert manifest_file is not None
        manifest = json.load(manifest_file)
        assert "./agents/runs" not in manifest.get("exports", {}), "run subpath remains exported"
        for mappings in manifest.get("typesVersions", {}).values():
            assert not any("agents/runs" in key or any("agents/runs" in target for target in targets)
                           for key, targets in mappings.items()), "run declaration mapping remains"
    docs = [args.tree / "CONVENTIONS.md", args.tree / "README.md", args.tree / "python/README.md", args.tree / "typescript/futureagi/README.md"]
    for path in docs:
        text = path.read_text()
        assert all(token not in text for token in ("client.agents.runs", "fi.agents.runs", "sdk/agents/runs", "futureagi agents runs")), f"run documentation remains in {path.name}"
    print("PASS: run namespace absent from wheel, tarball, entry points, export map and documentation")


if __name__ == "__main__":
    main()
