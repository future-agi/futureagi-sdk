"""Repin integration with stub generators; no backend or tool installation."""
from types import SimpleNamespace

import pytest

from ._gates_support import REPO, load
from .test_contract_catalog_source import inputs as catalog_inputs
from .test_contract_management import inputs as management_inputs


def fixture(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(REPO / "scripts/platform"))
    module = load("repin_flow", "scripts/platform/repin_contracts.py")
    catalog_module = load("repin_catalog_flow", "scripts/platform/catalog_contracts.py")
    generator = load("repin_cases_flow", "scripts/platform/contract_cases.py")
    root, inputs = tmp_path / "repo", tmp_path / "inputs"
    catalog, swagger = catalog_inputs()
    ee = {"openapi": "3.0.3", "paths": {"/unwrapped": {"get": {
        "operationId": "unwrapped", "x-omega-sdk": {"family": "things", "method": "list"}}}}}
    for folder in ("scripts", "python/fi/generated", "typescript/futureagi/src/generated"):
        (root / folder).mkdir(parents=True)
    def write(path, data):
        module.write(root / path, data)
    write("openapi/platform/generated/futureagi-platform.openapi.json", ee)
    write("openapi/platform/source.json", {"scoped": {}})
    write("openapi/platform/wrapper-map.json", {"operations": {}})
    write("openapi/contract-offerings.json", {"modules": {"management": {
        "status": "NOT-OFFERED", "owner": "management", "reason": "Not integrated"}}})
    write("openapi/sdk/generated/futureagi-sdk.openapi.json", {"paths": {}})
    write("openapi/sdk/wrapper-map.json", {})
    write("openapi/catalog/operations.json", catalog)
    write("openapi/catalog/source.json", catalog_module.project(swagger, catalog))
    write("openapi/contract-inputs.json", {"handle_fixtures": {}, "module_absences": [], "namespace_absences": []})
    write("openapi/catalog/models-source.json", {"path": "/models", "method": "GET",
        "operation_id": "models", "overrides": {"query": []}, "response_schema": {"type": "object"}})
    write("openapi/connectors/wrapper-map.json", {"sources": {}, "operations": {}})
    write("openapi/connectors/features.json", dict.fromkeys(
        ("mcp_core", "oauth_connect", "data_integrations", "slack_channels", "credential_reads"), False))
    write("openapi/tracing/source.json", {"paths": {}})
    write("openapi/tracing/wrapper-map.json", {"operations": []})
    module.write(inputs / "ee.json", ee)
    module.write(inputs / "fa.json", swagger)
    module.write(inputs / "gateway.json", {"properties": {"config": {"type": "object"}}})
    (inputs / "ee.sha256").write_text(module.digest(inputs / "ee.json"))
    args = SimpleNamespace(root=root, ee_openapi=inputs / "ee.json", ee_sha256=inputs / "ee.sha256",
        ee_revision="fixture", fa_swagger=inputs / "fa.json", fa_certificate=None,
        gateway_schema=inputs / "gateway.json", gateway_sha256=module.digest(inputs / "gateway.json"),
        fa_management_generator=None, check=True, report=tmp_path / "report.json")
    def run(stage, *command):
        if "scripts/platform/contract_cases.py" in command:
            module.write(stage / generator.OUTPUT, generator.generate(stage))
        elif "scripts/management-fixture.sh" in command:
            doc, mapping = management_inputs()
            module.write(stage / module.MANAGEMENT_SPEC, doc)
            module.write(stage / module.MANAGEMENT_MAP, mapping)
    monkeypatch.setattr(module, "run", run)
    return module, args, run


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_repin_reports_catalog_drift_even_when_core_generation_refuses(monkeypatch, tmp_path):
    module, args, run = fixture(monkeypatch, tmp_path)
    fa = module.read(args.fa_swagger)
    fa["paths"]["/moved/"] = {"post": fa["paths"].pop("/tracer/dashboard/")["get"]}
    module.write(args.fa_swagger, fa)
    def failing(stage, *command):
        if "scripts/generate-oss-sdk.sh" in command:
            raise ValueError("core generation refused")
        run(stage, *command)
    monkeypatch.setattr(module, "run", failing)
    before = snapshot(args.root)
    with pytest.raises(ValueError, match="core generation refused"):
        module.repin(args)
    report = module.read(args.report)
    assert report["namespaces"]["tracing"]["changed"] == ["tracing.dashboards.list"]
    assert report["namespaces"]["tracing"]["verdict"] == "NOT-EVALUATED"
    assert snapshot(args.root) == before


def test_management_hook_can_emit_a_contract_candidate_and_second_repin_is_noop(monkeypatch, tmp_path):
    module, args, _ = fixture(monkeypatch, tmp_path)
    (args.root / "scripts/management-fixture.sh").write_text("# fixture generator\n")
    args.fa_management_generator = "scripts/management-fixture.sh"
    args.check = False
    assert module.repin(args) == 0
    cases = module.read(args.root / "tests/fixtures/contracts/operations.json")
    assert any(row["adapter"] == "management" for row in cases["operations"])
    report = module.read(args.report)
    assert "tests owed" in report["management"]
    assert report["namespaces"]["gateway"]["verdict"] == "NOT-EVALUATED"
    args.check = True
    assert module.repin(args) == 0
    assert module.read(args.report)["status"] == "NO-OP"


def test_repin_inventory_excludes_tool_caches_but_tracks_generated_code(monkeypatch, tmp_path):
    module, args, _ = fixture(monkeypatch, tmp_path)
    cache = args.root / "python/fi/generated/openapi_client/.ruff_cache/0.17/entry"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"temporary-path-specific-cache")
    code = args.root / "python/fi/generated/openapi_client/model.py"
    code.write_text("VALUE = 1\n")
    before = module.files(args.root)
    cache.write_bytes(b"different-temporary-path")
    assert module.files(args.root) == before
    code.write_text("VALUE = 2\n")
    assert module.files(args.root) != before
    assert all(".ruff_cache" not in name for name in before)


def test_missing_catalog_identity_refuses_apply_without_checkout_mutation(monkeypatch, tmp_path):
    module, args, _ = fixture(monkeypatch, tmp_path)
    fa = module.read(args.fa_swagger)
    fa["paths"] = {"/other/": {"get": {"operationId": "other"}}}
    module.write(args.fa_swagger, fa)
    args.check = False
    before = snapshot(args.root)
    with pytest.raises(ValueError, match="missing catalog operation"):
        module.repin(args)
    assert snapshot(args.root) == before
    assert module.read(args.report)["namespaces"]["tracing"]["removed"] == ["tracing.dashboards.list"]
