"""sdkgen/sync_scoped_contract.py: the SQL, Epoch and Skills groups from one product commit, the rest from the
SDK baseline slice. Runs on fixtures built from the committed contract, without Git history."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared fixture, under any import mode

import _scoped_product as fixture  # noqa: E402

ROOT = fixture.ROOT
CATALOG = fixture.CATALOG
SPEC = fixture.SPEC
EPOCH_TOOLS = fixture.EPOCH_TOOLS
SQL_PROJECTIONS = fixture.SQL_PROJECTIONS
_mcp_name = fixture.mcp_name


@pytest.fixture
def scoped_sync(monkeypatch):
    """The product commit is the committed contract itself; the baseline is its unscoped projection."""
    monkeypatch.syspath_prepend(str(ROOT / "sdkgen"))
    import sync_contract
    import sync_scoped_contract as sync

    scoped = fixture.scoped_entries()
    unscoped = [e for e in CATALOG["operations"] if e not in scoped]
    paths, definitions = copy.deepcopy(sync_contract.project(SPEC, unscoped))  # tests edit the baseline
    baseline = {**{k: copy.deepcopy(SPEC[k]) for k in ("swagger", "info", "securityDefinitions", "security")},
                "x-source-sha256": "a" * 64, "paths": paths, "definitions": definitions}
    built = fixture.product()
    manifest, tools_yaml = built["manifest"], built["tools_yaml"]

    def blob(_repo, _commit, path):
        return {"sdkgen/contracts/swagger.json": json.dumps(baseline).encode(), sync.SWAGGER: json.dumps(built["source"]).encode(),
                sync.MCP: json.dumps(manifest).encode(), sync.TOOLS_YAML: yaml.safe_dump(tools_yaml).encode()}[path]

    monkeypatch.setattr(sync, "_blob", blob)
    state = {"source": built["source"], "baseline": baseline, "manifest": manifest, "tools": built["tools"], "tools_yaml": tools_yaml}

    def compose(scopes=None):
        if not state.get("keep_fingerprint"):  # a test that adds a tool gets a consistent manifest
            fixture.fingerprint(manifest)
        return sync.compose(ROOT, "0" * 40, "1" * 40, scopes)

    return compose, state


@pytest.fixture
def paired_sync(scoped_sync):
    """Product pairing: the baseline is the paired SDK slice itself, every scope recorded."""
    compose, state = scoped_sync
    state["baseline"].clear()
    state["baseline"].update(copy.deepcopy(SPEC))
    return compose, state


def _epoch_route():
    entry = next(e for e in fixture.scoped_entries() if (e["surfaces"].get("mcp") or {}).get("group") == "epoch")
    return entry["operation"]["path"], entry["operation"]["method"].lower(), mcp_name(entry)


def mcp_name(entry):
    return _mcp_name(entry)


def test_selecting_every_scope_is_byte_identical_to_the_default(scoped_sync):
    import sync_scoped_contract as sync

    compose, _ = scoped_sync
    default = json.dumps(compose(), indent=2)
    assert json.dumps(compose(tuple(sync.SCOPES)), indent=2) == default
    assert json.dumps(compose(tuple(reversed(list(sync.SCOPES)))), indent=2) == default


def test_a_skills_only_sync_keeps_every_pinned_scope_as_the_paired_slice_has_it(paired_sync):
    compose, state = paired_sync
    # The product moves an Epoch route and drops an unscoped route the SDK wraps; neither may
    # reach a Skills-only sync, nor fail it.
    path, method, _ = _epoch_route()
    state["source"]["paths"][path][method].setdefault("parameters", []).append(
        {"name": "probe", "in": "query", "required": False, "type": "string"})
    unscoped = next(e for e in CATALOG["operations"] if e not in fixture.scoped_entries())
    del state["source"]["paths"][unscoped["operation"]["path"]][unscoped["operation"]["method"].lower()]
    result = compose(("skills",))
    assert (result["paths"], result["definitions"]) == (SPEC["paths"], SPEC["definitions"])
    sources, committed = result["x-contract-sources"], SPEC["x-contract-sources"]
    assert {name: sources[name] for name in ("sql", "epoch", "other")} == {
        name: committed[name] for name in ("sql", "epoch", "other")}
    assert sources["skills"]["backend_commit"] == "0" * 40
    assert sources["skills"]["tools"] == committed["skills"]["tools"]


def test_a_pinned_scope_is_not_checked_for_missing_or_extra_tools(paired_sync):
    compose, state = paired_sync
    _, _, name = _epoch_route()
    state["manifest"]["tools"] = [t for t in state["manifest"]["tools"] if t["name"] != name]
    with pytest.raises(ValueError, match="epoch"):
        compose()
    assert compose(("skills",))["x-contract-sources"]["epoch"] == SPEC["x-contract-sources"]["epoch"]


def test_a_skills_sync_cannot_change_a_definition_a_pinned_scope_shares(paired_sync):
    compose, state = paired_sync
    state["source"]["definitions"]["ManagementAPIErrorResponse"]["title"] = "drifted product shape"
    with pytest.raises(ValueError, match="collides"):
        compose(("skills",))


def _skills_route():
    entry = next(e for e in fixture.scoped_entries() if (e["surfaces"].get("mcp") or {}).get("group") == "skills")
    return entry["operation"]["path"], entry["operation"]["method"].lower(), mcp_name(entry)


def test_a_skills_sync_refuses_a_definition_only_a_pinned_scope_and_skills_share(paired_sync):
    # A definition no unscoped operation reaches: shared by one Epoch and one Skills route only.
    compose, state = paired_sync
    probe = {"description": "probe", "schema": {"$ref": "#/definitions/ScopeSharedProbe"}}
    for doc in (state["source"], state["baseline"]):
        doc["definitions"]["ScopeSharedProbe"] = {"type": "object", "title": "shared"}
        for path, method, _ in (_epoch_route(), _skills_route()):
            doc["paths"][path][method].setdefault("responses", {})["299"] = copy.deepcopy(probe)
    result = compose(("skills",))
    assert result["definitions"]["ScopeSharedProbe"] == {"type": "object", "title": "shared"}
    state["source"]["definitions"]["ScopeSharedProbe"]["title"] = "drifted product shape"
    with pytest.raises(ValueError, match="collides"):
        compose(("skills",))


def test_a_skills_only_sync_still_checks_and_resyncs_skills(paired_sync):
    compose, state = paired_sync
    path, method, name = _skills_route()
    # The selected scope comes from the product: a product-side change to a Skills route lands.
    state["source"]["paths"][path][method].setdefault("responses", {})["298"] = {"description": "probe"}
    assert compose(("skills",))["paths"][path][method]["responses"]["298"] == {"description": "probe"}
    # And it is still checked against the product's MCP manifest.
    state["manifest"]["tools"] = [t for t in state["manifest"]["tools"] if t["name"] != name]
    with pytest.raises(ValueError, match="skills"):
        compose(("skills",))


def test_an_epoch_input_change_fails_the_full_sync_but_not_a_skills_only_one(paired_sync):
    compose, state = paired_sync
    path, method, name = _epoch_route()
    for tool in state["manifest"]["tools"]:
        if tool["name"] == name:
            tool.setdefault("inputSchema", {}).setdefault("properties", {})["probe"] = {"type": "string"}
    state["source"]["paths"][path][method].setdefault("parameters", []).append(
        {"name": "probe", "in": "query", "required": False, "type": "string"})
    with pytest.raises(ValueError):
        compose()
    assert compose(("skills",))["paths"][path] == SPEC["paths"][path]


@pytest.mark.parametrize("scopes", [(), ("nope",), ("skills", "skills")])
def test_an_invalid_scope_selection_is_rejected(paired_sync, scopes):
    compose, _ = paired_sync
    with pytest.raises(ValueError, match="scope selection"):
        compose(scopes)


def test_pinning_needs_a_scoped_baseline_slice(scoped_sync):
    compose, _ = scoped_sync  # the default fixture's baseline is a release slice
    with pytest.raises(ValueError, match="previously synced scoped SDK slice"):
        compose(("skills",))


def test_scoped_groups_come_from_one_commit_and_the_rest_from_the_baseline(scoped_sync):
    compose, state = scoped_sync
    result = compose()
    assert (result["paths"], result["definitions"]) == (SPEC["paths"], SPEC["definitions"])
    sources = result["x-contract-sources"]
    assert set(sources) == {"sql", "epoch", "skills", "other"}
    assert sources["sql"]["tools"] == sorted(SQL_PROJECTIONS) and sources["epoch"]["tools"] == sorted(EPOCH_TOOLS)
    assert {k: v for k, v in sources["sql"].items() if k != "tools"} == {k: v for k, v in sources["epoch"].items() if k != "tools"}
    assert len(sources["skills"]["tools"]) == 13
    assert sources["epoch"]["backend_commit"] == "0" * 40 and sources["other"]["sdk_commit"] == "1" * 40
    assert sources["other"]["openapi_sha256"] == state["baseline"]["x-source-sha256"]


def test_the_committed_contract_records_all_groups_from_one_product_commit():
    sources = SPEC["x-contract-sources"]
    assert sources["sql"]["tools"] == sorted(SQL_PROJECTIONS) and sources["epoch"]["tools"] == sorted(EPOCH_TOOLS)
    for key in ("backend_commit", "openapi_sha256", "mcp_sha256", "tools_yaml_sha256"):
        assert sources["sql"][key] == sources["epoch"][key] == sources["skills"][key]
    assert {_mcp_name(e) for e in CATALOG["operations"] if (e["surfaces"].get("mcp") or {}).get("group") == "epoch"} == EPOCH_TOOLS


def test_scoped_sync_rejects_mismatched_manifests_and_shared_definitions(scoped_sync):
    compose, state = scoped_sync
    state["baseline"]["definitions"]["ManagementAPIErrorResponse"]["title"] = "conflicting baseline shape"
    with pytest.raises(ValueError, match="collides"):
        compose()
    state["manifest"]["source_contract_sha256"] = "wrong"
    with pytest.raises(ValueError, match="hashes disagree"):
        compose()


def test_scoped_sync_rejects_a_wrong_tool_name_fingerprint(scoped_sync):
    compose, state = scoped_sync
    state["keep_fingerprint"] = True
    state["manifest"]["tool_names_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="fingerprint"):
        compose()


def test_scoped_sync_rejects_ambiguous_baseline_provenance(scoped_sync):
    compose, state = scoped_sync
    state["baseline"]["x-contract-sources"] = {}
    with pytest.raises(ValueError, match="release slice"):
        compose()


def test_every_epoch_tool_needs_exactly_one_catalog_entry(scoped_sync):
    compose, state = scoped_sync
    state["manifest"]["tools"].append({**copy.deepcopy(state["tools"]["get_epoch"]), "name": "get_epoch_tomorrow"})
    with pytest.raises(ValueError, match=r"one catalog mapping per epoch tool: missing \['get_epoch_tomorrow'\]"):
        compose()


@pytest.mark.parametrize("tool, hint", [
    ("launch_epoch", "openWorldHint"), ("stop_epoch", "readOnlyHint"), ("discard_evidence_import", "destructiveHint"),
])
def test_scoped_sync_rejects_epoch_exposure_drift(scoped_sync, tool, hint):
    compose, state = scoped_sync
    annotations = state["tools"][tool]["annotations"]
    annotations[hint] = not annotations[hint]
    with pytest.raises(ValueError, match="exposure mismatch"):
        compose()


def test_scoped_sync_rejects_an_unwrap_the_sdk_does_not_share(scoped_sync):
    compose, state = scoped_sync
    state["tools"]["get_epoch"]["response"]["unwrap"] = "data"
    with pytest.raises(ValueError, match=r"unwrap mismatch: simulation\.epochs\.get"):
        compose()


def test_an_epoch_catalog_entry_needs_a_product_epoch_tool(scoped_sync):
    compose, state = scoped_sync
    state["tools"]["get_epoch"]["group"] = "simulation"  # the product moved the tool out of the group
    with pytest.raises(ValueError, match=r"epoch scope mismatch: simulation\.epochs\.get is in MCP group epoch"):
        compose()


def test_scoped_sync_rejects_epoch_description_drift(scoped_sync):
    compose, state = scoped_sync
    entry = next(t for t in state["tools_yaml"]["tools"] if t["name"] == "list_epochs")
    entry["description"] = entry["description"].replace("newest first", "newest  first")
    with pytest.raises(ValueError, match="descriptions differ"):
        compose()


def test_a_nullable_input_must_stay_nullable_on_mcp(scoped_sync):
    compose, state = scoped_sync
    props = state["tools"]["launch_epoch"]["inputSchema"]["properties"]
    assert props["cost_limit_usd"]["anyOf"][1] == {"type": "null"}  # the committed contract marks it x-nullable
    props["cost_limit_usd"] = props["cost_limit_usd"]["anyOf"][0]
    with pytest.raises(ValueError, match=r"input schema mismatch: simulation\.epochs\.launch\.cost_limit_usd"):
        compose()


@pytest.mark.parametrize("drift, message", [
    ("move_path", "placement"), ("move_query", "placement"), ("move_body", "placement"),
    ("missing_required", "required"), ("extra_required", "required"), ("extra_property", "properties"),
])
def test_scoped_sync_rejects_mcp_input_projection_drift(scoped_sync, drift, message):
    compose, state = scoped_sync
    tools = state["tools"]
    reader = tools["get_sql_result"]
    params = reader["request"]["parameters"]
    if drift == "move_path":
        params["query"].append(params["path"].pop())
    elif drift == "move_query":
        params["body"].append(params["query"].pop())
    elif drift == "move_body":
        params = tools["run_sql"]["request"]["parameters"]
        params["query"].append(params["body"].pop())
    elif drift == "missing_required":
        reader["inputSchema"]["required"].remove("project_id")
    elif drift == "extra_required":
        reader["inputSchema"]["required"].append("offset")
    else:
        reader["inputSchema"]["properties"]["unknown"] = {}
    with pytest.raises(ValueError, match=message):
        compose()


@pytest.mark.parametrize("field, value", [("type", "string"), ("maximum", 99)])
def test_scoped_sync_rejects_mcp_input_schema_drift(scoped_sync, field, value):
    compose, state = scoped_sync
    state["tools"]["get_sql_result"]["inputSchema"]["properties"]["limit"][field] = value
    message = (r"scoped MCP input schema mismatch: sql\.get_result\.limit"
               if field == "type" else r"scoped MCP page limit mismatch: sql\.get_result\.limit")
    with pytest.raises(ValueError, match=message):
        compose()


def test_list_epochs_keeps_the_mcp_page_cap(scoped_sync):
    compose, state = scoped_sync
    state["tools"]["list_epochs"]["inputSchema"]["properties"]["limit"]["maximum"] = 50
    with pytest.raises(ValueError, match=r"page limit mismatch: simulation\.epochs\.list\.limit"):
        compose()


def test_scoped_sync_imports_the_isolated_credential_scheme(scoped_sync):
    compose, state = scoped_sync
    del state["baseline"]["securityDefinitions"]["ContextCredential"]
    assert compose()["securityDefinitions"] == SPEC["securityDefinitions"]


@pytest.fixture
def mixed_baseline(scoped_sync):
    import sync_contract

    compose, state = scoped_sync
    baseline = state["baseline"]
    # The pre-Skills SDK recorded SQL and Epoch from one product commit.
    previous = [e for e in CATALOG["operations"] if not e["operation"]["path"].startswith("/model-hub/skills/")]
    baseline["paths"], baseline["definitions"] = sync_contract.project(SPEC, previous)
    product = {"backend_commit": "b" * 40, "openapi_sha256": "c" * 64,
               "mcp_sha256": "d" * 64, "tools_yaml_sha256": "e" * 64}
    sources = baseline["x-contract-sources"] = {
        "other": {"sdk_commit": "3" * 40, "slice_sha256": "2" * 64, "openapi_sha256": baseline.pop("x-source-sha256")},
        "sql": {**product, "tools": sorted(SQL_PROJECTIONS)},
        "epoch": {**product, "tools": sorted(EPOCH_TOOLS)},
    }
    return compose, sources


def test_mixed_sdk_baseline_records_the_underlying_release(mixed_baseline):
    compose, sources = mixed_baseline
    other = compose()["x-contract-sources"]["other"]
    assert other["openapi_sha256"] == sources["other"]["openapi_sha256"]
    assert other["sdk_commit"] == "1" * 40 and other["slice_sha256"] != sources["other"]["slice_sha256"]


@pytest.mark.parametrize(("scope", "field", "invalid"), [
    ("other", "sdk_commit", None), ("other", "slice_sha256", None), ("other", "openapi_sha256", "baseline-hash"),
    ("sql", "backend_commit", "b" * 39), ("epoch", "openapi_sha256", None), ("epoch", "mcp_sha256", "z" * 64),
    ("sql", "tools_yaml_sha256", None), ("sql", "tools", None), ("epoch", "tools", ["get_epoch", "get_epoch"]),
])
def test_incomplete_or_malformed_scoped_provenance_is_rejected(mixed_baseline, scope, field, invalid):
    compose, sources = mixed_baseline
    if invalid is None:
        del sources[scope][field]
    else:
        sources[scope][field] = invalid
    with pytest.raises(ValueError, match=rf"{scope}\.{field}"):
        compose()


def test_malformed_product_mcp_json_preserves_existing_contract(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "sdkgen"))
    import sync_scoped_contract as sync

    product = tmp_path / "product"
    built = fixture.product()
    malformed = '{"tools": ['
    for name, text in ((sync.SWAGGER, json.dumps(built["source"])), (sync.MCP, malformed),
                       (sync.TOOLS_YAML, yaml.safe_dump(built["tools_yaml"]))):
        path = product / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    contract = Path("sdkgen/contracts/swagger.json")
    output = tmp_path / contract
    output.parent.mkdir(parents=True)
    before = (ROOT / contract).read_bytes()
    output.write_bytes(before)
    monkeypatch.setattr(sync.sync_contract, "ROOT", tmp_path)
    monkeypatch.setattr(sync.sync_contract, "OUT", output)
    # Substitute only Git blob lookup; the CLI parses the real bytes and owns the write.
    monkeypatch.setattr(sync, "_blob", lambda repo, commit, path: (repo / path).read_bytes())
    with pytest.raises(json.JSONDecodeError) as error:
        sync.main([str(product), "0" * 40, "1" * 40])
    assert error.value.doc == malformed
    assert output.read_bytes() == before


@pytest.mark.parametrize("rows", [None, [None], [{"name": None}], [{"name": "  "}]])
def test_invalid_manifest_names_are_not_treated_as_missing_input(scoped_sync, rows):
    compose, state = scoped_sync
    state["keep_fingerprint"] = True
    state["manifest"]["tools"] = rows
    with pytest.raises(ValueError, match="invalid product MCP manifest"):
        compose()


def test_duplicate_tool_names_are_not_collapsed(scoped_sync):
    compose, state = scoped_sync
    state["manifest"]["tools"].append(state["tools"]["get_skill"])
    with pytest.raises(ValueError, match="invalid product MCP manifest"):
        compose()


def test_scoped_sync_cannot_restore_removed_product_route_from_baseline(scoped_sync):
    compose, state = scoped_sync
    route = next(iter(state["baseline"]["paths"]))
    del state["source"]["paths"][route]
    with pytest.raises(ValueError, match="selected operation missing on product"):
        compose()
