"""Commit-pinned OpenAPI/MCP sync and release-sync provenance regressions."""

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sdkgen import check_mcp_parity, sync_contract  # noqa: E402


@pytest.fixture
def sources(tmp_path, monkeypatch):
    catalog = tmp_path / "sdkgen/catalog/operations.yaml"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(yaml.safe_dump({"operations": [{
        "id": "fixture.read", "operation": {"method": "GET", "path": "/fixture/"},
        "surfaces": {"sdk": {}, "mcp": {"name": "synthetic_read"}},
    }]}))
    source = tmp_path / "source.json"
    source.write_text(json.dumps({
        "swagger": "2.0", "info": {"title": "Synthetic", "version": "1"},
        "paths": {"/fixture/": {"get": {"responses": {"200": {"schema": {"$ref": "#/definitions/Fixture"}}}}}},
        "definitions": {"Fixture": {"type": "object"}},
    }))
    tools = tmp_path / "tools.json"
    tools.write_text(json.dumps({"tools": [{"name": "synthetic_read"}]}))
    output = tmp_path / "sdkgen/contracts/swagger.json"
    for module in (sync_contract, check_mcp_parity):
        monkeypatch.setattr(module, "ROOT", tmp_path)
        monkeypatch.setattr(module, "CATALOG", catalog)
    monkeypatch.setattr(sync_contract, "OUT", output)
    monkeypatch.setattr(sync_contract, "VERSION_FILE", output.parent / "BACKEND_VERSION")
    monkeypatch.setattr(check_mcp_parity, "BACKEND_VERSION", output.parent / "BACKEND_VERSION")
    return source, tools, output


def invoke(monkeypatch, source, *options):
    monkeypatch.setattr(sys, "argv", ["sync_contract", str(source), *options])
    sync_contract.main()


def test_commit_sync_binds_sources_and_parity_works_without_network(sources, monkeypatch):
    source, tools, output = sources
    invoke(monkeypatch, source, "--backend-commit", "a" * 40, "--mcp-tools", str(tools))
    provenance = json.loads(output.with_name("SOURCE.json").read_text())
    assert provenance == {
        "backend_commit": "a" * 40,
        "openapi_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "mcp_sha256": hashlib.sha256(tools.read_bytes()).hexdigest(),
    }
    assert json.loads(output.read_text())["x-source-sha256"] == provenance["openapi_sha256"]
    assert json.loads(output.with_name("mcp-tools.json").read_text()) == {
        "x-source-sha256": provenance["mcp_sha256"], "tools": [{"name": "synthetic_read"}],
    }
    def unavailable(*args, **kwargs):
        raise AssertionError("Commit-pinned parity must be offline")
    monkeypatch.setattr(check_mcp_parity.urllib.request, "urlopen", unavailable)
    assert check_mcp_parity.main([]) == 0
    invoke(monkeypatch, source, "--backend-version", "v1.99.0")
    assert output.with_name("BACKEND_VERSION").read_text() == "v1.99.0\n"
    assert not output.with_name("SOURCE.json").exists()
    assert not output.with_name("mcp-tools.json").exists()


@pytest.mark.parametrize("options", [
    ("--backend-commit", "a" * 40),
    ("--mcp-tools", "tools.json"),
    ("--backend-commit", "not-a-sha", "--mcp-tools", "tools.json"),
])
def test_incomplete_provenance_cannot_replace_contract(sources, monkeypatch, options):
    source, _, output = sources
    with pytest.raises(SystemExit):
        invoke(monkeypatch, source, *options)
    assert not output.exists()


def test_duplicate_mcp_names_fail_before_contract_write(sources, monkeypatch):
    source, tools, output = sources
    tools.write_text(json.dumps({"tools": [{"name": "same"}, {"name": "same"}]}))
    with pytest.raises(SystemExit):
        invoke(monkeypatch, source, "--backend-commit", "b" * 40, "--mcp-tools", str(tools))
    assert not output.exists()


def test_pinned_consumption_contract_declares_exclusive_auth_and_wire_identity():
    root = Path(__file__).resolve().parents[3] / "sdkgen/contracts"
    contract = json.loads((root / "swagger.json").read_text())
    provenance = json.loads((root / "SOURCE.json").read_text())
    assert contract["x-source-sha256"] == provenance["openapi_sha256"]
    assert json.loads((root / "mcp-tools.json").read_text())["x-source-sha256"] == provenance["mcp_sha256"]
    for path, item in contract["paths"].items():
        if path.startswith(("/model-hub/skills/contexts/", "/model-hub/skills/consumption/")) and "credentials" not in path:
            for method in ("get", "post"):
                if method in item:
                    assert item[method]["security"] == [{"ContextCredential": []}]
                    if "versions" in path:
                        assert any(p["name"] == "X-Context-Resolution" and p["required"] for p in item[method]["parameters"])
    manifest = contract["definitions"]["SkillsContextConsumptionManifest"]["properties"]
    assert {"resource_id", "kind", "resolution_id", "resolution_expires_at"} <= manifest.keys()
    assert not {"context_id", "skill_id"} & manifest.keys()
