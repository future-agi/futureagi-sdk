#!/usr/bin/env python3
"""Run inside a consumer interpreter with -I; no checkout imports or network calls."""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import importlib
from importlib import metadata
import json
from pathlib import Path
import socket
import sys


def deny_network(*args, **kwargs):
    raise RuntimeError("consumer probe forbids network access")


def record_integrity():
    """Check every hashed futureagi RECORD entry, including installer-generated scripts."""
    dist = metadata.distribution("futureagi")
    errors = []
    checked = 0
    for entry, recorded, size in csv.reader(io.StringIO(dist.read_text("RECORD") or "")):
        if not recorded:
            continue
        checked += 1
        path = Path(dist.locate_file(entry))
        if not path.is_file():
            errors.append({"kind": "missing", "path": entry})
            continue
        algorithm, expected = recorded.split("=", 1)
        digest = base64.urlsafe_b64encode(hashlib.new(algorithm, path.read_bytes()).digest()).rstrip(b"=").decode()
        if digest != expected or (size and path.stat().st_size != int(size)):
            errors.append({"kind": "changed", "path": entry})
    return {"checked": checked, "errors": errors}


def imports(golden):
    """Check each census entry against its recorded legacy import outcome."""
    failures = {}
    count = 0
    for key, expected in json.loads(golden.read_text())["census"].items():
        module, _, name = key.partition(":")
        try:
            imported = importlib.import_module(module)
            value = imported if name == "*" else getattr(imported, name)
            if value is None:
                raise AssertionError("export is None")
            outcome = "ok"
        except Exception as exc:
            outcome = type(exc).__name__
        wanted = "ok" if expected["ok"] else expected["error"].split(":", 1)[0]
        count += 1
        if outcome != wanted:
            failures[key] = {"expected": wanted, "actual": outcome}
    for module, name in [("fi", "FutureAGIClient"), ("fi", "AsyncFutureAGIClient")]:
        try:
            assert getattr(importlib.import_module(module), name) is not None
        except Exception as exc:
            failures[module + ":" + name] = type(exc).__name__
    return {"count": count, "failures": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["doctor", "integrity", "imports", "residue"])
    parser.add_argument("--golden", type=Path)
    args = parser.parse_args()
    socket.create_connection = deny_network
    socket.socket.connect = deny_network
    socket.getaddrinfo = deny_network
    if args.mode == "doctor":
        from fi._cli.main import main as cli
        return cli(["doctor", "--json", "--offline"])
    if args.mode == "integrity":
        result = record_integrity()
        good = result["checked"] > 0 and not result["errors"]
    elif args.mode == "imports":
        result = imports(args.golden)
        good = not result["failures"]
    else:
        import sysconfig
        root = Path(sysconfig.get_paths()["purelib"]) / "fi"
        remaining = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())
        result = {"remaining_files": remaining}
        good = not remaining
    print(json.dumps(result))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
