"""Validate PEP 660 source mappings without importing or executing finder code."""
from __future__ import annotations

import ast
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
from urllib.parse import unquote, urlsplit


def _record_file(dist: Any, rows: dict[str, tuple[str, str]], name: str) -> Path:
    from fi._core.namespace_ownership import file_digest

    if name not in rows or ".." in PurePosixPath(name).parts or "\\" in name:
        raise ValueError("unrecorded editable mapping")
    target = Path(dist.locate_file(name))
    digest, size = rows[name]
    algorithm, expected = digest.split("=", 1)
    if (not target.is_file() or file_digest(target, algorithm) != expected
            or (size and target.stat().st_size != int(size))):
        raise ValueError("damaged editable mapping")
    return target


def _finder_target(dist: Any, rows: dict[str, tuple[str, str]], line: str) -> Path:
    match = re.fullmatch(r"import (__editable__[a-zA-Z0-9_]*_finder);\s*\1\.install\(\)", line)
    if match is None:
        raise ValueError("unsupported editable import hook")
    finder = _record_file(dist, rows, match[1] + ".py")
    mappings = []
    for node in ast.parse(finder.read_text(encoding="utf-8")).body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(target, ast.Name) and target.id == "MAPPING" for target in targets):
            mappings.append(ast.literal_eval(node.value))
    if len(mappings) != 1 or not isinstance(mappings[0], dict) or not isinstance(mappings[0].get("fi"), str):
        raise ValueError("missing static package mapping")
    return Path(mappings[0]["fi"])


def inspect_editable(dist: Any, record_rows: list[list[str]]) -> bool:
    """True only for an explicit editable install with an intact recorded source hook.

    False means ordinary wheel semantics. Malformed or damaged editable metadata
    raises ValueError so it cannot silently turn into a clean development install.
    Source files deliberately have no immutable wheel hashes in this mode.
    """
    direct = dist.read_text("direct_url.json")
    if direct is None:
        return False
    doc = json.loads(direct)
    if not isinstance(doc, dict) or not isinstance(doc.get("dir_info"), dict):
        return False
    if doc["dir_info"].get("editable") is not True:
        return False
    url = urlsplit(doc.get("url", ""))
    if url.scheme != "file" or url.netloc not in ("", "localhost") or url.query or url.fragment:
        raise ValueError("editable source must be a local directory")
    project = Path(unquote(url.path))
    if not project.is_absolute() or not project.is_dir():
        raise ValueError("editable source directory is missing")
    project = project.resolve()
    rows: dict[str, tuple[str, str]] = {}
    site = Path(dist.locate_file("")).resolve()
    for row in record_rows:
        if len(row) != 3:
            raise ValueError("damaged editable RECORD")
        name = row[0]
        # Poetry records absolute installed paths; wheels generally use relative
        # ones. Only mapping files inside this distribution's site directory count.
        if Path(name).is_absolute():
            try:
                name = Path(name).resolve().relative_to(site).as_posix()
            except ValueError:
                continue
        if name in rows:
            raise ValueError("duplicate editable RECORD path")
        rows[name] = (row[1], row[2])
    targets = []
    for name in rows:
        if not name.endswith(".pth") or "/" in name:
            continue
        pth = _record_file(dist, rows, name)
        for line in pth.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(("import ", "import\t")):
                target = _finder_target(dist, rows, line)
            else:
                base = Path(line)
                if not base.is_absolute():
                    raise ValueError("editable path must be absolute")
                target = base / "fi"
            target = target.resolve()
            if not target.is_relative_to(project) or not (target / "__init__.py").is_file():
                raise ValueError("editable mapping is outside its source or missing its package")
            if not (target / "_core/namespace_ownership.py").is_file():
                raise ValueError("editable mapping does not contain the SDK")
            targets.append(target)
    if len(set(targets)) != 1:
        raise ValueError("editable package mapping is missing or ambiguous")
    return True
