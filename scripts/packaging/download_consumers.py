#!/usr/bin/env python3
"""Download exact public runtime wheels, recording unavailable binary inputs explicitly.

Each requirement is downloaded into its own new directory. No sdist fallback is
allowed. Missing inputs prevent import-matrix qualification, not diagnostic work.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

from packaging.requirements import Requirement


def main(output):
    downloads = output / "downloads"
    downloads.mkdir()
    missing, available = [], []
    for index, line in enumerate((output / "requirements-all.txt").read_text().splitlines()):
        if not line.strip() or line.startswith("#"):
            continue
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate():
            continue
        if not str(requirement.specifier).startswith("==") or requirement.url:
            raise ValueError(f"requirement is not an exact registry pin: {requirement.name}")
        destination = downloads / str(index)
        destination.mkdir()
        command = [sys.executable, "-I", "-m", "pip", "download", "--no-deps", "--only-binary=:all:",
                   "--index-url", "https://pypi.org/simple", "--dest", str(destination), line]
        proc = subprocess.run(command, text=True, capture_output=True, timeout=120)
        (destination / "download.log").write_text(proc.stdout + proc.stderr)
        if proc.returncode:
            missing.append({"requirement": line, "reason": "public pinned wheel download failed",
                            "log": str(destination / "download.log")})
        else:
            available.append(line)
            for wheel in destination.glob("*.whl"):
                shutil.copyfile(wheel, output / "dependencies" / wheel.name)
    (output / "requirements-available.txt").write_text("\n".join(available) + "\n")
    (output / "dependency-status.json").write_text(json.dumps({"missing": missing}, indent=2) + "\n")
    print(json.dumps({"available": len(available), "missing": missing}))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
