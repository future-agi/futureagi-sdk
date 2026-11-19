"""Review provenance uses a retained record, never an unpublished revision."""

from __future__ import annotations

import copy
import json

import pytest

from . import test_e_new_overlay as overlay
from . import test_gw_public_hygiene as hygiene
from parity import test_parity_intended as shared

RECORD = "python-transport-fixes-2026-10-28"


def _record() -> dict:
    return {
        "by": "independent cross-family review of the Python transport fixes",
        "record": RECORD,
        "date": "2026-10-28",
        "evidence": "python/tests/gateway/unit/test_catalog_compatibility.py",
        "verdict": "accepted: the four transport fixes, not release acceptance",
    }


def _validate(monkeypatch, reviewer: dict, validator: str) -> None:
    entry = copy.deepcopy(overlay._transport_entries()[0])
    entry.update(status="proven", reviewer=reviewer)
    if validator == "overlay":
        overlay._assert_review_state(entry)
    else:
        monkeypatch.setattr(shared, "INTENDED", [entry])
        shared.test_a_proven_entry_carries_evidence_a_test_id_and_a_reviewer_record()


@pytest.mark.parametrize("validator", ["overlay", "shared"])
def test_both_schemas_accept_retained_review_records(monkeypatch, validator) -> None:
    _validate(monkeypatch, _record(), validator)


BAD = [
    {k: v for k, v in _record().items() if k != missing}
    for missing in _record()
]
BAD += [
    {**_record(), key: value}
    for key, value in [
        ("record", ""), ("record", "unrelated-review"), ("record", []),
        ("date", "2026-02-30"), ("date", "20261028"),
        ("date", "2026-10-29"), ("evidence", "missing-test.py"),
        ("evidence", ""), ("by", " "), ("verdict", ""),
        ("commit", "a" * 40), ("commit", None),
        ("by", "review at " + "a" * 12),
        ("verdict", "accepted " + "B" * 40),
        ("extra", {"commit": "a" * 40}),
    ]
]


@pytest.mark.parametrize("validator", ["overlay", "shared"])
@pytest.mark.parametrize("reviewer", BAD)
def test_both_schemas_reject_malformed_or_revision_bearing_records(
    monkeypatch, validator, reviewer
) -> None:
    with pytest.raises(AssertionError):
        _validate(monkeypatch, reviewer, validator)


def test_public_transport_records_use_named_provenance() -> None:
    entries = overlay._transport_entries()
    assert len(entries) == 4
    for entry in entries:
        assert set(entry["reviewer"]) == set(_record()), entry["id"]
        assert entry["reviewer"]["record"] == RECORD


@pytest.mark.parametrize("field", ["commit", "by", "evidence", "verdict", "extra"])
def test_hygiene_detects_revision_in_any_transport_review_field(tmp_path, field) -> None:
    entry = copy.deepcopy(overlay._transport_entries()[0])
    entry["reviewer"] = _record()
    path = tmp_path / "intended-differences.json"
    path.write_text(json.dumps({"differences": [entry]}))
    assert hygiene._hits([path], tmp_path) == []
    entry["reviewer"][field] = "reviewed " + "a" * 40
    path.write_text(json.dumps({"differences": [entry]}))
    assert hygiene._hits([path], tmp_path), field
