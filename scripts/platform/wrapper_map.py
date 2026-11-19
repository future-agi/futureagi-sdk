#!/usr/bin/env python3
"""Check ``openapi/platform/wrapper-map.json``: one public path per platform method, in both languages.

    python3 scripts/platform/wrapper_map.py                       # against the committed scoped spec
    python3 scripts/platform/wrapper_map.py --contract FILE       # also: every operation of the pinned
                                                                  # contract is wrapped or has a reason

A finding is one of: an operation of the scoped spec with no wrapper, or a wrapper for an operation the
spec does not have; an unwrapped entry without a reason, or one that is in the spec; a duplicate public
path; a method that shadows a namespace; a missing language twin, or a path whose two languages differ
after case conversion; a rename that is not listed (or listed but not needed); argument names that differ
after case conversion; a query parameter no argument covers; a method on the wrong handle; an
idempotent operation whose method does not take ``idempotency_key`` (``options.idempotencyKey``), or a
method that takes one for an operation that is not idempotent (the core refuses such a key).

Standard library only: ``python/tests/platform/test_gates.py`` imports this module in CI.
"""

from __future__ import annotations

import argparse
import json
import keyword
import re
import sys
from pathlib import Path
from typing import Any

# Also importable by the isolated gate-test loader.
import importlib.util
_helper_spec = importlib.util.spec_from_file_location("wrapper_admission", Path(__file__).with_name("wrapper_admission.py"))
assert _helper_spec is not None and _helper_spec.loader is not None
_admission = importlib.util.module_from_spec(_helper_spec)
_helper_spec.loader.exec_module(_admission)

REPO = Path(__file__).resolve().parents[2]
MAP = REPO / "openapi" / "platform" / "wrapper-map.json"
SPEC = REPO / "openapi" / "platform" / "generated" / "futureagi-platform.openapi.json"
METHODS = ("get", "post", "put", "patch", "delete")
#: Methods an operation may back besides its primary one (methods[0]): re-reads, waiters, the stream
#: twin of a command, and a property read from the same response.
DERIVED = {"refresh", "wait", "stream", "wait_for_approval", "identity"}
RETURNS = {"stream", "property", "CommandResult"}


def snake(name: str) -> str:
    """``rotateAccessToken`` -> ``rotate_access_token`` (already-snake names are unchanged)."""
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


