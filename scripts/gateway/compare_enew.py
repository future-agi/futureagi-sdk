"""Compare an fi.gateway (E-NEW) recording with the agentcc 1.0.0 golden.

    PYTHONPATH=python python scripts/gateway/compare_enew.py --new <recording dir> [--report out.json]
    PYTHONPATH=python python scripts/gateway/compare_enew.py --record   # record here first (pinned env)

The differences allowed are the shared tests/fixtures/gateway/intended-differences.json
plus the Python port's overlay, python/tests/gateway/intended-differences-py.json.
The port's entries (ids 'D-xx-py' and 'PY-*') live in the shared file once signed
('proven', with a reviewer record) and in the overlay while 'landed' (evidence and test
id filled, reviewer record pending); both cover here, and the report counts how many
still wait for a reviewer. The comparison passes only with 0 unlisted differences,
every port entry covering something and every port rule used. The release gate is the
shared file's rule, under which only 'proven' entries cover, so the report also gives
that strict count ('strict_unlisted'): 0 exactly when no port entry waits for a
reviewer. The parity comparator
(python/tests/gateway/parity/compare.py) does the diffing; a recording is only
meaningful in the golden's pinned environment (Python 3.12,
tests/fixtures/gateway/e-old/constraints-py.txt).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GATEWAY_TESTS = ROOT / "python" / "tests" / "gateway"
FIXTURES = ROOT / "tests" / "fixtures" / "gateway"
GOLDEN = FIXTURES / "golden" / "py-agentcc-1.0.0"
SHARED_FILE = FIXTURES / "intended-differences.json"
OVERLAY = GATEWAY_TESTS / "intended-differences-py.json"
LABEL = "py-agentcc-1.0.0->e-new-py"
COVERING = {"landed", "proven"}
# The Python port's ids: '-py' splits of the shared D-xx work list, 'PY-*' for port
# changes without a D number.
PORT_ID = re.compile(r"D-\d\d[a-z]?-py|PY-[0-9.]+-[a-z0-9-]+")

if str(GATEWAY_TESTS) not in sys.path:
    sys.path.insert(0, str(GATEWAY_TESTS))

from parity.compare import (
    compare_cases,
    covers,
    diff,  # noqa: E402
    load_recording,
    view,
)
from parity.labels import check_label  # noqa: E402


def overlay_entries(path: Path = OVERLAY) -> list[dict[str, Any]]:
    """The port's entries still in the overlay (not yet signed into the shared file)."""
    return json.loads(path.read_text(encoding="utf-8"))["differences"]


def shared_entries() -> list[dict[str, Any]]:
    return json.loads(SHARED_FILE.read_text(encoding="utf-8"))["differences"]


def port_entries(path: Path = OVERLAY) -> list[dict[str, Any]]:
    """Every entry of the Python port: those signed into the shared file, then those
    still in the overlay."""
    signed = [e for e in shared_entries() if PORT_ID.fullmatch(e["id"])]
    return signed + overlay_entries(path)


def merged(
    overlay: list[dict[str, Any]], *, landed_covers: bool = True
) -> list[dict[str, Any]]:
    """The shared entries plus the overlay's; the overlay's landed entries count as
    covering unless *landed_covers* is false (the shared file's strict rule: only
    'proven' entries cover)."""
    shared = shared_entries()
    clash = {e["id"] for e in shared} & {e["id"] for e in overlay}
    if clash:
        raise ValueError(f"overlay ids must be new: {sorted(clash)}")
    if not landed_covers:
        return shared + overlay
    as_proven = [
        {**e, "status": "proven"} for e in overlay if e.get("status") in COVERING
    ]
    return shared + as_proven


def unused_rules(
    golden: dict[str, Any], new: dict[str, Any], overlay: list[dict[str, Any]]
) -> list[str]:
    used: dict[str, set[int]] = {e["id"]: set() for e in overlay}
    for d in diff(view(golden), view(new)):
        for e in overlay:
            for i, rule in enumerate(e["match"]):
                if covers(rule, d):
                    used[e["id"]].add(i)
    return [
        f"{e['id']}: rule {i} {e['match'][i]['path']}"
        for e in overlay
        for i in range(len(e["match"]))
        if i not in used[e["id"]]
    ]


def compare_new(new_dir: Path, overlay_path: Path = OVERLAY) -> dict[str, Any]:
    check_label(LABEL, GOLDEN, new_dir)
    overlay = overlay_entries(overlay_path)
    port = port_entries(overlay_path)
    golden, new = load_recording(GOLDEN), load_recording(new_dir)
    report = compare_cases(golden["cases"], new["cases"], merged(overlay), LABEL)
    report["unused_overlay_rules"] = unused_rules(golden["cases"], new["cases"], port)
    ids = {e["id"] for e in port}
    report["unobserved_overlay"] = sorted(set(report["unobserved_proven"]) & ids)
    report["awaiting_reviewer"] = sorted(
        e["id"] for e in port if e.get("status") == "landed"
    )
    report["ok"] = (
        report["ok"]
        and not report["unused_overlay_rules"]
        and not report["unobserved_overlay"]
    )
    strict = compare_cases(
        golden["cases"], new["cases"], merged(overlay, landed_covers=False), LABEL
    )
    report["strict_unlisted"] = len(strict["unlisted"])
    report["strict_ok"] = strict["ok"]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--new", type=Path, help="an fi.gateway recording directory")
    source.add_argument(
        "--record", action="store_true", help="record fi.gateway here first"
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args(argv)
    if args.record:
        from parity.record import record

        new_dir = Path(tempfile.mkdtemp(prefix="e-new-py-"))
        record("fi.gateway", new_dir)
    else:
        new_dir = args.new
    report = compare_new(new_dir)
    if args.report:
        args.report.write_text(
            json.dumps(report, indent=1, sort_keys=True, default=str) + "\n"
        )
    print(
        f"{LABEL}: ok={report['ok']} unlisted={len(report['unlisted'])} "
        f"covered={sum(report['covered'].values())} in {len(report['covered'])} entries; "
        f"unused overlay rules={len(report['unused_overlay_rules'])}; "
        f"awaiting a reviewer record: {len(report['awaiting_reviewer'])} entries"
    )
    print(
        f"  strict rule (only signed entries cover; the release gate): "
        f"ok={report['strict_ok']} unlisted={report['strict_unlisted']}"
    )
    for d in report["unlisted"][: args.limit]:
        print(
            f"  UNLISTED {d['kind']} {d['path']}: {str(d['old'])[:80]} -> {str(d['new'])[:80]}"
        )
    for line in report["unused_overlay_rules"][: args.limit]:
        print(f"  UNUSED {line}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
