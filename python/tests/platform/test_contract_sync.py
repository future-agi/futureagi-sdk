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


@pytest.mark.parametrize("value", [
    None,
    [],
    {},
    {"tools": None},
    {"tools": [None]},
    {"tools": [{"name": None}]},
    {"tools": [{"name": "  "}]},
])
def test_explicit_invalid_mcp_is_not_omission_and_preserves_every_output(
    sources, monkeypatch, value
):
    source, tools, output = sources
    paths = [
        output,
        output.with_name("SOURCE.json"),
        output.with_name("mcp-tools.json"),
        output.with_name("BACKEND_VERSION"),
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"existing:{path.name}")
    tools.write_text(json.dumps(value))
    before = {path: path.read_bytes() for path in paths}
    with pytest.raises(SystemExit):
        invoke(monkeypatch, source, "--backend-commit", "c" * 40, "--mcp-tools", str(tools))
    assert {path: path.read_bytes() for path in paths} == before


def test_malformed_mcp_json_preserves_existing_outputs(sources, monkeypatch):
    source, tools, output = sources
    paths = [output, output.with_name("SOURCE.json"), output.with_name("mcp-tools.json")]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"existing:{path.name}")
    tools.write_text("null {")
    before = {path: path.read_bytes() for path in paths}
    with pytest.raises(SystemExit):
        invoke(monkeypatch, source, "--backend-commit", "d" * 40, "--mcp-tools", str(tools))
    assert {path: path.read_bytes() for path in paths} == before


CONTRACTS = Path(__file__).resolve().parents[3] / "sdkgen/contracts"
CONTEXTS = "/model-hub/skills/contexts/"
CONSUMPTION = "/model-hub/skills/consumption/"
VERSION = "{resource_id}/versions/{number}/"
RESOLVE = {("get", root + "resolve/") for root in (CONTEXTS, CONSUMPTION)}
LEASED = {
    (method, root + VERSION + endpoint)
    for root in (CONTEXTS, CONSUMPTION)
    for method, endpoint in (("get", "manifest/"), ("get", "files/"), ("post", "access-check/"))
}
INSPECTION = {("get", CONTEXTS + suffix) for suffix in (
    "", "{context_id}/", "{context_id}/versions/", "{context_id}/versions/{number}/inspection/",
)}
ISSUE = ("post", CONTEXTS + "credentials/")
CREDENTIAL_ADMIN = {ISSUE, ("get", CONTEXTS + "credentials/"), ("delete", CONTEXTS + "credentials/{credential_id}/")}
ISOLATED_AUTH = [{"ContextCredential": []}]
PLATFORM_AUTH = [{"X-Api-Key": []}, {"X-Secret-Key": []}]


def assert_context_contract(contract):
    """Classify every operation in the *SDK slice*, not every upstream product route."""
    routes = {
        (method, path): operation
        for path, item in contract["paths"].items() if path.startswith((CONTEXTS, CONSUMPTION))
        for method, operation in item.items() if method != "parameters"
    }
    assert routes.keys() == RESOLVE | LEASED | INSPECTION | CREDENTIAL_ADMIN, "context route inventory changed"
    assert contract["security"] == PLATFORM_AUTH
    for scheme, wire_name in (("ContextCredential", "Authorization"), ("X-Api-Key", "X-Api-Key"), ("X-Secret-Key", "X-Secret-Key")):
        definition = contract["securityDefinitions"][scheme]
        assert (definition["type"], definition["in"], definition["name"]) == ("apiKey", "header", wire_name)

    for route, op in routes.items():
        _, path = route
        expected = ISOLATED_AUTH if route in RESOLVE | LEASED else PLATFORM_AUTH
        assert op.get("security", contract["security"]) == expected, route
        # Check path-level parameters too, so an inherited lease or auth header can't slip in.
        parameters = contract["paths"][path].get("parameters", []) + op.get("parameters", [])
        headers = [p for p in parameters if p["in"] == "header"]
        header = "X-Context-Resolution" if route in LEASED else "Idempotency-Key" if route == ISSUE else None
        assert [p["name"] for p in headers] == ([header] if header else []), route
        if headers:
            assert headers[0].get("required") is True and headers[0].get("type") == "string", route
            assert headers[0].get("format") == "uuid", route
        assert not any(p["name"].lower() == "x-context-resolution" and p["in"] != "header" for p in parameters), route


