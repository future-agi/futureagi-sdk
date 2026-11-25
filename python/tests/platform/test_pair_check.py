"""sdkgen/pair_check.py: the scoped slice against one product commit, offline."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "sdkgen"))

import pair_check as pc  # noqa: E402

FOO = {"type": "object", "properties": {"bar": {"$ref": "#/definitions/Bar"}}}
BAR = {"type": "object", "properties": {"name": {"type": "string"}}}


def spec():
    return {
        "swagger": "2.0",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/epochs/{id}/": {
                "parameters": [{"name": "id", "in": "path", "required": True, "type": "string"}],
                "get": {"operationId": "epochs_read", "responses": {"200": {"description": "", "schema": {"$ref": "#/definitions/Foo"}}}},
            },
            "/tracer/sql-query/catalog/": {
                "get": {"operationId": "sql_catalog", "responses": {"200": {"description": "", "schema": {"$ref": "#/definitions/Bar"}}}},
            },
            "/other/": {"get": {"operationId": "other", "responses": {"200": {"description": "ok"}}}},
        },
        "definitions": {"Foo": FOO, "Bar": BAR},
    }


def catalog():
    return {"operations": [
        {"id": "simulation.epochs.get", "description": "Return one Epoch.",
         "operation": {"method": "GET", "path": "/epochs/{id}/"},
         "surfaces": {"sdk": {}, "mcp": {"name": "get_epoch", "group": "epoch", "access": "read"}}},
        {"id": "sql.get_catalog", "description": "SQL sources.",
         "operation": {"method": "GET", "path": "/tracer/sql-query/catalog/"},
         "surfaces": {"sdk": {}, "mcp": {"name": "get_sql_catalog", "group": "observability", "access": "read"}}},
        {"id": "other.get", "description": "Other.", "operation": {"method": "GET", "path": "/other/"},
         "surfaces": {"sdk": {}, "mcp": False}},
    ]}


def manifest():
    tools = [
        {"name": "get_epoch", "group": "epoch", "request": {"method": "GET", "path": "/epochs/{id}/"}},
        {"name": "get_sql_catalog", "group": "observability", "request": {"method": "GET", "path": "/tracer/sql-query/catalog/"}},
    ]
    return {"tool_count": len(tools), "tools": tools}


def tools_yaml():
    return {"tools": [{"name": "get_epoch", "group": "epoch", "description": "Return one Epoch."},
                      {"name": "get_sql_catalog", "group": "observability", "description": "Different words."}]}


def test_scopes_are_the_sql_ids_and_the_epoch_group():
    entries = pc.scoped(catalog())
    assert [e["id"] for e in entries["epoch"]] == ["simulation.epochs.get"]
    assert [e["id"] for e in entries["sql"]] == ["sql.get_catalog"]


def test_identical_scoped_projection_passes_and_out_of_scope_drift_is_ignored():
    product, committed = spec(), spec()
    committed["paths"]["/other/"]["get"]["operationId"] = "renamed"
    entries = pc.scoped(catalog())
    for scope in pc.SCOPES:
        assert pc.compare_projection(product, committed, entries[scope], scope) == []
    assert pc.compare_mcp(manifest(), tools_yaml(), entries) == []


def test_drift_inside_a_scope_fails():
    entries = pc.scoped(catalog())
    changed = spec()
    changed["definitions"]["Bar"] = {"type": "string"}
    assert pc.compare_projection(changed, spec(), entries["epoch"], "epoch") == ["epoch: definition Bar differs from the product contract"]
    changed = spec()
    changed["paths"]["/epochs/{id}/"]["parameters"][0]["type"] = "integer"
    assert pc.compare_projection(changed, spec(), entries["epoch"], "epoch") == ["epoch: parameters /epochs/{id}/ differs from the product contract"]
    gone = spec()
    del gone["paths"]["/tracer/sql-query/catalog/"]
    (problem,) = pc.compare_projection(gone, spec(), entries["sql"], "sql")
    assert problem.startswith("sql: product contract: the backend contract no longer has")


def test_epoch_tool_set_paths_and_descriptions_must_match_the_product():
    entries = pc.scoped(catalog())
    extra = manifest()
    extra["tools"].append({"name": "stop_epoch", "group": "epoch", "request": {"method": "POST", "path": "/epochs/{id}/stop/"}})
    extra["tool_count"] += 1
    assert pc.compare_mcp(extra, tools_yaml(), entries) == ["epoch: product tools without an epoch catalog entry: stop_epoch"]
    moved = manifest()
    moved["tools"][0]["request"]["path"] = "/epochs/{id}/v2/"
    assert pc.compare_mcp(moved, tools_yaml(), entries) == [
        "epoch: simulation.epochs.get is GET /epochs/{id}/, product get_epoch is GET /epochs/{id}/v2/"]
    reworded = tools_yaml()
    reworded["tools"][0]["description"] = "Return one Epoch. "
    assert pc.compare_mcp(manifest(), reworded, entries) == [
        "epoch: simulation.epochs.get description differs from product tools.yaml get_epoch"]
    relabelled = manifest()
    relabelled["tools"][0]["group"] = "simulation"
    assert pc.compare_mcp(relabelled, tools_yaml(), entries) == [
        "epoch: catalog entries outside the product's epoch group: get_epoch"]


def _product_repo(path: Path, contract: dict) -> str:
    files = {pc.SWAGGER: json.dumps(contract), pc.MCP: json.dumps(manifest()), pc.TOOLS_YAML: yaml.safe_dump(tools_yaml())}
    for name, text in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(text)
    git = ["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "product"], check=True)
    return subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()


@pytest.fixture
def sdk_files(tmp_path, monkeypatch):
    slice_path, catalog_path = tmp_path / "swagger.json", tmp_path / "operations.yaml"
    committed = {**spec(), "x-contract-sources": {"sql": {"backend_commit": "0" * 40}}}
    slice_path.write_text(json.dumps(committed))
    catalog_path.write_text(yaml.safe_dump(catalog()))
    monkeypatch.setattr(pc, "SLICE", slice_path)
    monkeypatch.setattr(pc, "CATALOG", catalog_path)
    return committed


def test_record_names_the_commit_hashes_and_stack(tmp_path, sdk_files):
    product = tmp_path / "product"
    product.mkdir()
    sha = _product_repo(product, spec())
    extra = tmp_path / "stack.json"
    extra.write_text(json.dumps({"image_digest": "sha256:" + "1" * 64}))
    out = tmp_path / "pair" / "pair.json"
    assert pc.main(["--product", str(product), "--sha", sha, "--branch", "dev", "--out", str(out), "--extra-json", str(extra)]) == 0
    record = json.loads(out.read_text())
    assert record["product"] == {"repository": "future-agi/future-agi", "sha": sha, "resolved_branch": "dev"}
    assert record["slice_matches"] is True and record["problems"] == []
    assert record["scope"] == {"epoch": ["simulation.epochs.get"], "sql": ["sql.get_catalog"]}
    assert record["contract_sources"] == sdk_files["x-contract-sources"]
    assert record["stack"] == {"image_digest": "sha256:" + "1" * 64}
    raw = (product / pc.SWAGGER).read_bytes()
    assert record["hashes"]["openapi_sha256"] == pc._sha256(raw)
    assert set(record["hashes"]) == {"openapi_sha256", "mcp_sha256", "tools_yaml_sha256", "sdk_slice_sha256", "sdk_catalog_sha256"}


def test_a_mismatch_still_writes_the_record_and_fails(tmp_path, sdk_files):
    product = tmp_path / "product"
    product.mkdir()
    drifted = copy.deepcopy(spec())
    drifted["definitions"]["Foo"]["properties"]["added"] = {"type": "string"}
    sha = _product_repo(product, drifted)
    out = tmp_path / "pair.json"
    assert pc.main(["--product", str(product), "--sha", sha, "--out", str(out)]) == 1
    record = json.loads(out.read_text())
    assert record["slice_matches"] is False
    assert record["problems"] == ["epoch: definition Foo differs from the product contract"]


def test_the_checkout_must_be_at_the_paired_commit(tmp_path, sdk_files):
    product = tmp_path / "product"
    product.mkdir()
    _product_repo(product, spec())
    out = tmp_path / "pair.json"
    assert pc.main(["--product", str(product), "--sha", "f" * 40, "--out", str(out)]) == 1
    assert "not " + "f" * 40 in json.loads(out.read_text())["problems"][0]
    with pytest.raises(SystemExit):
        pc.main(["--product", str(product), "--sha", "HEAD", "--out", str(out)])