def operations(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """``{sdk name: {"method", "sdk_method", "params", "query"}}`` for every operation of a document."""
    out: dict[str, dict[str, Any]] = {}
    params_by_ref = (doc.get("components") or {}).get("parameters") or {}

    def resolve(p: dict[str, Any]) -> dict[str, Any]:
        ref = p.get("$ref")
        return params_by_ref[ref.rsplit("/", 1)[-1]] if ref else p

    for route, item in (doc.get("paths") or {}).items():
        for method in METHODS:
            op = item.get(method)
            if op is None:
                continue
            sdk = op["x-omega-sdk"]
            params = [
                resolve(p)
                for p in (item.get("parameters") or []) + (op.get("parameters") or [])
            ]
            out[f"{sdk['family']}.{sdk['method']}"] = {
                "sdk_method": sdk["method"],
                "method": method.upper(),
                "path": route,
                "operation_id": op.get("operationId"),
                "path_params": re.findall(r"\{([^}]+)\}", route),
                "query": [p["name"] for p in params if p.get("in") == "query"],
                "human_only": op.get("x-omega-human-only") is True,
                "idempotent": op.get("x-omega-idempotent") is True,
            }
    return out


def _segments(path: str) -> list[str]:
    return path.split(".")


def _check_args(
    where: str, method: dict[str, Any], findings: list[str]
) -> tuple[list[str], list[str], list[str]]:
    py_args, ts_args = method.get("py_args"), method.get("ts_args")
    if not isinstance(py_args, list) or not isinstance(ts_args, list):
        findings.append(f"{where}: py_args and ts_args are both required")
        return [], [], []
    star = py_args.index("*") if "*" in py_args else len(py_args)
    py_pos, py_kw = py_args[:star], py_args[star:][1:]
    ts_pos = [a for a in ts_args if not a.startswith("options.")]
    ts_kw = [a.split(".", 1)[1] for a in ts_args if a.startswith("options.")]
    leading = len(ts_pos)
    if ts_args[:leading] != ts_pos:
        findings.append(f"{where}: a TypeScript positional argument follows an option")
    if py_args.count("*") > 1 or (py_args and py_args[-1] == "*"):
        findings.append(f"{where}: py_args has a misplaced '*'")
    for name in py_pos + py_kw:
        if not name.isidentifier() or keyword.iskeyword(name) or name != snake(name):
            findings.append(
                f"{where}: Python argument {name!r} is not a snake_case identifier"
            )
    if [snake(a) for a in ts_pos] != py_pos:
        findings.append(
            f"{where}: positional arguments differ after case conversion: {py_pos} vs {ts_pos}"
        )
    if [snake(a) for a in ts_kw] != py_kw:
        findings.append(
            f"{where}: keyword arguments differ after case conversion: {py_kw} vs {ts_kw}"
        )
    return py_pos, py_kw, ts_kw


def _check_key(
    where: str,
    op: dict[str, Any],
    primary: bool,
    py_kw: list[str],
    ts_kw: list[str],
    findings: list[str],
) -> None:
    """An idempotent operation's method takes the key; any other method takes none."""
    takes = ("idempotency_key" in py_kw, "idempotencyKey" in ts_kw)
    if op["idempotent"] and primary and takes != (True, True):
        findings.append(
            f"{where}: the operation is idempotent, so its method takes idempotency_key "
            "(options.idempotencyKey)"
        )
    if not op["idempotent"] and any(takes):
        findings.append(
            f"{where}: the operation is not idempotent, so it takes no idempotency key"
        )


def _check_rename(
    name: str,
    sdk_method: str,
    primary: dict[str, Any],
    rename: Any,
    findings: list[str],
) -> None:
    wanted = [snake(s) for s in _segments(sdk_method)]
    count = len(wanted)
    tail = _segments(primary["py"])[1:][-count:]
    if rename is None:
        if tail != wanted:
            findings.append(
                f"{name}: {primary['py']} renames {sdk_method} but no rename is listed"
            )
        return
    if not isinstance(rename, dict) or not rename.get("why"):
        findings.append(f"{name}: a rename needs from, to and why")
        return
    if tail == wanted:
        findings.append(
            f"{name}: rename listed but {primary['py']} keeps the contract name"
        )
    if rename.get("from") != sdk_method:
        findings.append(
            f"{name}: rename.from {rename.get('from')!r} is not the contract method {sdk_method!r}"
        )
    if rename.get("to") != ".".join(tail):
        findings.append(
            f"{name}: rename.to {rename.get('to')!r} is not {'.'.join(tail)!r}"
        )


def check(
    mapping: dict[str, Any],
    spec: dict[str, Any],
    contract: dict[str, Any] | None = None,
    exclusions: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Every rule violation, as one line each (empty when the map is clean)."""
    findings: list[str] = []
    scoped = operations(spec)
    for namespace, unavailable in mapping.get("not_offered", {}).items():
        if (not isinstance(unavailable, dict) or unavailable.get("status") != "NOT-OFFERED"
                or not unavailable.get("owner") or not unavailable.get("reason")):
            findings.append(f"{namespace}: NOT-OFFERED requires status, owner and reason")
        if not any(name == namespace or name.startswith(namespace + ".") for name in scoped):
            findings.append(f"{namespace}: stale NOT-OFFERED namespace")
    entries: dict[str, Any] = mapping.get("operations") or {}
    handles = set(mapping.get("handles") or {})
    families = mapping.get("families") or {}
    py_paths: dict[str, str] = {}
    ts_paths: dict[str, str] = {}
    for name, entry in entries.items():
        if "unwrapped" in entry:
            if not entry.get("unwrapped") or entry.get("until") not in {
                "later",
                "never",
                "if-needed",
            }:
                findings.append(
                    f"{name}: an unwrapped entry needs a reason and until (later, never, if-needed)"
                )
            if name in scoped:
                findings.append(
                    f"{name}: unwrapped, but the scoped spec has it (remove it from scope.json)"
                )
            continue
        if name not in scoped:
            findings.append(f"{name}: wrapped, but the scoped spec does not have it")
            continue
        methods = entry.get("methods") or []
        if not methods:
            findings.append(f"{name}: no methods")
            continue
        op = scoped[name]
        if _admission.excluded_operation(name, op, exclusions or []):
            findings.append(f"{name}: public method maps to an operation the admission ledger excludes")
        checked = [_admission.language_methods(m, findings, name, snake) for m in methods]
        if checked[0].get("py"):
            _check_rename(name, op["sdk_method"], checked[0], entry.get("rename"), findings)
        internal = set(entry.get("internal") or [])
        for index, method in enumerate(checked):
            where = f"{name} {method.get('py')}"
            py, ts = method.get("py"), method.get("ts")
            if not py or not ts:
                findings.append(f"{where}: a missing language twin")
                continue
            py_seg, ts_seg = _segments(py), _segments(ts)
            same_root = py_seg[0] == ts_seg[0]
            if (
                not same_root
                or len(py_seg) != len(ts_seg)
                or [snake(s) for s in ts_seg[1:]] != py_seg[1:]
            ):
                findings.append(f"{where}: {py} and {ts} differ after case conversion")
            handle = method.get("handle")
            root = handle if handle else "client"
            if handle is not None and handle not in handles:
                findings.append(f"{where}: unknown handle {handle!r}")
            if py_seg[0] != root:
                findings.append(
                    f"{where}: the path does not start at its handle ({root})"
                )
            returns = method.get("returns")
            if (
                returns
                and returns not in RETURNS
                and re.sub(r"^Page\[(\w+)\]$", r"\1", returns) not in handles
            ):
                findings.append(f"{where}: unknown return {returns!r}")
            if index > 0 and py_seg[-1] not in DERIVED:
                findings.append(
                    f"{where}: an extra method must be one of {sorted(DERIVED)}"
                )
            for path, seen, lang in ((py, py_paths, "py"), (ts, ts_paths, "ts")):
                if not methods[index].get(lang):
                    continue
                if path in seen:
                    findings.append(
                        f"{where}: duplicate {lang} path {path} (also {seen[path]})"
                    )
                seen[path] = name
            _, py_kw, ts_kw = _check_args(where, method, findings)
            _check_key(where, op, index == 0, py_kw, ts_kw, findings)
            if index == 0:
                uncovered = [
                    q for q in op["query"] if q not in ts_kw and q not in internal
                ]
                if uncovered:
                    findings.append(
                        f"{where}: query parameters no argument covers: {uncovered}"
                    )
                bound = 1 if handle else 0
                positional = [
                    a
                    for a in method.get("ts_args") or []
                    if not a.startswith("options.")
                ]
                if len(op["path_params"]) != len(positional) + bound:
                    findings.append(
                        f"{where}: {len(op['path_params'])} path parameters, {len(positional)} positional + {bound} bound"
                    )
    for paths, lang in ((py_paths, "py"), (ts_paths, "ts")):
        names = sorted(paths)
        for a, b in zip(names, names[1:]):
            if b.startswith(a + "."):
                findings.append(f"{lang} path {a} shadows the namespace of {b}")
    for name in scoped:
        if name not in entries:
            findings.append(f"{name}: in the scoped spec with no wrapper-map entry")
    if contract is not None:
        for name, op in operations(contract).items():
            family = name.split(".", 1)[0]
            if name in entries or (
                family in families and families[family].get("unwrapped")
            ):
                if op["human_only"] and "unwrapped" not in entries.get(
                    name, {"unwrapped": True}
                ):
                    findings.append(f"{name}: human-only, so it is never wrapped")
                continue
            findings.append(
                f"{name}: in the pinned contract with no wrapper-map entry or family reason"
            )
    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Check openapi/platform/wrapper-map.json."
    )
    parser.add_argument(
        "--contract",
        type=Path,
        help="the pinned contract file (from build-platform-openapi.sh)",
    )
    parser.add_argument("--ledger", type=Path, default=_admission.DEFAULT_LEDGER)
    args = parser.parse_args(argv)
    exclusions, notice = _admission.read_ledger(args.ledger)
    print(f"wrapper-map: {notice}")
    mapping = json.loads(MAP.read_text(encoding="utf-8"))
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    contract = (
        json.loads(args.contract.read_text(encoding="utf-8")) if args.contract else None
    )
    findings = check(mapping, spec, contract, exclusions)
    for line in findings:
        print(f"wrapper-map: {line}", file=sys.stderr)
    wrapped = sum(1 for e in mapping["operations"].values() if "methods" in e)
    methods = sum(len(e.get("methods") or []) for e in mapping["operations"].values())
    print(
        f"wrapper-map: {wrapped} operations wrapped as {methods} methods, {len(findings)} finding(s)"
    )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
