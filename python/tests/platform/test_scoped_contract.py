"""sdkgen/sync_scoped_contract.py: the sql and epoch groups from one product commit, the rest from the
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
    baseline = {**{k: SPEC[k] for k in ("swagger", "info", "securityDefinitions", "security")},
                "x-source-sha256": "baseline-hash", "paths": paths, "definitions": definitions}
    built = fixture.product()
    source_raw = json.dumps(built["source"]).encode()
    manifest, tools_yaml = built["manifest"], built["tools_yaml"]

    def blob(_repo, _commit, path):
        return {"sdkgen/contracts/swagger.json": json.dumps(baseline).encode(), sync.SWAGGER: source_raw,
                sync.MCP: json.dumps(manifest).encode(), sync.TOOLS_YAML: yaml.safe_dump(tools_yaml).encode()}[path]

    monkeypatch.setattr(sync, "_blob", blob)
    state = {"baseline": baseline, "manifest": manifest, "tools": built["tools"], "tools_yaml": tools_yaml}

    def compose():
        if not state.get("keep_fingerprint"):  # a test that adds a tool gets a consistent manifest
            fixture.fingerprint(manifest)
        return sync.compose(ROOT, "0" * 40, "1" * 40)

    return compose, state


def test_sql_and_epoch_come_from_one_commit_and_the_rest_from_the_baseline(scoped_sync):
    compose, state = scoped_sync
    result = compose()
    assert (result["paths"], result["definitions"]) == (SPEC["paths"], SPEC["definitions"])
    sources = result["x-contract-sources"]
    assert set(sources) == {"sql", "epoch", "other"}
    assert sources["sql"]["tools"] == sorted(SQL_PROJECTIONS) and sources["epoch"]["tools"] == sorted(EPOCH_TOOLS)
    assert {k: v for k, v in sources["sql"].items() if k != "tools"} == {k: v for k, v in sources["epoch"].items() if k != "tools"}
    assert sources["epoch"]["backend_commit"] == "0" * 40 and sources["other"]["sdk_commit"] == "1" * 40
    assert sources["other"]["openapi_sha256"] == "baseline-hash"


def test_the_committed_contract_records_both_groups_from_one_product_commit():
    sources = SPEC["x-contract-sources"]
    assert sources["sql"]["tools"] == sorted(SQL_PROJECTIONS) and sources["epoch"]["tools"] == sorted(EPOCH_TOOLS)
    for key in ("backend_commit", "openapi_sha256", "mcp_sha256", "tools_yaml_sha256"):
        assert sources["sql"][key] == sources["epoch"][key]
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


def test_scoped_sync_rejects_a_baseline_that_is_not_a_release_slice(scoped_sync):
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
