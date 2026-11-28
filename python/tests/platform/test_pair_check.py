"""sdkgen/pair_check.py: the scoped slice against one product commit, offline.

The product commit is a throwaway Git repository holding the committed contract and the MCP
manifest and tools.yaml the product would generate for it (_scoped_product.py, shared with the
scoped sync tests), so the pairing runs the same scope rules as sync_scoped_contract.py."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared fixture, under any import mode

import _scoped_product as fixture  # noqa: E402

sys.path.insert(0, str(fixture.ROOT / "sdkgen"))

import pair_check as pc  # noqa: E402
import sync_contract  # noqa: E402

N_SQL = len(fixture.SQL_PROJECTIONS)
N_EPOCH = len(fixture.EPOCH_TOOLS)


def _commit(path, built) -> str:
    fixture.fingerprint(built["manifest"])
    files = {pc.SWAGGER: json.dumps(built["source"]), pc.MCP: json.dumps(built["manifest"]),
             pc.TOOLS_YAML: yaml.safe_dump(built["tools_yaml"])}
    for name, text in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(text)
    git = ["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    if not (path / ".git").exists():
        subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "product"], check=True)
    return subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()


@pytest.fixture
def product(tmp_path):
    """(directory, built product files); tests edit the files, then call _commit."""
    path = tmp_path / "product"
    path.mkdir()
    return path, fixture.product()


def _run(tmp_path, path, sha, *extra):
    out = tmp_path / "pair" / "pair.json"
    code = pc.main(["--product", str(path), "--sha", sha, "--out", str(out), *extra])
    return code, json.loads(out.read_text())


def _epoch_only_response_definition() -> str:
    """A definition reached by an epoch read's response and by no SQL operation."""
    scoped = fixture.scoped_entries()
    sql = [e for e in scoped if e["id"].startswith("sql.")]
    _, sql_defs = sync_contract.project(fixture.SPEC, sql)
    get_epoch = next(e for e in scoped if fixture.mcp_name(e) == "get_epoch")
    _, epoch_defs = sync_contract.project(fixture.SPEC, [get_epoch])
    return sorted(set(epoch_defs) - set(sql_defs))[0]


def test_the_committed_slice_pairs_and_the_record_names_the_commit_hashes_and_stack(tmp_path, product):
    path, built = product
    sha = _commit(path, built)
    extra = tmp_path / "stack.json"
    extra.write_text(json.dumps({"image_digest": "sha256:" + "1" * 64}))
    code, record = _run(tmp_path, path, sha, "--branch", "dev", "--extra-json", str(extra))
    assert code == 0, record["problems"]
    assert record["product"] == {"repository": "future-agi/future-agi", "sha": sha, "resolved_branch": "dev"}
    assert record["slice_matches"] is True and record["problems"] == []
    assert record["scope_groups"] == ["epoch", "skills", "sql"]
    assert len(record["scope"]["sql"]) == N_SQL and all(i.startswith("sql.") for i in record["scope"]["sql"])
    assert len(record["scope"]["epoch"]) == N_EPOCH
    assert len(record["scope"]["skills"]) == 24 and "contexts.manifest" in record["scope"]["skills"]
    assert record["contract_sources"] == fixture.SPEC["x-contract-sources"]
    assert record["stack"] == {"image_digest": "sha256:" + "1" * 64}
    assert record["hashes"]["openapi_sha256"] == pc._sha256((path / pc.SWAGGER).read_bytes())
    assert set(record["hashes"]) == {"openapi_sha256", "mcp_sha256", "tools_yaml_sha256", "sdk_slice_sha256", "sdk_catalog_sha256"}
    assert record["mcp"]["tool_count"] == N_SQL + N_EPOCH + 13 + 1


def test_drift_outside_the_scopes_is_ignored(tmp_path, product):
    path, built = product
    scoped = {(e["operation"]["method"].lower(), e["operation"]["path"]) for e in fixture.scoped_entries()}
    method, route = next((e["operation"]["method"].lower(), e["operation"]["path"]) for e in fixture.CATALOG["operations"]
                         if (e["operation"]["method"].lower(), e["operation"]["path"]) not in scoped)
    built["source"]["paths"][route][method]["operationId"] = "renamed_on_the_product"
    code, record = _run(tmp_path, path, _commit(path, built))
    assert (code, record["problems"]) == (0, [])


def test_a_scoped_definition_that_drifted_fails_and_still_writes_the_record(tmp_path, product):
    path, built = product
    name = _epoch_only_response_definition()
    built["source"]["definitions"][name]["title"] = "changed on the product"
    code, record = _run(tmp_path, path, _commit(path, built))
    assert code == 1
    assert record["slice_matches"] is False
    assert record["problems"] == [f"epoch: definition {name} differs from the product contract"]
    assert set(record["hashes"]) == {"openapi_sha256", "mcp_sha256", "tools_yaml_sha256", "sdk_slice_sha256", "sdk_catalog_sha256"}


