"""Bounded complete-snapshot JSONL; fingerprints remain server assertions."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any, Literal, NoReturn
from uuid import UUID

from fi.generated.openapi_client.models.dataset_version_create import (
    DatasetVersionCreate,
)

MAX_BYTES = 10 * 1024 * 1024
MAX_ITEMS = 10_000
CASE_FIELDS = (
    "example_id",
    "external_id",
    "input",
    "expected",
    "metadata",
    "source_trace_id",
    "source_span_id",
    "content_hash",
    "legacy_row",
)
HEADER_FIELDS = (
    "format",
    "format_version",
    "dataset_id",
    "version_id",
    "parent_version",
    "description",
    "metadata",
    "source_revision",
    "content_hash",
    "item_count",
    "records_sha256",
)
LegacyRows = Literal["reject", "preserve", "drop"]


def _fail(line: int, message: str) -> NoReturn:
    raise ValueError(f"JSONL line {line}: {message}")


def _uuid(value: object, line: int) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        value,
    ):
        _fail(line, "identity must be a UUID string")
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        _fail(line, "identity must be a UUID string")


def _json(value: object, line: int, depth: int = 0) -> None:
    if depth > 100:
        _fail(line, "JSON nesting exceeds 100 levels")
    if isinstance(value, str):
        if "\x00" in value:
            _fail(line, "null characters are not supported")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            _fail(line, "invalid Unicode")
    elif value is None or type(value) in (bool, int):
        pass
    elif type(value) is float:
        if not math.isfinite(value):
            _fail(line, "non-finite number")
    elif isinstance(value, list):
        for child in value:
            _json(child, line, depth + 1)
    elif isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                _fail(line, "JSON object keys must be strings")
            _json(key, line, depth + 1)
            _json(child, line, depth + 1)
    else:
        _fail(line, "unsupported JSON value")


def _text(value: object, line: int, maximum: int | None = None) -> None:
    if not isinstance(value, str) or (maximum is not None and len(value) > maximum):
        _fail(line, "invalid or oversized text field")


def _hash(value: object, line: int, *, allow_blank: bool = True) -> None:
    if value == "" and allow_blank:
        return
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        _fail(line, "invalid SHA-256 fingerprint")


def _validate(header: dict, cases: list[dict]) -> None:
    if set(header) != set(HEADER_FIELDS):
        _fail(1, "missing or unknown header fields")
    if (
        header["format"] != "futureagi.dataset-version"
        or type(header["format_version"]) is not int
        or header["format_version"] != 1
    ):
        _fail(1, "unsupported format/version")
    if (
        type(header["item_count"]) is not int
        or header["item_count"] != len(cases)
        or len(cases) > MAX_ITEMS
    ):
        _fail(1, f"item_count must match 0–{MAX_ITEMS} complete records")
    _json(header, 1)
    _uuid(header["dataset_id"], 1)
    _uuid(header["version_id"], 1)
    if header["parent_version"] is not None:
        _uuid(header["parent_version"], 1)
    _text(header["description"], 1)
    _text(header["source_revision"], 1, 255)
    _hash(header["content_hash"], 1)
    _hash(header["records_sha256"], 1, allow_blank=False)
    if not isinstance(header["metadata"], dict):
        _fail(1, "metadata must be an object")
    examples, external = set(), set()
    for line, case in enumerate(cases, 2):
        if not isinstance(case, dict) or set(case) != set(CASE_FIELDS):
            _fail(line, "missing or unknown case fields")
        _json(case, line)
        example = _uuid(case["example_id"], line)
        if example in examples:
            _fail(line, "duplicate example_id")
        examples.add(example)
        if case["input"] is None:
            _fail(line, "input must not be null")
        if not isinstance(case["metadata"], dict):
            _fail(line, "metadata must be an object")
        identifier = case["external_id"]
        if identifier is not None:
            _text(identifier, line, 500)
        if identifier:
            if identifier in external:
                _fail(line, "duplicate external_id")
            external.add(identifier)
        for field in ("source_trace_id", "source_span_id"):
            _text(case[field], line, 255)
        if case["legacy_row"] is not None:
            _uuid(case["legacy_row"], line)
        _hash(case["content_hash"], line)


def _line(value: dict) -> str:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    )


def case_records_size(items: Sequence[Mapping[str, Any]]) -> int:
    """Count only the portable case bytes, excluding GET-only fields."""
    total = 0
    for index, item in enumerate(items, 2):
        try:
            record = {key: item[key] for key in CASE_FIELDS}
        except KeyError as exc:
            raise ValueError(f"JSONL line {index}: missing {exc.args[0]}") from exc
        _json(record, index)
        total += len(_line(record).encode("utf-8"))
        if total > MAX_BYTES:
            _fail(index, f"archive exceeds {MAX_BYTES} bytes")
    return total


def encode_version_jsonl(
    version: Mapping[str, Any], items: Sequence[Mapping[str, Any]]
) -> str:
    """Encode a complete version; checksum covers exact case-line UTF-8 bytes."""
    if not items:
        _fail(1, "empty exports are not accepted")
    if len(items) > MAX_ITEMS:
        _fail(1, f"at most {MAX_ITEMS} cases are supported")
    try:
        cases = [{key: item[key] for key in CASE_FIELDS} for item in items]
        header = {
            key: version[key]
            for key in (
                "parent_version",
                "description",
                "metadata",
                "source_revision",
                "content_hash",
                "item_count",
            )
        }
        header.update(
            format="futureagi.dataset-version",
            format_version=1,
            dataset_id=version["dataset"],
            version_id=version["id"],
            records_sha256="0" * 64,
        )
    except KeyError as exc:
        raise ValueError(f"Incomplete version response: missing {exc.args[0]}") from exc
    _validate(header, cases)
    cases.sort(key=lambda case: _uuid(case["example_id"], 1))
    records = "".join(_line(case) for case in cases)
    header["records_sha256"] = hashlib.sha256(records.encode("utf-8")).hexdigest()
    result = _line(header) + records
    if len(result.encode("utf-8")) > MAX_BYTES:
        _fail(1, f"archive exceeds {MAX_BYTES} bytes")
    return result


def decode_version_jsonl(
    source: str | bytes,
    dataset_id: str | UUID,
    *,
    parent_version_id: str | UUID | None = None,
    legacy_rows: LegacyRows = "reject",
) -> DatasetVersionCreate:
    """Validate an entire archive and construct one generated snapshot request."""
    if legacy_rows not in ("reject", "preserve", "drop"):
        raise ValueError("legacy_rows must be reject, preserve, or drop")
    try:
        data = source.encode("utf-8") if isinstance(source, str) else source
        if not isinstance(data, bytes) or len(data) > MAX_BYTES:
            _fail(1, f"archive must be UTF-8 text/bytes at most {MAX_BYTES} bytes")
        text = data.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("JSONL line 1: invalid UTF-8") from exc
    if not text.endswith("\n"):
        _fail(1, "archive must end with a newline")
    lines = text[:-1].split("\n")
    if not 2 <= len(lines) <= MAX_ITEMS + 1:
        _fail(1, f"archive must contain 1–{MAX_ITEMS} cases")
    objects = []
    for line, raw in enumerate(lines, 1):
        try:
            value = json.loads(raw)
        except (ValueError, RecursionError) as exc:
            raise ValueError(f"JSONL line {line}: invalid JSON") from exc
        if not isinstance(value, dict):
            _fail(line, "record must be an object")
        objects.append(value)
    header, cases = objects[0], objects[1:]
    _validate(header, cases)
    if not cases:
        _fail(1, "empty imports are not accepted")
    records = data[data.index(b"\n") + 1 :]
    if hashlib.sha256(records).hexdigest() != header["records_sha256"]:
        _fail(1, "case-record checksum mismatch")
    target = _uuid(str(dataset_id), 1)
    if parent_version_id is not None:
        _uuid(str(parent_version_id), 1)
    items = []
    for line, case in enumerate(cases, 2):
        item = {
            key: value
            for key, value in case.items()
            if key not in ("content_hash", "legacy_row")
        }
        if case["legacy_row"] is not None:
            if legacy_rows == "reject" or (
                legacy_rows == "preserve" and _uuid(header["dataset_id"], 1) != target
            ):
                _fail(
                    line, "legacy_row requires explicit same-dataset preserve or drop"
                )
            if legacy_rows == "preserve":
                item["legacy_row_id"] = case["legacy_row"]
        items.append(item)
    payload = {
        "items": items,
        "description": header["description"],
        "metadata": header["metadata"],
        "source_revision": header["source_revision"],
    }
    if parent_version_id is not None:
        payload["parent_version_id"] = str(parent_version_id)
    if len(_line(payload).encode("utf-8")) > MAX_BYTES:
        _fail(1, "snapshot request exceeds byte limit")
    return DatasetVersionCreate.from_dict(payload)
