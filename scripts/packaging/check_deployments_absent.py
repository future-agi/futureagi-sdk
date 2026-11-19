#!/usr/bin/env python3
"""Reject deployment surfaces in release wheels, sdists and npm tarballs.

Usage: python check_deployments_absent.py WHEEL SDIST NPM_TARBALL
Archives are read in memory, never extracted or imported. Consumer import and
CLI checks complement this inventory gate; neither replaces the other.
"""
from __future__ import annotations

import configparser
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile
import zipfile


API_REFERENCE = re.compile(
    r"\bfi[./]deployments\b|\bclient\.deployments\b|"
    r"@future-agi/sdk/deployments\b|\bfutureagi\s+deployments\b|"
    r"futureagi\[deployments\]|`(?:Async)?Deployments?`"
)


def _namespace(path: str) -> bool:
    return any(part == "deployments" or part.startswith("deployments.")
               for part in PurePosixPath(path).parts)


def _safe_names(names: list[str]) -> None:
    if len(set(names)) != len(names):
        raise ValueError("Duplicate archive members")
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe archive member: {name}")


def _read(path: Path) -> dict[str, bytes]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            _safe_names(archive.namelist())
            return {item.filename: archive.read(item) for item in archive.infolist()
                    if not item.is_dir()}
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        _safe_names([item.name for item in members])
        if any(item.issym() or item.islnk() for item in members):
            raise ValueError("Archive links are not allowed")
        return {item.name: archive.extractfile(item).read() for item in members if item.isfile()}


def check_files(files: dict[str, bytes], kind: str) -> list[str]:
    """Return every deployment leak in one archive's file inventory."""
    findings: list[str] = []
    for name, content in files.items():
        parts = PurePosixPath(name).parts
        runtime = "fi" in parts if kind != "npm" else "dist" in parts
        if runtime and _namespace(name):
            findings.append(f"deployment module: {name}")
        if name.lower().endswith((".md", ".rst", ".html")):
            if API_REFERENCE.search(content.decode("utf-8", "replace")):
                findings.append(f"deployment API documentation: {name}")
        if name.endswith(".dist-info/entry_points.txt"):
            config = configparser.ConfigParser(interpolation=None)
            config.read_string(content.decode("utf-8"))
            for group in config.sections():
                for key, value in config[group].items():
                    if "deployment" in key.lower() or "fi.deployments" in value:
                        findings.append(f"deployment entry point: {group}.{key}")
        if name.endswith(".dist-info/METADATA"):
            if re.search(rb"(?im)^Provides-Extra:\s*deployments\s*$", content):
                findings.append("deployment-only Python extra")
    if kind == "npm":
        package = json.loads(files["package/package.json"])
        for subpath in package.get("exports", {}):
            if _namespace(subpath) or "*" in subpath:
                findings.append(f"deployment-capable export: {subpath}")
        for versions in package.get("typesVersions", {}).values():
            for subpath in versions:
                if _namespace(subpath) or "*" in subpath:
                    findings.append(f"deployment-capable types mapping: {subpath}")
        for name in package.get("scripts", {}):
            if "deployment" in name.lower():
                findings.append(f"deployment build entry: {name}")
    return findings


def main(wheel: str, sdist: str, tarball: str) -> int:
    findings = []
    for path, kind in ((wheel, "wheel"), (sdist, "sdist"), (tarball, "npm")):
        findings.extend(f"{Path(path).name}: {item}" for item in check_files(_read(Path(path)), kind))
    for item in findings:
        print(item, file=sys.stderr)
    if not findings:
        print("Deployment archive absence: PASS (wheel, sdist, npm)")
    return int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
