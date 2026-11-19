"""Canonical bytes and receipts.

The journal stores the **exact canonical bytes** of each item: sorted keys, compact separators,
no NaN/Infinity, UTF-8. ``receipt_key = sha256(run_id 0x1f example_id 0x1f trial 0x1f
sha256(bytes))`` in hex. The bytes are never re-serialized, so a resume after an SDK upgrade cannot
produce a different receipt for the same work. ``golden/receipts.json`` pins the arithmetic.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from typing import Any

_SEP = "\x1f"


def to_jsonable(value: Any) -> Any:
    """Serialize a task output when its trial ends (pydantic, dataclass, LangChain messages, numpy)."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_jsonable(v) for v in value]
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        try:
            return to_jsonable(dump(mode="json"))
        except TypeError:
            return to_jsonable(dump())
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return to_jsonable(dataclasses.asdict(value))
    item = getattr(value, "item", None)  # numpy scalars
    if callable(item) and type(value).__module__.startswith("numpy"):
        try:
            return to_jsonable(item())
        except (TypeError, ValueError):
            pass
    tolist = getattr(value, "tolist", None)
    if callable(tolist) and type(value).__module__.startswith("numpy"):
        return to_jsonable(tolist())
    to_dict = getattr(value, "to_dict", None) or getattr(value, "dict", None)
    if callable(to_dict):
        try:
            return to_jsonable(to_dict())
        except TypeError:
            pass
    return repr(value)


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(
        to_jsonable(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def receipt_key(run_id: str, example_id: str, trial: int, item_bytes: bytes) -> str:
    material = _SEP.join([str(run_id), str(example_id), str(int(trial)), sha256_hex(item_bytes)])
    return sha256_hex(material.encode("utf-8"))


def content_hash(row: Any) -> str:
    return sha256_hex(canonical_bytes(row))
