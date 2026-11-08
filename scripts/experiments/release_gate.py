#!/usr/bin/env python3
"""The experiments options gate: fail when an offered option's real e2e rows are not all GREEN.

    python scripts/experiments/release_gate.py --truth ../e2e/truth/truth.json [--options FILE] [--json]

Reads ``python/fi/experiments/_options.yaml`` (every offered option → its rows) and the e2e truth
table (``{"rows": {ROW: "GREEN" | "RED" | "BLOCKED" | "NOT_RUN"}}``). Exit 0 when every row of
every option is GREEN; exit 1 otherwise, listing each option that is not ready with its rows'
statuses (a row the table does not have is ``NOT_RECORDED``). Exit 2 on unreadable input.
For a retained truth table with older row names, pass ``--row-map FILE`` containing
its explicit one-to-one old-to-public name mapping. Verdicts are never inferred;
alias collisions fail, and missing required rows still fail closed.

An option under ``holds:`` in the options file is not ready whatever its rows say, until the hold is
lifted: its rows' GREEN is known not to be evidence yet (evaluation regression's gate passes or
fails by a per-call rate, and the rate gate awaits a ruling). It is listed as ``HOLD`` with its reason.
A hold must name an option of the file (exit 2 otherwise).

This is the ship gate of API design section item 9 ("an option appears in the drawer, the docs, --help
and the released signature only when all its section rows are GREEN"). It is not the run-comparison
"release gate" of ``experiment_runs.compare`` (scripts/validate-generated-release-gate.py).
It needs PyYAML (a dev dependency); it makes no network call.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OPTIONS = ROOT / "python" / "fi" / "experiments" / "_options.yaml"


def load_options(path: Path) -> dict[str, list[str]]:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    options = data.get("options")
    if not isinstance(options, Mapping) or not options:
        raise ValueError(f"{path} has no options mapping")
    return {str(k): [str(r) for r in (v or [])] for k, v in options.items()}


def load_holds(path: Path) -> dict[str, str]:
    """``holds:`` option → why it is held (empty when the file has none)."""
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    holds = data.get("holds") or {}
    if not isinstance(holds, Mapping):
        raise ValueError(f"{path}: holds is not a mapping")
    options = load_options(path)
    unknown = sorted(str(k) for k in holds if str(k) not in options)
    if unknown:
        raise ValueError(f"{path}: holds name options the file does not list: {', '.join(unknown)}")
    return {str(k): str(v).strip() for k, v in holds.items()}


def load_truth(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows") if isinstance(data, Mapping) else None
    if not isinstance(rows, Mapping):
        raise ValueError(f"{path} has no rows mapping")
    return {str(k): str(v) for k, v in rows.items()}


def evaluate(options: Mapping[str, list[str]], truth: Mapping[str, str],
             holds: Mapping[str, str] | None = None) -> dict[str, Any]:
    holds = dict(holds or {})
    blocked: dict[str, dict[str, str]] = {}
    for option, rows in options.items():
        if not rows:
            blocked[option] = {"(no rows)": "ORPHAN"}
            continue
        statuses = {row: truth.get(row, "NOT_RECORDED") for row in rows}
        if any(s != "GREEN" for s in statuses.values()):
            blocked[option] = {r: s for r, s in statuses.items() if s != "GREEN"}
        if option in holds:
            blocked.setdefault(option, {})["(hold)"] = "HOLD: " + holds[option]
    return {"options": len(options), "ready": len(options) - len(blocked), "blocked": blocked,
            "held": {o: holds[o] for o in sorted(holds) if o in options}, "passed": not blocked}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--truth", required=True, type=Path, help="e2e/truth/truth.json")
    parser.add_argument("--options", type=Path, default=DEFAULT_OPTIONS)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--row-map", type=Path,
                        help="explicit legacy-to-public row mapping retained with the truth table")
    args = parser.parse_args(argv)
    try:
        truth = load_truth(args.truth)
        if args.row_map:
            # Load beside this script even when a test imports it by absolute path.
            import runpy
            migration = runpy.run_path(str(Path(__file__).with_name("truth_rows.py")))
            mapping = migration["load_row_map"](args.row_map)
            truth = migration["migrate_rows"](truth, mapping)
        report = evaluate(load_options(args.options), truth, load_holds(args.options))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(f"{report['ready']} of {report['options']} options have every row GREEN")
        for option, rows in sorted(report["blocked"].items()):
            print(f"  NOT READY  {option}: " + ", ".join(f"{r} {s}" for r, s in rows.items()))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
