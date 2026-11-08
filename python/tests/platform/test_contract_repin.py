"""Repinning validates all input identities before writing and reports schema drift."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ._gates_support import REPO, load


def repinner(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "scripts/platform"))
    return load("contract_repinner", "scripts/platform/repin_contracts.py")


def test_digest_file_and_prefixed_digest_are_equivalent(monkeypatch, tmp_path):
    module = repinner(monkeypatch)
    source = tmp_path / "contract.json"
    source.write_text('{}\n')
    checksum = module.digest(source)
    sidecar = tmp_path / "contract.sha256"
    sidecar.write_text(checksum + "  contract.json\n")
    assert module.checked(source, sidecar) == checksum
    assert module.checked(source, "sha256:" + checksum) == checksum
    with pytest.raises(ValueError, match="mismatch"):
        module.checked(source, "0" * 64)


def test_invalid_digest_changes_no_checkout_files(monkeypatch, tmp_path):
    module = repinner(monkeypatch)
    source = tmp_path / "contract.json"
    source.write_text('{}\n')
    checksum = tmp_path / "contract.sha256"
    checksum.write_text("0" * 64)
    before = {str(p): p.read_bytes() for p in tmp_path.iterdir()}
    args = SimpleNamespace(root=tmp_path, ee_openapi=source, ee_sha256=checksum)
    with pytest.raises(ValueError, match="digest mismatch"):
        module.repin(args)
    assert {str(p): p.read_bytes() for p in tmp_path.iterdir()} == before


def test_drift_in_a_referenced_schema_marks_its_namespace_not_evaluated():
    module = load("contract_drift_test", "scripts/platform/contract_drift.py")
    doc = {"paths": {"/things": {"get": {"operationId": "listThings", "responses": {
        "200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Item"}}}}
    }}}}, "components": {"schemas": {"Item": {"type": "string"}}}}
    before = module.inventory(doc, {"listThings": ["things.list"]})
    assert module.compare(before, module.inventory(doc, {"listThings": ["things.list"]})) == {}
    doc["components"]["schemas"]["Item"]["type"] = "integer"
    drift = module.compare(before, module.inventory(doc, {"listThings": ["things.list"]}))
    assert drift == {"things": {"verdict": "NOT-EVALUATED", "added": [], "removed": [], "changed": ["things.list"]}}


def test_drift_lists_additions_and_removals():
    module = load("contract_drift_sets", "scripts/platform/contract_drift.py")
    rows = {"things.list": {"namespace": "things", "signature": "fixture"}}
    assert module.compare({}, rows)["things"]["added"] == ["things.list"]
    assert module.compare(rows, {})["things"]["removed"] == ["things.list"]


def test_reference_cycles_are_finite_and_external_references_are_refused():
    module = load("contract_drift_refs", "scripts/platform/contract_drift.py")
    doc = {"components": {"schemas": {"Item": {"type": "object", "properties": {"child": {"$ref": "#/components/schemas/Item"}}}}}}
    assert module.signature(doc, {"$ref": "#/components/schemas/Item"})
    with pytest.raises(ValueError, match="non-local"):
        module.signature(doc, {"$ref": "https://example.invalid/schema"})
