"""Regenerate the SDKs and the MCP manifest from the contract + catalog.

    python sdkgen/generate.py                      write every output, scaffold new resources
    python sdkgen/generate.py --check              exit 1 if any output is stale (CI drift check)
    python sdkgen/generate.py --only python mcp    limit to some targets (python, typescript, mcp)

The emitters live in sdkgen/generator/; this file is just the command line.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sdkgen.generator import ROOT, TARGETS, CatalogError, build, scaffolds  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 if generated files are out of date")
    parser.add_argument("--only", nargs="+", choices=TARGETS, default=TARGETS, metavar="TARGET", help=f"one or more of {', '.join(TARGETS)}")
    args = parser.parse_args()
    targets = tuple(args.only)
    try:
        generated = build(targets)
        once = scaffolds(targets)
    except CatalogError as exc:
        print(f"catalog error: {exc}", file=sys.stderr)
        return 2

    stale = [path for path, text in generated.items() if not path.exists() or path.read_text() != text]
    missing = [path for path in once if not path.exists()]
    if args.check:
        for path in stale:
            print(f"stale: {path.relative_to(ROOT)} (run python sdkgen/generate.py)", file=sys.stderr)
        for path in missing:
            print(f"missing scaffold: {path.relative_to(ROOT)} (run python sdkgen/generate.py)", file=sys.stderr)
        return 1 if stale or missing else 0
    for path, text in generated.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(f"{'updated' if path in stale else 'unchanged'}: {path.relative_to(ROOT)}")
    for path in missing:
        path.write_text(once[path])
        print(f"scaffolded: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
