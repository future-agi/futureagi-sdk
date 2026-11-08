"""A credential hide removes the exact platform read set, not just its facade."""
import hashlib
import json
from pathlib import Path
import runpy
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
MODULE = runpy.run_path(str(ROOT / "scripts/connectors/hide_platform_credentials.py"))
READS = {"platform.credentials.bindings", "platform.credentials.get", "platform.credentials.list"}


def canonical_projection(spec, scope):
    script = """
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
const {scopeContract, loadRules} = await import(pathToFileURL(process.argv[2]));
const input = JSON.parse(readFileSync(0, 'utf8'));
const result = scopeContract(input.spec, input.scope, {...loadRules(), wording: []});
process.stdout.write(JSON.stringify(result.spec, null, 2) + '\\n');
"""
    return subprocess.check_output(
        ["node", "--input-type=module", "-e", script, "-", str(ROOT / "scripts/platform/scope-filter.mjs")],
        input=json.dumps({"spec": spec, "scope": scope}).encode(),
    )


def test_hidden_projection_is_canonical_and_prunes_credential_only_components(tmp_path):
    platform = tmp_path / "openapi/platform"
    (platform / "generated").mkdir(parents=True)
    for name in ("scope.json", "source.json", "generated/futureagi-platform.openapi.json", "generated/futureagi-platform.operations.txt"):
        (platform / name).write_bytes((ROOT / "openapi/platform" / name).read_bytes())
    original = json.loads((platform / "generated/futureagi-platform.openapi.json").read_text())
    MODULE["hide_platform_credentials"](tmp_path)
    scope = json.loads((platform / "scope.json").read_text())
    projection = (platform / "generated/futureagi-platform.openapi.json").read_bytes()
    assert projection == canonical_projection(original, scope)
    spec = json.loads(projection)
    for name in ("ListWorkspaceCredentialsResponse", "GetWorkspaceCredentialResponse", "ListWorkspaceCredentialBindingsResponse"):
        assert name not in spec["components"].get("schemas", {})
    assert not any(tag["name"] == "Workspace Credentials" for tag in spec["tags"])


def fixture(tmp_path):
    platform = tmp_path / "openapi/platform"
    (platform / "generated").mkdir(parents=True)
    names = ["platform.capabilities.get", *sorted(READS)]
    spec = {
        "openapi": "3.1.0", "info": {"version": "1"}, "security": [],
        "tags": [{"name": "Capabilities"}, {"name": "Workspace Credentials"}],
        "paths": {"/fixture/" + name: {"get": {
            "operationId": "op" + str(index),
            "tags": ["Capabilities" if index == 0 else "Workspace Credentials"],
            "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {
                "$ref": "#/components/schemas/" + ("Retained" if index == 0 else "CredentialOnly")
            }}}}},
            "x-omega-sdk": {"family": "platform", "method": name.split(".", 1)[1]},
        }} for index, name in enumerate(names)},
        "components": {"schemas": {"Retained": {"type": "object"}, "CredentialOnly": {"type": "object"}, "Unreachable": {"type": "object"}}},
    }
    files = {
        "scope.json": {"operations": names},
        "source.json": {"source_digest": "sha256:" + "0" * 64, "scoped": {"sha256": hashlib.sha256((json.dumps(spec) + "\n").encode()).hexdigest()}},
        "generated/futureagi-platform.openapi.json": spec,
    }
    for name, value in files.items():
        (platform / name).write_text(json.dumps(value) + "\n")
    (platform / "generated/futureagi-platform.operations.txt").write_text("\n".join(name + " GET /fixture/" + name + " op" for name in names) + "\n")
    return platform, spec


def test_credential_hide_removes_exact_scope_and_rebinds_digest(tmp_path):
    platform, original = fixture(tmp_path)
    MODULE["hide_platform_credentials"](tmp_path)
    scope = json.loads((platform / "scope.json").read_text())
    assert scope["operations"] == ["platform.capabilities.get"]
    spec_path = platform / "generated/futureagi-platform.openapi.json"
    assert spec_path.read_bytes() == canonical_projection(original, scope)
    projection = json.loads(spec_path.read_text())
    assert set(projection["paths"]) == {"/fixture/platform.capabilities.get"}
    assert set(projection["components"]["schemas"]) == {"Retained"}
    assert projection["tags"] == [{"name": "Capabilities"}]
    source = json.loads((platform / "source.json").read_text())
    assert source["source_digest"] == "sha256:" + "0" * 64
    assert source["scoped"]["sha256"] == hashlib.sha256(spec_path.read_bytes()).hexdigest()
    assert (platform / "generated/futureagi-platform.operations.txt").read_text().splitlines() == ["platform.capabilities.get GET /fixture/platform.capabilities.get op0"]
    before = spec_path.read_bytes()
    MODULE["hide_platform_credentials"](tmp_path)
    assert spec_path.read_bytes() == before


def test_credential_hide_refuses_partial_scope(tmp_path):
    platform, _ = fixture(tmp_path)
    file = platform / "scope.json"
    scope = json.loads(file.read_text())
    scope["operations"].remove("platform.credentials.get")
    file.write_text(json.dumps(scope))
    before = (platform / "generated/futureagi-platform.openapi.json").read_bytes()
    with pytest.raises(ValueError, match="incomplete"):
        MODULE["hide_platform_credentials"](tmp_path)
    assert (platform / "generated/futureagi-platform.openapi.json").read_bytes() == before
