"""Check python/tests/gateway/port_manifest.json, the map of agentcc 1.0's 789 test ids.

    PYTHONPATH=python python scripts/gateway/check_port_manifest.py                 # structure + collection
    PYTHONPATH=python python scripts/gateway/check_port_manifest.py --require-signed  # release gate

Every one of the 789 ids at agent-command-center-sdk the recorded source maps to a
test here, to ``shim:<id>`` (it stays with the S-bucket code in the agentcc 2.0
package), or to ``dropped`` (only S-bucket or bug-asserting tests, each with a reason
and a reviewer record). An id with no entry fails. ``--require-signed`` also fails while
any drop lacks its reviewer record; python/tests/gateway/unit/test_port_manifest.py runs
the rest in the CI line.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "python" / "tests" / "gateway" / "port_manifest.json"
UNIT = "python/tests/gateway/unit"
KINDS = {"same", "renamed", "edited", "shim", "dropped"}
COUNT = 789
# A shim entry's reason names the bucket that keeps the test in the agentcc 2.0
# compatibility package.
SHIM_REASON = "shim-only"


def load(path: Path = MANIFEST) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collected_ids() -> set[str]:
    """Test ids under python/tests/gateway/unit, as repo-relative node ids."""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "python")}
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
            UNIT,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    ids = set()
    for line in out.stdout.splitlines():
        if "::" not in line:
            continue
        node = line.strip()
        # pytest prints ids relative to its rootdir (python/ holds the ini file)
        ids.add(node if node.startswith("python/") else f"python/{node}")
    if out.returncode != 0 or not ids:
        raise RuntimeError(
            f"collection failed ({out.returncode}): {out.stderr[-2000:]}"
        )
    return ids


def _reviewer_ok(reviewer: Any) -> bool:
    return (
        isinstance(reviewer, dict)
        and all(
            isinstance(reviewer.get(k), str) and reviewer[k].strip()
            for k in ("by", "record", "verdict")
        )
        and set(reviewer) == {"by", "record", "verdict"}
        and re.fullmatch(r"review-[a-z][a-z0-9-]{2,}", reviewer["record"]) is not None
    )


def problems(
    manifest: dict[str, Any], collected: set[str] | None, require_signed: bool
) -> list[str]:
    out: list[str] = []
    entries = manifest["entries"]
    olds = [e["old"] for e in entries]
    source = manifest["source"]
    if len(olds) != COUNT or source.get("count") != COUNT:
        out.append(
            f"{len(olds)} entries, the source names {source.get('count')}; want {COUNT}"
        )
    dupes = [o for o, n in collections.Counter(olds).items() if n > 1]
    if dupes:
        out.append(f"duplicate old ids: {dupes[:5]}")
    digest = hashlib.sha256(("\n".join(olds) + "\n").encode()).hexdigest()
    if digest != source.get("ids_sha256"):
        out.append("the old ids differ from the recorded list (ids_sha256)")
    for e in entries:
        old, kind, to = e["old"], e.get("kind"), e.get("to")
        where = f"{old}: "
        if kind not in KINDS:
            out.append(where + f"kind {kind!r}")
            continue
        if not old.startswith("tests/test_"):
            out.append(where + "old id is not an agentcc sdk/python/tests id")
        if kind in {"same", "renamed", "edited"}:
            if not isinstance(to, str) or not to.startswith(f"{UNIT}/"):
                out.append(where + f"target {to!r}")
            elif collected is not None and to not in collected:
                out.append(where + f"target {to} is not a collected test")
            if kind == "same" and to != f"{UNIT}/{old[len('tests/'):]}":
                out.append(where + "'same' must keep the file, class and name")
            if kind == "renamed" and not e.get("note"):
                out.append(where + "a rename says why")
            if kind == "edited" and not e.get("edits"):
                out.append(where + "an edit describes its retained changes")
        elif kind == "shim":
            if to != f"shim:{old}" or SHIM_REASON not in (e.get("reason") or ""):
                out.append(
                    where + "a shim entry is 'shim:<old id>' with a shim-only reason"
                )
        elif kind == "dropped":
            if to is not None or not (e.get("reason") or "").strip():
                out.append(where + "a drop has no target and gives its reason")
            reviewer = e.get("reviewer")
            if reviewer is not None and not _reviewer_ok(reviewer):
                out.append(where + "reviewer record needs by, record (review name) and verdict")
            if require_signed and not _reviewer_ok(reviewer):
                out.append(where + "drop not signed")
    return out


def summary(manifest: dict[str, Any]) -> dict[str, int]:
    return dict(collections.Counter(e["kind"] for e in manifest["entries"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--require-signed", action="store_true")
    parser.add_argument(
        "--no-collect", action="store_true", help="skip the pytest collection check"
    )
    args = parser.parse_args(argv)
    manifest = load()
    collected = None if args.no_collect else collected_ids()
    found = problems(manifest, collected, args.require_signed)
    print(f"port manifest: {summary(manifest)}; problems: {len(found)}")
    for line in found[:50]:
        print("  " + line)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
