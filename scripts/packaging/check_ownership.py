#!/usr/bin/env python3
"""Validate wheel RECORD integrity and exclusive runtime ownership without extraction.

Run with ``python -I check_ownership.py WHEEL [COMPANION ...]``. Each argument
is one distribution in a supported combination. Unknown distributions fail closed.
"""
from __future__ import annotations

import argparse
import base64
import configparser
import csv
import email
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

SOURCE = Path(__file__).resolve().parents[2] / "python/fi/_core/namespace_ownership.py"
spec = importlib.util.spec_from_file_location("namespace_ownership", SOURCE)
ownership = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ownership)


def safe_path(path: str) -> str:
    """Reject noncanonical archive names before deriving installation destinations."""
    p = PurePosixPath(path)
    if not path or p.is_absolute() or ".." in p.parts or "\\" in path or str(p) != path:
        raise ValueError(f"noncanonical wheel path: {path!r}")
    return path


def destination(path: str, stem: str) -> str:
    """Map wheel purelib/platlib spreads to the shared installed path."""
    if path.startswith(stem + ".data/"):
        _, scheme, relative = path.split("/", 2)
        if scheme in {"purelib", "platlib"}:
            return relative
        raise ValueError(f"unsupported wheel data scheme: {scheme}")
    return path


def wheel_record(path: Path) -> dict:
    """Verify every archive member against RECORD, then enforce the ownership manifest."""
    rules = ownership.manifest()
    with zipfile.ZipFile(path) as archive:
        members = [i for i in archive.infolist() if not i.is_dir()]
        names = [safe_path(i.filename) for i in members]
        if len(names) != len(set(names)):
            raise ValueError("duplicate wheel member")
        if any(stat.S_ISLNK(i.external_attr >> 16) for i in members):
            raise ValueError("wheel contains a symlink")
        records = [p for p in names if p.endswith(".dist-info/RECORD")]
        if len(records) != 1:
            raise ValueError("wheel must contain exactly one RECORD")
        record = records[0]
        info = record.rsplit("/", 1)[0]
        stem = info.removesuffix(".dist-info")
        meta = email.message_from_bytes(archive.read(info + "/METADATA"))
        name = ownership.canonical_name(meta.get("Name", ""))
        version = meta.get("Version", "")
        rule = ownership.policy(name, rules)
        if rule is None or not ownership.supported_version(version, rule):
            raise ValueError(f"unsupported distribution: {name} {version}")
        expected_stem = name.replace("-", "_") + "-" + version.replace("-", "_")
        if stem != expected_stem:
            raise ValueError("dist-info directory disagrees with METADATA")
        rows = list(csv.reader(io.StringIO(archive.read(record).decode("utf-8"))))
        if any(len(row) != 3 for row in rows):
            raise ValueError("invalid RECORD row")
        paths = [safe_path(row[0]) for row in rows]
        if len(paths) != len(set(paths)) or set(paths) != set(names):
            raise ValueError("RECORD does not enumerate archive members exactly once")
        payload = set()
        for member, digest, size in rows:
            content = archive.read(member)
            if member == record:
                if digest or size:
                    raise ValueError("RECORD self entry must be unhashed")
            else:
                algorithm, sep, encoded = digest.partition("=")
                if not sep or algorithm not in {"sha256", "sha384", "sha512"}:
                    raise ValueError(f"missing or unsafe RECORD digest: {member}")
                actual = base64.urlsafe_b64encode(hashlib.new(algorithm, content).digest()).rstrip(b"=").decode()
                if actual != encoded or not size.isdigit() or len(content) != int(size):
                    raise ValueError(f"RECORD content mismatch: {member}")
            installed = destination(member, stem)
            if installed in payload:
                raise ValueError(f"duplicate installed path: {installed}")
            payload.add(installed)
            if not member.startswith(info + "/") and not ownership.owns(name, installed, rules):
                raise ValueError(f"unowned runtime path: {name}: {installed}")
        ep_path = info + "/entry_points.txt"
        scripts = []
        if ep_path in names:
            parser = configparser.ConfigParser(interpolation=None)
            parser.optionxform = str
            parser.read_string(archive.read(ep_path).decode())
            scripts = list(parser["console_scripts"]) if parser.has_section("console_scripts") else []
            if set(scripts) & set(rules["forbidden_console_scripts"]):
                raise ValueError("forbidden legacy console script: fi")
        return {"name": name, "version": version, "wheel": path.name,
                "digest": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
                "paths": sorted(payload), "console_scripts": scripts}


def check_combination(paths: list[Path]) -> dict:
    """Fail on any overlapping file or console script in a supported combination."""
    wheels = [wheel_record(p) for p in paths]
    if len({w["name"] for w in wheels}) != len(wheels):
        raise ValueError("duplicate distribution in combination")
    owners = {}
    for wheel in wheels:
        for path in wheel["paths"] + ["console_scripts/" + s for s in wheel["console_scripts"]]:
            if path in owners:
                raise ValueError(f"overlap: {path}: {owners[path]}, {wheel['name']}")
            owners[path] = wheel["name"]
    return {"status": "PASS", "wheels": wheels}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheels", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = check_combination(args.wheels)
    except (ValueError, KeyError, OSError, zipfile.BadZipFile, csv.Error) as exc:
        result = {"status": "FAIL", "error": str(exc)}
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text)
    return int(result["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