def test_a_new_product_epoch_tool_fails_with_the_scoped_sync_rule(tmp_path, product):
    path, built = product
    built["manifest"]["tools"].append({**copy.deepcopy(built["tools"]["get_epoch"]), "name": "get_epoch_tomorrow"})
    code, record = _run(tmp_path, path, _commit(path, built))
    assert code == 1
    (problem,) = record["problems"]
    assert problem.startswith("scoped catalog check: expected exactly one catalog mapping per epoch tool: missing ['get_epoch_tomorrow']")
    assert "scope" not in record and "hashes" in record


def test_an_epoch_tool_that_left_the_group_fails(tmp_path, product):
    path, built = product
    built["tools"]["get_epoch"]["group"] = "simulation"
    code, record = _run(tmp_path, path, _commit(path, built))
    assert code == 1
    (problem,) = record["problems"]
    assert "epoch scope mismatch: simulation.epochs.get is in MCP group epoch" in problem


def test_an_epoch_description_must_match_tools_yaml_byte_for_byte(tmp_path, product):
    path, built = product
    entry = next(t for t in built["tools_yaml"]["tools"] if t["name"] == "list_epochs")
    entry["description"] += " "
    code, record = _run(tmp_path, path, _commit(path, built))
    assert code == 1
    (problem,) = record["problems"]
    assert "epoch descriptions differ from product tools.yaml" in problem and "list_epochs" in problem


def test_a_sql_route_the_product_moved_fails(tmp_path, product):
    path, built = product
    built["tools"]["get_sql_catalog"]["request"]["path"] = "/tracer/sql-query/catalog/v2/"
    code, record = _run(tmp_path, path, _commit(path, built))
    assert code == 1
    (problem,) = record["problems"]
    assert "scoped MCP operation mismatch: sql." in problem


def test_the_checkout_must_be_at_the_paired_commit(tmp_path, product):
    path, built = product
    _commit(path, built)
    code, record = _run(tmp_path, path, "f" * 40)
    assert code == 1
    assert record["problems"][0].startswith("could not read the pairing inputs:")
    assert "not " + "f" * 40 in record["problems"][0]
    with pytest.raises(SystemExit):
        pc.main(["--product", str(path), "--sha", "HEAD", "--out", str(tmp_path / "pair.json")])


def test_the_live_coverage_table_names_every_epoch_operation_once():
    entries = yaml.safe_load(pc.CATALOG.read_text())["operations"]
    coverage, problems = pc.live_coverage(entries)
    assert problems == []
    assert coverage["tracking"] == "TH-10732"
    assert sum(coverage["counts"].values()) == 19
    rows = coverage["operations"]
    # Only reading Debug failures succeeds live today; the rest wait for PR2 or cannot succeed.
    assert {op for op, row in rows.items() if row["bucket"] == "a"} == {"simulation.executions.insights.get"}
    assert {op for op, row in rows.items() if row["bucket"] == "c"} == {
        "simulation.epochs.candidates.open_pull_request"}
    assert all(row["status"] == "refusal-only until PR2 TH-10732" for row in rows.values() if row["bucket"] == "b")


def test_the_record_carries_the_live_coverage_table(tmp_path, product):
    path, built = product
    code, record = _run(tmp_path, path, _commit(path, built))
    assert code == 0, record["problems"]
    assert record["live_coverage"]["counts"] == {"a": 1, "b": 17, "c": 1}


@pytest.mark.parametrize("edit, message", [
    (lambda t: t["operations"].pop("simulation.epochs.list"), "differs from the epoch-group catalog"),
    (lambda t: t["operations"].__setitem__("simulation.extra", {"bucket": "a"}), "differs from the epoch-group catalog"),
    (lambda t: t["operations"]["simulation.epochs.list"].pop("status"), "without the status"),
    (lambda t: t["operations"]["simulation.epochs.list"].__setitem__("bucket", "covered"), "not a, b or c"),
    (lambda t: t["operations"]["simulation.epochs.candidates.open_pull_request"].pop("reason"), "without a reason"),
])
def test_a_wrong_live_coverage_table_fails(tmp_path, monkeypatch, edit, message):
    table = yaml.safe_load(pc.COVERAGE.read_text())
    edit(table)
    changed = tmp_path / "coverage.yaml"
    changed.write_text(yaml.safe_dump(table))
    monkeypatch.setattr(pc, "COVERAGE", changed)
    entries = yaml.safe_load(pc.CATALOG.read_text())["operations"]
    _, problems = pc.live_coverage(entries)
    assert any(message in problem for problem in problems), problems


def test_sdk_only_context_route_is_part_of_the_pair(tmp_path, product):
    path, built = product
    route = "/model-hub/skills/contexts/resolve/"
    del built["source"]["paths"][route]["get"]
    code, record = _run(tmp_path, path, _commit(path, built))
    assert code == 1 and any(f"missing on product: GET {route}" in p for p in record["problems"])


def test_pair_rejects_changed_context_credential_scheme(tmp_path, product):
    path, built = product
    built["source"]["securityDefinitions"]["ContextCredential"]["name"] = "X-Different-Credential"
    code, record = _run(tmp_path, path, _commit(path, built))
    assert code == 1 and record["problems"] == ["skills: auth scheme ContextCredential differs from the product contract"]
