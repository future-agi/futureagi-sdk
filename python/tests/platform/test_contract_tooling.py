"""Contract tooling fails closed on missing coverage and admission conflicts."""
import copy
import json
from pathlib import Path

import pytest

from ._gates_support import PLATFORM, SCOPED, load, read_json


def test_missing_twin_is_red_unless_explicitly_not_offered():
    checker = load("contract_wrapper_checker", "scripts/platform/wrapper_map.py")
    mapping = read_json(PLATFORM / "wrapper-map.json")
    spec = read_json(SCOPED)
    method = mapping["operations"]["runs.send"]["methods"][0]
    method.pop("ts")
    assert any("missing language twin" in f for f in checker.check(mapping, spec))
    method["not_offered"] = {"ts": {"status": "NOT-OFFERED", "reason": "Unavailable in this language"}}
    assert checker.check(mapping, spec) == []
    method["not_offered"]["ts"]["reason"] = ""
    assert any("missing language twin" in f for f in checker.check(mapping, spec))


def test_excluded_operation_rejects_a_public_wrapper():
    checker = load("ledger_wrapper_checker", "scripts/platform/wrapper_map.py")
    mapping = read_json(PLATFORM / "wrapper-map.json")
    spec = read_json(SCOPED)
    rows = [{"sdk_name": "runs.send", "disposition": "excluded", "authority": "contract policy"}]
    assert any("ledger excludes" in f for f in checker.check(mapping, spec, exclusions=rows))
    op = checker.operations(spec)["runs.send"]
    rows = [{"path": op["path"], "method": op["method"], "namespace": "excluded"}]
    assert any("ledger excludes" in f for f in checker.check(mapping, spec, exclusions=rows))


def test_ledger_absence_is_explicit_and_invalid_ledger_is_not_absence(tmp_path):
    helper = load("contract_admission_helper", "scripts/platform/wrapper_admission.py")
    absent = tmp_path / "missing.json"
    rows, notice = helper.read_ledger(absent)
    assert rows == [] and "empty exclusion list" in notice
    absent.write_text('{"incorrect": []}')
    with pytest.raises(ValueError):
        helper.read_ledger(absent)
    absent.write_text('{"operations": [{"status": "excluded"}]}')
    with pytest.raises(ValueError):
        helper.read_ledger(absent)


def test_contract_case_generation_is_current_and_complete(monkeypatch):
    monkeypatch.syspath_prepend(str(PLATFORM.parents[1] / "scripts/platform"))
    generator = load("contract_cases_generator", "scripts/platform/contract_cases.py")
    generated = generator.generate()
    assert generated == read_json(generator.ROOT / generator.OUTPUT)
    assert len(generated["operations"]) > 77
    expected = {"platform", "core", "catalog", "tracing"}
    features = read_json(generator.ROOT / "openapi/connectors/features.json")
    if any(features[name] for name in ("mcp_core", "data_integrations", "credential_reads")):
        expected.add("connectors")
    if (generator.ROOT / "openapi/fa-mgmt/generated/spec.json").exists():
        expected.add("management")
    assert {r["adapter"] for r in generated["operations"]} == expected
    assert len({r["id"] for r in generated["operations"]}) == len(generated["operations"])
