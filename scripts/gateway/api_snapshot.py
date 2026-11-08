"""Write or check python/tests/gateway/api_snapshot.json, the public surface of fi.gateway.

    PYTHONPATH=python python scripts/gateway/api_snapshot.py --write   # after an intended change
    PYTHONPATH=python python scripts/gateway/api_snapshot.py           # exit 1 if it drifted

The snapshot guards the surface the way wrapper-map guards platform methods: the root's ``__all__`` and public ``dir()``, each public subpackage's ``__all__``,
and the names that are new against agentcc 1.0.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "python" / "tests" / "gateway" / "api_snapshot.json"
GOLDEN_SURFACE = (
    ROOT
    / "tests"
    / "fixtures"
    / "gateway"
    / "golden"
    / "py-agentcc-1.0.0"
    / "surface.json"
)
SUBPACKAGES = (
    "fi.gateway.types",
    "fi.gateway.types.chat",
    "fi.gateway.resources",
    "fi.gateway.callbacks",
    "fi.gateway.testing",
)


def build() -> dict:
    gw = importlib.import_module("fi.gateway")
    old_all = set(
        json.loads(GOLDEN_SURFACE.read_text())["cases"]["surface.all[sync]"]["result"][
            "__all__"
        ]
    )
    snap: dict = {
        "about": "The public surface of fi.gateway (scripts/gateway/api_snapshot.py writes it; "
        "test_gw_d21_config_and_surface.py checks it). A change here is an API change.",
        "fi.gateway": {
            "__all__": sorted(gw.__all__),
            "dir": sorted(n for n in dir(gw) if not n.startswith("_")),
        },
        "new_names": sorted(set(gw.__all__) - old_all),
    }
    for name in SUBPACKAGES:
        mod = importlib.import_module(name)
        snap[name] = {"__all__": sorted(getattr(mod, "__all__", []))}
    return snap


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    current = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if args.write:
        SNAPSHOT.write_text(current)
        return 0
    if SNAPSHOT.read_text() != current:
        print(
            f"{SNAPSHOT} is out of date: run with --write if the change is intended",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
