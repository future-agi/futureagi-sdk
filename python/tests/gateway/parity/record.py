"""Record the case catalog against one target module root.

    cd python/tests/gateway && python -m parity.record --root agentcc --out <dir>

Writes ``<dir>/<area>.json`` (one file per catalog area) and ``<dir>/index.json``
(the environment, every case id, and each area file's sha256). Two runs in the
same environment must be byte-identical; ``fetch-artifacts.sh``'s sibling
``record-e-old.sh`` runs it twice in fresh processes, the second from another
checkout and venv path, and compares with ``cmp``. A file that would carry a
local path is refused, not written (``_hygiene.py``).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata as md
import os
import platform
import sys
from pathlib import Path
from typing import Any

from ._hygiene import recorder_roots, write_checked
from ._runner import ENV_PREFIXES, run_case
from .cases import all_cases

DEPS = (
    "httpx",
    "httpcore",
    "pydantic",
    "pydantic-core",
    "anyio",
    "typing-extensions",
    "jsonschema",
    "tiktoken",
    "agentcc",
    "futureagi",
)
FORMAT = 1


def _version(dist: str) -> str | None:
    try:
        return md.version(dist)
    except md.PackageNotFoundError:
        return None


def library_environment() -> dict[str, Any]:
    """The interpreter and libraries this process records with (no target import)."""
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "deps": {d: _version(d) for d in DEPS},
    }


def environment(root: str) -> dict[str, Any]:
    module = importlib.import_module(root)
    return {
        "root": root,
        "module_version": getattr(module, "__version__", None),
        **library_environment(),
    }


def _import_clean(root: str) -> None:
    saved = dict(os.environ)
    for key in [k for k in os.environ if k.startswith(ENV_PREFIXES)]:
        del os.environ[key]
    try:
        importlib.import_module(root)
        importlib.import_module("httpx")
    finally:
        os.environ.clear()
        os.environ.update(saved)


def record(root: str, out: Path, only: str | None = None) -> dict[str, Any]:
    _import_clean(root)
    by_area: dict[str, dict[str, Any]] = {}
    ids: list[str] = []
    for case in all_cases():
        if only and not case.id.startswith(only):
            continue
        for mode in case.modes:
            key = f"{case.id}[{mode}]"
            ids.append(key)
            by_area.setdefault(case.area, {})[key] = run_case(case, root, mode)
    out.mkdir(parents=True, exist_ok=True)
    roots = recorder_roots(out)
    files = {}
    for area, data in sorted(by_area.items()):
        text = write_checked(
            out / f"{area}.json", {"format": FORMAT, "area": area, "cases": data}, roots
        )
        files[f"{area}.json"] = hashlib.sha256(text.encode()).hexdigest()
    index = {
        "format": FORMAT,
        "environment": environment(root),
        "case_ids": ids,
        "files": files,
    }
    write_checked(out / "index.json", index, roots)
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root", required=True, help="agentcc (E-OLD, E-SHIM) or fi.gateway (E-NEW)"
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--only", help="record only case ids with this prefix")
    args = parser.parse_args(argv)
    index = record(args.root, args.out, args.only)
    print(
        f"recorded {len(index['case_ids'])} case runs in {len(index['files'])} areas -> {args.out}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
