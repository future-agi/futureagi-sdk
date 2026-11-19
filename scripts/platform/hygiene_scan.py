#!/usr/bin/env python3
"""The hygiene scan in Python: the same rules as ``hygiene-scan.mjs``, for CI jobs that have no Node.

    python3 scripts/platform/hygiene_scan.py [path ...]

Reads ``scripts/platform/hygiene-rules.json``: text patterns and hashed internal names in every
public platform file, and in an OpenAPI document any key named ``evidence`` and any extension the
allowlist does not name (an extension is told apart from a property or header named ``x-...`` by
position, as in ``openapi-walk.mjs``). Internal names are matched as in ``hygiene-names.mjs``: a line
is lower-cased and split into words (``[a-z0-9_]`` runs); words joined only by ``.`` or ``-`` form a
run, and every sequence of 1 to ``maxWords`` consecutive words of a run, with its separators, is
hashed and looked up.

Which files: in a git checkout, every file git would commit under the paths (tracked, plus untracked
files that are not ignored); elsewhere (an exported tree), every file under them except interpreter
caches. No file is skipped for its name or extension, the rule file included; a file that is not
UTF-8 text is a hit. An exemption names one file, the sha256 of one line (stripped) and the rules that
line may hit; an exemption that matches nothing in a scanned file is itself a hit. Standard library
only; ``python/tests/platform/test_gates_hygiene.py`` imports it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[2]
RULES_PATH = "scripts/platform/hygiene-rules.json"
RULES = REPO / RULES_PATH
DEFAULT_PATHS = (
    "python/fi/evals",
    "python/tests/evals",
    "openapi/platform",
    "scripts/platform",
    "scripts/generate-platform-sdk.sh",
    "python/fi/_core",
    "python/fi/generated/platform",
    "python/tests/platform",
    "typescript/futureagi/src/_core",
    "typescript/futureagi/src/generated/platform",
    "tests/platform-conformance",
)
#: Outside a git checkout only: interpreter and package caches, which nothing commits.
CACHE_DIRS = {"node_modules", "__pycache__", ".pytest_cache"}
WORD = re.compile(r"[a-z0-9_]+")
SEPARATOR = re.compile(r"[.-]+")
HEX64 = re.compile(r"[0-9a-f]{64}")
METHODS = ("get", "post", "put", "patch", "delete")
Visit = Callable[[str, Any, str, bool, str], None]
_LOCK_SPEC = importlib.util.spec_from_file_location("hygiene_lockfiles", Path(__file__).with_name("hygiene_lockfiles.py"))
_LOCKS = importlib.util.module_from_spec(_LOCK_SPEC)
_LOCK_SPEC.loader.exec_module(_LOCKS)


def load_rules(path: Path = RULES) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def name_candidates(line: str, max_words: int) -> list[str]:
    """Every candidate of one line, in order of its first word, then length."""
    lower = line.lower()
    words = [(m.start(), m.end()) for m in WORD.finditer(lower)]
    out = []
    for i in range(len(words)):
        for j in range(i, min(len(words), i + max_words)):
            if j > i and not SEPARATOR.fullmatch(lower, words[j - 1][1], words[j][0]):
                break
            out.append(lower[words[i][0] : words[j][1]])
    return out


def name_hits(line: str, names: dict[str, Any] | None) -> list[dict[str, str]]:
    """The hashed-name hits of one line: the first candidate per rule, as ``{"rule", "text"}``."""
    table = (names or {}).get("sha256") or {}
    if not table:
        return []
    hits: dict[str, dict[str, str]] = {}
    for candidate in name_candidates(line, names["maxWords"]):
        rule = table.get(sha256(candidate))
        if rule is not None and rule not in hits:
            hits[rule] = {"rule": rule, "text": candidate}
    return list(hits.values())


def scan_text(text: str, suffix: str, rules: dict[str, Any], file: str = "") -> list[dict[str, Any]]:
    """Pattern and name hits in one text: ``{"rule", "line", "text"}``."""
    hits = []
    patterns = [
        (p["id"], re.compile(p["regex"]))
        for p in rules["patterns"]
        if suffix not in p.get("skipExtensions", []) and ("paths" not in p or file in p["paths"])
    ]
    names = rules.get("names")
    for number, line in enumerate(text.split("\n"), start=1):
        for rule, pattern in patterns:
            match = pattern.search(line)
            if match:
                hits.append({"rule": rule, "line": number, "text": match.group(0)})
        for hit in name_hits(line, names):
            hits.append({"rule": hit["rule"], "line": number, "text": hit["text"]})
    return hits


def _walk(
    node: Any, rules: dict[str, Any], visit: Visit, where: str = "root", path: str = ""
) -> None:
    if isinstance(node, list):
        for index, item in enumerate(node):
            _walk(item, rules, visit, "other", f"{path}/{index}")
        return
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        here = f"{path}/{key}"
        visit(key, value, where, False, here)
        if key == "paths" and where == "root" and isinstance(value, dict):
            for name, item in value.items():
                visit(name, item, "root", True, f"{here}/{name}")
                _walk_path_item(item, rules, visit, f"{here}/{name}")
        elif key in rules["nameMaps"] and isinstance(value, dict):
            for name, child in value.items():
                visit(name, child, "other", True, f"{here}/{name}")
                _walk(child, rules, visit, "other", f"{here}/{name}")
        else:
            _walk(value, rules, visit, "other", here)


def _walk_path_item(item: Any, rules: dict[str, Any], visit: Visit, path: str) -> None:
    if not isinstance(item, dict):
        return
    for key, value in item.items():
        here = f"{path}/{key}"
        visit(key, value, "pathItem", False, here)
        if key in METHODS and isinstance(value, dict):
            for op_key, op_value in value.items():
                op_path = f"{here}/{op_key}"
                visit(op_key, op_value, "operation", False, op_path)
                if op_key in rules["nameMaps"] and isinstance(op_value, dict):
                    for name, child in op_value.items():
                        visit(name, child, "other", True, f"{op_path}/{name}")
                        _walk(child, rules, visit, "other", f"{op_path}/{name}")
                else:
                    _walk(op_value, rules, visit, "other", op_path)
        else:
            _walk(value, rules, visit, "other", here)


def extension_allowed(
    key: str, value: Any, where: str, is_name: bool, rules: dict[str, Any]
) -> bool:
    if is_name or not key.startswith("x-"):
        return True
    if where == "operation":
        return key in rules["extensions"]["operation"]
    if where in ("pathItem", "root"):
        return False
    return key in rules["extensions"]["schema"] and value is True


def structural_findings(
    doc: dict[str, Any], rules: dict[str, Any]
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    subkeys = rules["extensions"]["subkeys"]

    def visit(key: str, value: Any, where: str, is_name: bool, path: str) -> None:
        if not is_name and key in rules["forbiddenKeys"]:
            findings.append({"rule": "forbidden-key", "at": path, "text": key})
        if not extension_allowed(key, value, where, is_name, rules):
            findings.append({"rule": "extension-not-allowed", "at": path, "text": key})
        if (
            not is_name
            and where == "operation"
            and key in subkeys
            and isinstance(value, dict)
        ):
            for sub in value:
                if sub not in subkeys[key]:
                    findings.append(
                        {
                            "rule": "extension-subkey-not-allowed",
                            "at": f"{path}/{sub}",
                            "text": sub,
                        }
                    )

    _walk(doc, rules, visit)
    return findings


def _git_files(targets: list[str], root: Path) -> list[str] | None:
    """Repository-relative files git would commit under ``targets``, or None when ``root`` is not a checkout's top."""

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        ).stdout

    try:
        top = git("rev-parse", "--show-toplevel").strip()
        if os.path.realpath(top) != os.path.realpath(root):
            return None
        out = git(
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            *targets,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return sorted({rel for rel in out.split("\0") if rel and (root / rel).exists()})


def list_files(targets: list[str], root: Path = REPO) -> list[str]:
    """The repository-relative files the scan reads under ``targets``."""
    from_git = _git_files(targets, root)
    if from_git is not None:
        return from_git
    out = []
    for target in targets:
        absolute = root / target
        if absolute.is_file():
            out.append(absolute.relative_to(root).as_posix())
            continue
        for path in sorted(absolute.rglob("*")) if absolute.is_dir() else []:
            if path.is_file() and not CACHE_DIRS & set(
                path.relative_to(absolute).parts[:-1]
            ):
                out.append(path.relative_to(root).as_posix())
    return out


def _exemption_for(
    rules: dict[str, Any], rel: str, rule: str, line: str
) -> dict[str, Any] | None:
    digest = sha256(line)
    for exemption in rules.get("exemptions", []):
        if (
            exemption.get("path") == rel
            and exemption.get("lineSha256") == digest
            and rule in (exemption.get("rules") or [])
        ):
            return exemption
    return None


def _names_findings(names: dict[str, Any] | None) -> list[str]:
    out: list[str] = []
    if names is None:
        return out
    limit = names.get("maxWords")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        out.append("names.maxWords must be a positive integer")
    for digest, rule in (names.get("sha256") or {}).items():
        if not HEX64.fullmatch(digest):
            out.append(f'names.sha256: "{digest[:12]}..." is not a lower-case sha256')
        if not isinstance(rule, str) or rule == "":
            out.append(f"names.sha256: {digest[:12]} has no rule id")
    return out


def _rule_findings(
    rules: dict[str, Any], scanned: set[str], used: list[int]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = [
        {"file": RULES_PATH, "line": 0, "rule": "invalid-names", "text": text}
        for text in _names_findings(rules.get("names"))
    ]
    for exemption in rules.get("exemptions", []):
        digest = exemption.get("lineSha256")
        valid = (
            isinstance(exemption.get("path"), str)
            and isinstance(digest, str)
            and HEX64.fullmatch(digest) is not None
            and isinstance(exemption.get("rules"), list)
            and len(exemption["rules"]) > 0
            and bool(exemption.get("why"))
        )
        if not valid:
            out.append(
                {
                    "file": str(exemption.get("path")),
                    "line": 0,
                    "rule": "invalid-exemption",
                    "text": "needs path, lineSha256, rules and why",
                }
            )
        elif exemption["path"] in scanned and id(exemption) not in used:
            out.append(
                {
                    "file": exemption["path"],
                    "line": 0,
                    "rule": "stale-exemption",
                    "text": digest[:12],
                }
            )
    return out


def scan_paths(
    targets: list[str], rules: dict[str, Any], root: Path = REPO
) -> tuple[int, list[dict[str, Any]]]:
    """``(files scanned, hits)`` for repository-relative ``targets`` (missing ones are skipped)."""
    hits: list[dict[str, Any]] = []
    scanned: set[str] = set()
    used: list[int] = []
    files = list_files(targets, root)
    for rel in files:
        scanned.add(rel)
        suffix = Path(rel).suffix
        try:
            text = (root / rel).read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            text = "\0"
        if "\0" in text:
            hits.append(
                {
                    "file": rel,
                    "rule": "not-text",
                    "line": 0,
                    "text": "not UTF-8 text, so it cannot be scanned",
                }
            )
            continue
        lines = text.split("\n")
        try:
            projected = _LOCKS.project(text, rel)
        except Exception:
            projected = text
            hits.append({"file": rel, "rule": "invalid-lockfile", "line": 0,
                         "text": "lockfile could not be parsed structurally"})
        for hit in scan_text(projected, suffix, rules, rel):
            exemption = _exemption_for(
                rules, rel, hit["rule"], lines[hit["line"] - 1].strip()
            )
            if exemption is not None:
                used.append(id(exemption))
            else:
                hits.append({"file": rel, **hit})
        if suffix != ".json":
            continue
        try:
            doc = json.loads(text)
        except ValueError:
            hits.append({"file": rel, "rule": "invalid-json", "line": 0, "text": ""})
            continue
        if isinstance(doc, dict) and isinstance(doc.get("openapi"), str):
            for f in structural_findings(doc, rules):
                hits.append(
                    {
                        "file": rel,
                        "rule": f["rule"],
                        "line": 0,
                        "text": f"{f['text']} at {f['at']}",
                    }
                )
    hits += _rule_findings(rules, scanned, used)
    return len(files), hits


def main(argv: list[str]) -> int:
    count, hits = scan_paths(argv or list(DEFAULT_PATHS), load_rules())
    for hit in hits:
        print(
            f"hygiene: {hit['file']}:{hit['line']} {hit['rule']} {hit['text']}",
            file=sys.stderr,
        )
    print(f"hygiene: {count} files scanned, {len(hits)} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
