"""The older base pin and separately sourced lifecycle extension remain independent."""
import json

import pytest

from ._gates_support import REPO, load


def tooling(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "scripts/platform"))
    return load("lifecycle_contract_source", "scripts/platform/lifecycle_contracts.py")


def test_extension_projection_requires_every_recorded_upstream_operation(monkeypatch):
    module = tooling(monkeypatch)
    doc = {"swagger": "2.0", "paths": {"/thing": {"get": {"operationId": "thing"}}}}
    assert set(module.project_source(doc, {"operations": ["GET /thing"]})["paths"]) == {"/thing"}
    with pytest.raises(KeyError):
        module.project_source(doc, {"operations": ["POST /thing"]})


def test_all_recorded_amendments_are_required_and_applied_in_order(monkeypatch, tmp_path):
    module = tooling(monkeypatch)
    directory = tmp_path / "openapi/sdk"
    directory.mkdir(parents=True)
    route = "POST /thing"
    def write(name, value):
        path = directory / name
        path.write_text(json.dumps(value))
        return path
    write("lifecycle-source.json", {"operations": [route]})
    base = write("base.json", {"swagger": "2.0", "paths": {"/thing": {"post": {"operationId": "old"}}}})
    write("release-gate-source.json", {"operations": [route], "backend_revision": "fixture"})
    amendment = write("release-gate.json", {"swagger": "2.0", "paths": {"/thing": {"post": {"operationId": "new"}}}})
    with pytest.raises(ValueError, match="every recorded"):
        module.stage(tmp_path, base)
    result = module.stage(tmp_path, base, [amendment])
    assert result["paths"]["/thing"]["post"]["operationId"] == "new"
    assert result["x-extension-sources"]["release-gate"]["pin"] == "openapi/sdk/release-gate-source.json"
    assert result["x-extension-sources"]["release-gate"]["sha256"].startswith("sha256:")


def test_extension_never_replaces_base_operations_or_schema_definitions(monkeypatch):
    module = tooling(monkeypatch)
    base = {"paths": {"/thing": {"get": {"operationId": "current"}}}, "definitions": {"Item": {"type": "integer"}}}
    extension = {"paths": {"/thing": {"get": {"operationId": "old"}},
                           "/extra": {"post": {"schema": {"$ref": "#/definitions/Item"}}}},
                 "definitions": {"Item": {"type": "string"}}}
    merged = module.merge(base, extension)
    assert merged["paths"]["/thing"]["get"]["operationId"] == "current"
    assert merged["definitions"]["Item"] == {"type": "integer"}
    assert merged["paths"]["/extra"]["post"]["schema"]["$ref"] == "#/definitions/ContractExtensionItem"
    assert merged["definitions"]["ContractExtensionItem"] == {"type": "string"}
