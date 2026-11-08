"""Admission-ledger and explicitly unavailable language handling for wrapper maps."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_LEDGER = Path(__file__).resolve().parents[2] / "openapi/admission-ledger.json"


def read_ledger(path: Path = DEFAULT_LEDGER) -> tuple[list[dict[str, Any]], str]:
    if not path.exists():
        return [], f"admission ledger absent ({path.name}); using an empty exclusion list"
    value = json.loads(path.read_text(encoding="utf-8"))
    rows = value.get("operations", value.get("entries")) if isinstance(value, dict) else value
    if isinstance(rows, dict):
        rows = [dict(row, ledger_key=key) for key, row in rows.items()]
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("admission ledger must contain an operations/entries list or object")
    excluded = []
    for row in rows:
        states = [str(row.get(k, "")).lower() for k in ("disposition", "state", "status", "namespace")]
        if "excluded" not in states:
            continue
        if not any(row.get(k) for k in ("operation_id", "operationId", "sdk_name", "name", "ledger_key", "path")):
            raise ValueError("excluded ledger operation has no operation identity")
        excluded.append(row)
    return excluded, f"admission ledger loaded: {len(excluded)} excluded operation(s)"


def excluded_operation(name: str, op: dict[str, Any], rows: list[dict[str, Any]]) -> bool:
    identities = {name, op.get("operation_id")}
    identities.discard(None)
    for row in rows:
        if any(row.get(k) in identities for k in ("operation_id", "operationId", "sdk_name", "name", "ledger_key")):
            return True
        if row.get("path") == op.get("path") and str(row.get("method", "")).upper() == op.get("method"):
            return True
    return False


def language_methods(method: dict[str, Any], findings: list[str], where: str, snake: Any) -> dict[str, Any]:
    """Validate NOT-OFFERED declarations, then supply comparison-only spellings for the missing twin."""
    result = dict(method)
    exceptions = method.get("not_offered", {})
    if not isinstance(exceptions, dict):
        findings.append(f"{where}: not_offered must be a language object")
        exceptions = {}
    for lang in exceptions:
        if lang not in ("py", "ts") or method.get(lang):
            findings.append(f"{where}: stale or unknown NOT-OFFERED language {lang}")
    for lang, other in (("py", "ts"), ("ts", "py")):
        if method.get(lang):
            continue
        declaration = exceptions.get(lang, {})
        if not isinstance(declaration, dict) or declaration.get("status") != "NOT-OFFERED" or not declaration.get("reason"):
            findings.append(f"{where}: a missing language twin ({lang}); requires NOT-OFFERED and reason")
            continue
        if not method.get(other):
            findings.append(f"{where}: both language twins are missing")
            continue
        if lang == "py":
            result[lang] = ".".join([method[other].split(".")[0], *map(snake, method[other].split(".")[1:])])
            args = method.get("ts_args", [])
            pos = [snake(a) for a in args if not a.startswith("options.")]
            kw = [snake(a.split(".", 1)[1]) for a in args if a.startswith("options.")]
            result["py_args"] = pos + (["*", *kw] if kw else [])
        else:
            result[lang] = method[other]
            args = method.get("py_args", [])
            star = args.index("*") if "*" in args else len(args)
            def camel(text: str) -> str:
                first, *rest = text.split("_")
                return first + "".join(s.title() for s in rest)
            result["ts_args"] = [camel(a) for a in args[:star]] + ["options." + camel(a) for a in args[star + 1:]]
    return result
