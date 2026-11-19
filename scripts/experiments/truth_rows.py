"""Explicit, lossless migration of externally retained conformance row names.

The mapping is supplied by the owner of the truth table, not inferred from row
prefixes. Unrelated rows are preserved; conflicting aliases are errors. Missing
required rows remain unrecorded at the gate. No migration assigns or changes a verdict.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


def load_row_map(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("row map must be a nonempty object")
    if any(not isinstance(k, str) or not k.strip() or
           not isinstance(v, str) or not v.strip() for k, v in data.items()):
        raise ValueError("row map names must be nonempty strings")
    if len(set(data.values())) != len(data):
        raise ValueError("row map must be one-to-one")
    return data


def migrate_rows(rows: Mapping[str, str], mapping: Mapping[str, str]) -> dict[str, str]:
    """Rename known rows once; preserve every unrelated row and every status."""
    result: dict[str, str] = {}
    for old, status in rows.items():
        new = mapping.get(old, old)
        if new in result:
            raise ValueError(f"truth row alias collision: {new}")
        result[new] = status
    return result
