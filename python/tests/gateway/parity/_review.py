"""Validate reviewer provenance without exposing unpublished revision identifiers."""

from __future__ import annotations

from datetime import date
import hashlib
import json
import re
from pathlib import Path

# Also loaded by the standalone hygiene checker, outside the parity package.
RETAINED = json.loads((Path(__file__).resolve().parents[4] /
                       "tests/fixtures/gateway/review-records.json").read_text())["entries"]


def contract_digest(entry: dict) -> str:
    """Bind a retained review to the exact acceptance rules it reviewed."""
    contract = {k: entry[k] for k in ("id", "lang", "status", "applies_to", "match")}
    return hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

TRANSPORT_RECORD = "python-transport-fixes-2026-10-28"
TRANSPORT_EVIDENCE = "python/tests/gateway/unit/test_catalog_compatibility.py"
RECORD_FIELDS = {"by", "record", "date", "evidence", "verdict"}
REVISION = re.compile(r'"commit"\s*:|(?<![A-Za-z0-9])[0-9a-fA-F]{7,40}(?![A-Za-z0-9])')


def review_metadata_hits(data: object) -> list[str]:
    """Flag revision-bearing transport review metadata, including nested values."""
    if not isinstance(data, dict) or not isinstance(data.get("differences"), list):
        return []
    hits = []
    for entry in data["differences"]:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id", "")
        if not isinstance(entry_id, str):
            continue
        if REVISION.search(json.dumps(entry.get("reviewer"), sort_keys=True)):
            hits.append(entry_id)
    return hits


def assert_review_record(entry: dict) -> None:
    """Historical reviews are exact retained records, not arbitrary signature-shaped text."""
    entry_id = entry["id"]
    reviewer = entry["reviewer"]
    assert isinstance(reviewer, dict), f"{entry_id}: no reviewer record"
    fields = RECORD_FIELDS if entry_id.startswith("PY-4.0-") else {"by", "record", "verdict"}
    for key in fields:
        assert isinstance(reviewer.get(key), str) and reviewer[key].strip(), (
            f"{entry_id}: reviewer.{key}"
        )
    assert not review_metadata_hits({"differences": [entry]}), entry_id
    if not entry_id.startswith("PY-4.0-"):
        retained = RETAINED.get(entry_id)
        assert retained is not None, f"{entry_id}: unretained review"
        assert set(reviewer) == fields, f"{entry_id}: reviewer fields"
        assert reviewer == retained["reviewer"], f"{entry_id}: reviewer differs from retained record"
        assert contract_digest(entry) == retained["contract_sha256"], f"{entry_id}: reviewed rules changed"
        return
    assert set(reviewer) == RECORD_FIELDS, f"{entry_id}: reviewer fields"
    assert reviewer["record"] == TRANSPORT_RECORD, f"{entry_id}: reviewer.record"
    try:
        assert date.fromisoformat(reviewer["date"]).isoformat() == reviewer["date"]
    except ValueError as exc:
        raise AssertionError(f"{entry_id}: reviewer.date") from exc
    assert reviewer["record"].endswith("-" + reviewer["date"]), entry_id
    assert reviewer["evidence"] == TRANSPORT_EVIDENCE, f"{entry_id}: reviewer.evidence"
    assert not review_metadata_hits({"differences": [entry]}), (
        f"{entry_id}: review metadata contains a revision identifier"
    )
