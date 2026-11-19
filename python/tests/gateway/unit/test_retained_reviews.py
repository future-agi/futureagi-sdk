"""Public provenance is bound to the existing reviewed comparison rules."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from parity._fixtures import load
from parity._review import assert_review_record

ENTRIES = [e for e in load("intended-differences.json")["differences"]
           if e["status"] == "proven" and not e["id"].startswith("PY-4.0-")]


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["id"])
def test_retained_review_accepts_exact_record(entry):
    assert_review_record(entry)


@pytest.mark.parametrize("field,value", [("record", "unrelated"), ("by", "someone else"),
                                         ("verdict", ""), ("commit", "a" * 40)])
def test_review_identity_cannot_be_swapped(field, value):
    entry = copy.deepcopy(ENTRIES[0])
    entry["reviewer"][field] = value
    with pytest.raises(AssertionError):
        assert_review_record(entry)


def test_review_cannot_cover_different_rules():
    entry = copy.deepcopy(ENTRIES[0])
    entry["match"].append({"path": "*"})
    with pytest.raises(AssertionError, match="reviewed rules changed"):
        assert_review_record(entry)


def test_metadata_projector_does_not_rewrite_wire_payloads_or_rules():
    root = Path(__file__).resolve().parents[4]
    spec = importlib.util.spec_from_file_location("projection", root / "scripts/gateway/project_public_metadata.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    old = {"source": {"commit": "old-source"}, "status": "proven",
           "match": [{"new": "old-source"}], "frames": ["old-source"],
           "test_id": "test_old_source", "cases": [{"name": "old-source"}]}
    new = module.project(old, {"old-source": "named-source"})
    assert new["source"] == {"record": "named-source"}
    # A short source id can also prefix a real content digest: never change that digest.
    import json
    short = "a1" * 4
    fixture = {"summary": short, "match": [{"new": "^" + short * 8 + "$"}]}
    rendered = json.loads(module.render(json.dumps(fixture), {short: "named-source"}))
    assert rendered["summary"] == "named-source"
    assert rendered["match"] == fixture["match"]
    with pytest.raises(ValueError, match="non-metadata"):
        module.render(json.dumps({"cases": [{"summary": short}]}), {short: "named-source"})
    assert {k: v for k, v in new.items() if k != "source"} == {
        k: v for k, v in old.items() if k != "source"}