def test_pinned_consumption_contract_declares_exclusive_auth_and_wire_identity():
    contract = json.loads((CONTRACTS / "swagger.json").read_text())
    source = CONTRACTS / "SOURCE.json"
    assert source.is_file() == (CONTRACTS / "mcp-tools.json").is_file()
    if "x-skills-only-baseline-sha256" in contract or source.exists():
        provenance = json.loads(source.read_text())
        assert contract["x-source-sha256"] == provenance["openapi_sha256"]
        assert json.loads((CONTRACTS / "mcp-tools.json").read_text())["x-source-sha256"] == provenance["mcp_sha256"]
        if "x-skills-only-baseline-sha256" in contract:
            assert contract["x-skills-only-baseline-sha256"] == provenance["non_skills_slice_sha256"]
    assert_context_contract(contract)
    manifest = contract["definitions"]["SkillsContextConsumptionManifest"]["properties"]
    assert {"resource_id", "kind", "resolution_id", "resolution_expires_at"} <= manifest.keys()
    assert not {"context_id", "skill_id"} & manifest.keys()


@pytest.fixture
def pinned_contract():
    return json.loads((CONTRACTS / "swagger.json").read_text())


@pytest.mark.parametrize("method,path", sorted(RESOLVE | LEASED | INSPECTION | CREDENTIAL_ADMIN))
def test_context_inventory_rejects_missing_operation(pinned_contract, method, path):
    del pinned_contract["paths"][path][method]
    with pytest.raises(AssertionError, match="inventory"):
        assert_context_contract(pinned_contract)


@pytest.mark.parametrize("method,path", [("patch", CONTEXTS), ("get", CONSUMPTION + "future/")])
def test_context_inventory_rejects_unclassified_operation(pinned_contract, method, path):
    pinned_contract["paths"].setdefault(path, {})[method] = {"security": PLATFORM_AUTH}
    with pytest.raises(AssertionError, match="inventory"):
        assert_context_contract(pinned_contract)


@pytest.mark.parametrize("method,path,reclassified", [
    ("get", CONTEXTS + "resolve/", PLATFORM_AUTH),
    ("post", CONSUMPTION + VERSION + "access-check/", ISOLATED_AUTH + PLATFORM_AUTH),
    ("get", CONTEXTS, ISOLATED_AUTH),
    (*ISSUE, ISOLATED_AUTH),
    ("delete", CONTEXTS + "credentials/{credential_id}/", []),
    ("get", CONTEXTS + "{context_id}/versions/", [{}]),
])
def test_context_contract_rejects_auth_reclassification(pinned_contract, method, path, reclassified):
    pinned_contract["paths"][path][method]["security"] = reclassified
    with pytest.raises(AssertionError):
        assert_context_contract(pinned_contract)


@pytest.mark.parametrize("change", [{"in": "query"}, {"required": False}, {"type": "integer"}])
def test_context_contract_rejects_changed_lease(pinned_contract, change):
    params = pinned_contract["paths"][CONSUMPTION + VERSION + "files/"]["get"]["parameters"]
    next(p for p in params if p["name"] == "X-Context-Resolution").update(change)
    with pytest.raises(AssertionError):
        assert_context_contract(pinned_contract)


def test_skills_only_sync_preserves_baseline_and_rejects_shared_model_drift(sources, monkeypatch):
    import copy

    source, _, output = sources
    baseline = json.loads(source.read_text())
    spec = copy.deepcopy(baseline)
    spec["paths"]["/fixture/"]["get"]["description"] = "unrelated upstream edit"
    skill = "/model-hub/skills/new-reader/"
    spec["paths"][skill] = copy.deepcopy(spec["paths"]["/fixture/"])
    catalog = yaml.safe_load(sync_contract.CATALOG.read_text())
    catalog["operations"].append({"id": "skills.reader", "operation": {"method": "GET", "path": skill}})
    sync_contract.CATALOG.write_text(yaml.safe_dump(catalog))
    source.write_text(json.dumps(spec))
    digest = hashlib.sha256(json.dumps(baseline).encode()).hexdigest()
    sync_contract.sync(source, baseline=baseline, baseline_hash=digest)
    result = output.read_bytes()
    sliced = json.loads(result)
    assert sliced["x-skills-only-baseline-sha256"] == digest
    assert sliced["paths"]["/fixture/"] == baseline["paths"]["/fixture/"]
    assert sliced["paths"][skill] == spec["paths"][skill]
    spec["definitions"]["Fixture"]["required"] = ["changed"]
    source.write_text(json.dumps(spec))
    with pytest.raises(SystemExit, match="definitions disagree"):
        sync_contract.sync(source, baseline=baseline, baseline_hash=digest)
    assert output.read_bytes() == result
