"""Compare a recording against a golden under intended-differences.json.

    cd python/tests/gateway && python -m parity.compare --golden <dir> --new <dir> --label <name>

A comparison is named ``<golden>-><new>`` (for example
``py-agentcc-1.0.0->e-new-py`` or ``ts-client-1.0.0-esm->ts-client-1.0.1-esm``),
and ``compare`` refuses a name that does not fit the two directories
(``labels.py``; the CLI exits 2).
Every leaf difference must be covered by a ``proven`` entry (evidence, a test
id and a reviewer record) whose ``applies_to`` names that comparison; a proven
entry that covers nothing fails too. A ``planned`` entry never covers: it is a
implementation's work list, so a difference only a planned entry matches is unlisted
(the report names that entry beside it), and a planned entry may stay
unobserved. Patterns use ``*`` and ``?`` only; every other character is literal.
A match rule is {path, kind (changed|added|removed|any), old/new (regex on the
value), top_level (the path is a whole case)}.
The TypeScript twin (gateway-client/tests/parity/compare.mjs) implements the
same rules and both pass tests/fixtures/gateway/comparator-cases.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .labels import LabelError, check_label

MISSING = "<missing>"
# Sorted name lists compared as sets, so one added name is one difference.
SET_KEYS = frozenset(
    {
        "exports",
        "public",
        "defined",
        "all",
        "__all__",
        "dir_public",
        "case_ids",
        "proto",
        "statics",
        "methods",
        "clientMethods",
        "valid",
        "valid_models",
        "model_info_keys",
    }
)


@dataclass(frozen=True)
class Diff:
    path: str
    kind: str  # changed | added | removed
    old: Any
    new: Any


# Unbounded, like the TypeScript twin's cache: the shim entries name about ten thousand
# exact paths, and a bounded cache recompiles each pattern on every lookup.
@lru_cache(maxsize=None)
def _glob(pattern: str) -> re.Pattern[str]:
    return re.compile(
        "".join(
            ".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern
        )
        + r"\Z",
        re.S,
    )


def matches(pattern: str, text: str) -> bool:
    return _glob(pattern).match(text) is not None


def view(value: Any) -> Any:
    """Headers recorded as [name, value] pairs become a name -> value map."""
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if (
                key == "headers"
                and isinstance(item, list)
                and all(isinstance(p, list) and len(p) == 2 for p in item)
            ):
                merged: dict[str, Any] = {}
                for name, val in item:
                    if name in merged:
                        prev = merged[name]
                        merged[name] = (prev if isinstance(prev, list) else [prev]) + [
                            val
                        ]
                    else:
                        merged[name] = val
                out[key] = merged
            elif (
                key in SET_KEYS
                and isinstance(item, list)
                and all(isinstance(v, str) for v in item)
            ):
                out[key] = {name: True for name in item}
            else:
                out[key] = view(item)
        return out
    if isinstance(value, list):
        return [view(v) for v in value]
    return value


def diff(old: Any, new: Any, path: str = "") -> list[Diff]:
    if isinstance(old, dict) and isinstance(new, dict):
        out: list[Diff] = []
        for key in sorted(old.keys() | new.keys()):
            sub = f"{path}/{key}" if path else key
            if key not in new:
                out.append(Diff(sub, "removed", old[key], MISSING))
            elif key not in old:
                out.append(Diff(sub, "added", MISSING, new[key]))
            else:
                out.extend(diff(old[key], new[key], sub))
        return out
    if isinstance(old, list) and isinstance(new, list):
        out = []
        for i in range(max(len(old), len(new))):
            sub = f"{path}/{i}"
            if i >= len(new):
                out.append(Diff(sub, "removed", old[i], MISSING))
            elif i >= len(old):
                out.append(Diff(sub, "added", MISSING, new[i]))
            else:
                out.extend(diff(old[i], new[i], sub))
        return out
    return (
        []
        if old == new and type(old) is type(new)
        else [Diff(path, "changed", old, new)]
    )


def _scalar(value: Any) -> str:
    """The text an old/new regex sees: strings as they are, anything else as compact sorted JSON."""
    return (
        value
        if isinstance(value, str)
        else json.dumps(value, sort_keys=True, separators=(",", ":"))
    )


def covers(rule: dict[str, Any], d: Diff) -> bool:
    if not matches(rule.get("path", "*"), d.path):
        return False
    if rule.get("top_level") and "/" in d.path:
        return False
    if rule.get("kind", "any") not in ("any", d.kind):
        return False
    for side in ("old", "new"):
        if side in rule and re.search(rule[side], _scalar(getattr(d, side))) is None:
            return False
    return True


def load_recording(folder: Path) -> dict[str, Any]:
    index = json.loads((folder / "index.json").read_text())
    cases: dict[str, Any] = {}
    for name in sorted(index.get("files", {})):
        cases.update(json.loads((folder / name).read_text())["cases"])
    surface = {k: index[k] for k in ("loads", "dts") if k in index}
    if surface:
        cases["<index>"] = surface
    return {"index": index, "cases": cases}


def compare_cases(
    golden: dict[str, Any],
    new: dict[str, Any],
    intended: list[dict[str, Any]],
    label: str,
) -> dict[str, Any]:
    rules = [
        r for r in intended if any(matches(p, label) for p in r.get("applies_to", []))
    ]
    hits: dict[str, int] = {r["id"]: 0 for r in rules}
    unlisted: list[dict[str, Any]] = []
    for d in diff(view(golden), view(new)):
        hit = [r for r in rules if any(covers(m, d) for m in r.get("match", []))]
        for r in hit:
            hits[r["id"]] += 1
        # Only a proven entry covers (API design 5.3: evidence, a test id, a reviewer).
        if not any(r.get("status") == "proven" for r in hit):
            unlisted.append({**d.__dict__, "planned": sorted(r["id"] for r in hit)})
    unobserved = {
        s: sorted(r["id"] for r in rules if r.get("status") == s and hits[r["id"]] == 0)
        for s in ("proven", "planned")
    }
    covered = {
        r["id"]: hits[r["id"]]
        for r in rules
        if r.get("status") == "proven" and hits[r["id"]]
    }
    return {
        "label": label,
        "ok": not unlisted and not unobserved["proven"],
        "unlisted": unlisted,
        "covered": dict(sorted(covered.items())),
        "unobserved_proven": unobserved["proven"],
        "unobserved_planned": unobserved["planned"],
    }


# The recording environment a golden is only valid in: the interpreter line and
# every third-party library the recorder notes (the targets themselves aside).
PINNED_DEPS = (
    "httpx",
    "httpcore",
    "pydantic",
    "pydantic-core",
    "anyio",
    "typing-extensions",
    "jsonschema",
    "tiktoken",
)


def pinned_environment_differences(
    golden_env: dict[str, Any], current_env: dict[str, Any]
) -> list[str]:
    """What differs between a golden's recording environment and this one.

    A Python golden pins library behaviour (pydantic's error text and its
    errors.pydantic.dev/<version> links, httpx defaults), so a comparison is only
    meaningful when this list is empty.
    """

    def line(env: dict[str, Any]) -> str:
        return ".".join(str(env.get("python") or "").split(".")[:2])

    out = []
    if line(golden_env) != line(current_env):
        out.append(f"python {line(golden_env)} != {line(current_env)}")
    if golden_env.get("implementation") != current_env.get("implementation"):
        out.append(
            f"implementation {golden_env.get('implementation')} != {current_env.get('implementation')}"
        )
    old, new = golden_env.get("deps", {}), current_env.get("deps", {})
    for dep in PINNED_DEPS:
        if old.get(dep) != new.get(dep):
            out.append(f"{dep} {old.get(dep)} != {new.get(dep)}")
    return out


def compare(
    golden_dir: Path, new_dir: Path, intended_file: Path, label: str
) -> dict[str, Any]:
    """Compare two recordings on disk; a label that does not fit them raises LabelError."""
    check_label(label, Path(golden_dir), Path(new_dir))
    golden, new = load_recording(golden_dir), load_recording(new_dir)
    intended = json.loads(intended_file.read_text())["differences"]
    report = compare_cases(golden["cases"], new["cases"], intended, label)
    env_old, env_new = golden["index"].get("environment", {}), new["index"].get(
        "environment", {}
    )
    report["environment_differences"] = [d.__dict__ for d in diff(env_old, env_new)]
    return report


def main(argv: list[str] | None = None) -> int:
    from ._fixtures import FIXTURES

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--golden", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument(
        "--intended", type=Path, default=FIXTURES / "intended-differences.json"
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args(argv)
    try:
        report = compare(args.golden, args.new, args.intended, args.label)
    except LabelError as err:
        print(err, file=sys.stderr)
        return 2
    if args.report:
        args.report.write_text(
            json.dumps(report, indent=1, sort_keys=True, default=str) + "\n"
        )
    print(
        f"{args.label}: ok={report['ok']} unlisted={len(report['unlisted'])} covered={report['covered']} "
        f"unobserved_proven={report['unobserved_proven']}"
    )
    for d in report["unlisted"][: args.limit]:
        planned = f" (planned: {', '.join(d['planned'])})" if d["planned"] else ""
        print(
            f"  UNLISTED {d['kind']} {d['path']}{planned}: {str(d['old'])[:80]!s} -> {str(d['new'])[:80]!s}"
        )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
