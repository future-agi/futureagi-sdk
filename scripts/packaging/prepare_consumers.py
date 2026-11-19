#!/usr/bin/env python3
"""Prepare offline consumer requirements and verify public wheels against poetry.lock.

Run only during VM preparation. Each downloaded archive remains in its own
wheelhouse, never extracted here. Companion distributions are installed by the
matrix, not by the common dependency substrate, so install order is meaningful.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import tomllib


def prepare(lock_path, output):
    lock = tomllib.loads(lock_path.read_text())
    expected = {f["file"]: f["hash"] for package in lock["package"] for f in package["files"]}
    evidence = []
    for wheel in sorted((output / "dependencies").glob("*.whl")):
        digest = "sha256:" + hashlib.sha256(wheel.read_bytes()).hexdigest()
        # Explicitly pinned runner tools are not runtime requirements.
        tool = wheel.name.startswith("pip-24.3.1-")
        if not tool and expected.get(wheel.name) != digest:
            raise ValueError(f"wheel does not match poetry.lock: {wheel.name}")
        evidence.append({"file": wheel.name, "digest": digest, "lock_verified": not tool})
    excluded = re.compile(r"^(fi-instrumentation-otel|traceai[-_]|agent-learning-kit|agentcc|futureagi)", re.I)
    lines = (output / "requirements-available.txt").read_text().splitlines()
    # Exported without hashes: each pinned requirement occupies one line.
    (output / "requirements.txt").write_text("\n".join(line for line in lines if not excluded.match(line)) + "\n")
    (output / "dependency-digests.json").write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    prepare(*map(Path, sys.argv[1:]))
