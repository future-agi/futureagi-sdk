"""sdkgen/pair_drift_issue.py: one issue while SDK dev's scoped contract drifts from the product.

Offline. The product commit is a throwaway Git repository built from the committed contract
(_scoped_product.py, shared with the pair_check and scoped sync tests); pair_check.py writes the
record, and an in-memory stand-in plays the GitHub issues API."""

import copy
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared fixture, under any import mode

import _scoped_product as fixture  # noqa: E402

sys.path.insert(0, str(fixture.ROOT / "sdkgen"))

import pair_check as pc  # noqa: E402
import pair_drift_issue as drift  # noqa: E402

REPO = "owner/sdk"


class FakeGitHub:
    """The issue, comment and label endpoints pair_drift_issue.py calls, in memory."""

    def __init__(self):
        self.issues, self.comments, self.labels, self.calls = {}, {}, set(), []

    def __call__(self, method, path, body=None):
        self.calls.append((method, path))
        prefix = f"/repos/{REPO}"
        assert path.startswith(prefix), path
        path = path[len(prefix):]
        if method == "GET" and path.startswith("/issues?"):
            assert f"labels={drift.LABEL}" in path and "state=open" in path
            return [i for i in self.issues.values() if i["state"] == "open" and drift.LABEL in i["labels"]]
        if method == "GET" and path.startswith("/labels/"):
            return {"name": path.split("/")[-1]} if path.split("/")[-1] in self.labels else None
        if method == "POST" and path == "/labels":
            self.labels.add(body["name"])
            return body
        if method == "POST" and path == "/issues":
            assert set(body["labels"]) <= self.labels, "the label must exist first"
            number = len(self.issues) + 1
            self.issues[number] = {"number": number, "state": "open", "title": body["title"], "body": body["body"],
                                   "labels": body["labels"]}
            self.comments[number] = []
            return self.issues[number]
        number = int(path.split("/")[2].split("?")[0])
        if method == "GET" and "/comments" in path:
            page = int(parse_qs(urlsplit(path).query)["page"][0])
            return [{"body": c} for c in self.comments[number][(page - 1) * 100:page * 100]]
        if method == "POST" and path.endswith("/comments"):
            self.comments[number].append(body["body"])
            return {}
        if method == "PATCH":
            self.issues[number].update(state=body["state"])
            return self.issues[number]
        raise AssertionError(f"unexpected call {method} {path}")

    def open(self):
        return [i for i in self.issues.values() if i["state"] == "open"]


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
    path = tmp_path / "product"
    path.mkdir()
    return path, fixture.product()


def _pair(tmp_path, path, sha):
    out = tmp_path / "pair" / "pair.json"
    pc.main(["--product", str(path), "--sha", sha, "--branch", "dev", "--out", str(out)])
    return out


def _run(tmp_path, path, sha, github):
    out = _pair(tmp_path, path, sha)
    return drift.main(["--pair", str(out), "--product", str(path), "--repo", REPO, "--run-url", "https://run"], github)


def _drift_a_description(built, name="list_epochs", suffix=" "):
    entry = next(t for t in built["tools_yaml"]["tools"] if t["name"] == name)
    entry["description"] += suffix


def test_a_clean_pairing_opens_nothing(tmp_path, product):
    path, built = product
    github = FakeGitHub()
    assert _run(tmp_path, path, _commit(path, built), github) == 0
    assert github.issues == {} and not [c for c in github.calls if c[0] != "GET"]


def test_drift_opens_one_labelled_issue_naming_the_range_and_the_operation(tmp_path, product):
    path, built = product
    _drift_a_description(built)
    sha = _commit(path, built)
    github = FakeGitHub()
    assert _run(tmp_path, path, sha, github) == 0
    (issue,) = github.open()
    assert issue["title"] == drift.TITLE and issue["labels"] == [drift.LABEL] and drift.LABEL in github.labels
    assert "`simulation.epochs.list`" in issue["body"]
    synced = fixture.SPEC["x-contract-sources"]["epoch"]["backend_commit"]
    assert f"/compare/{synced}...{sha}" in issue["body"]
    assert drift.MARKER.search(issue["body"]).group(1) == sha


def test_the_same_drift_on_a_newer_product_commit_adds_nothing(tmp_path, product):
    path, built = product
    _drift_a_description(built)
    github = FakeGitHub()
    _run(tmp_path, path, _commit(path, built), github)
    newer = _commit(path, built)  # a later product commit with the same drift
    assert _run(tmp_path, path, newer, github) == 0
    (issue,) = github.open()
    assert github.comments[issue["number"]] == []


def test_a_changed_drift_comments_on_the_open_issue_instead_of_opening_another(tmp_path, product):
    path, built = product
    _drift_a_description(built)
    github = FakeGitHub()
    _run(tmp_path, path, _commit(path, built), github)
    _drift_a_description(built, name="get_epoch")
    assert _run(tmp_path, path, _commit(path, built), github) == 0
    (issue,) = github.open()
    (comment,) = github.comments[issue["number"]]
    assert "`simulation.epochs.get`" in comment and "`simulation.epochs.list`" in comment


def test_a_new_product_tool_in_a_scoped_group_is_named(tmp_path, product):
    path, built = product
    built["manifest"]["tools"].append({**copy.deepcopy(built["tools"]["get_epoch"]), "name": "get_epoch_tomorrow"})
    github = FakeGitHub()
    assert _run(tmp_path, path, _commit(path, built), github) == 0
    (issue,) = github.open()
    assert "`get_epoch_tomorrow`" in issue["body"]


def test_passing_again_closes_the_issue(tmp_path, product):
    path, built = product
    clean = copy.deepcopy(built)
    _drift_a_description(built)
    github = FakeGitHub()
    _run(tmp_path, path, _commit(path, built), github)
    assert _run(tmp_path, path, _commit(path, clean), github) == 0
    assert github.open() == []
    (issue,) = github.issues.values()
    (comment,) = github.comments[issue["number"]]
    assert "passes on `dev`" in comment


def test_a_closed_issue_is_not_reused_and_a_new_drift_opens_one(tmp_path, product):
    path, built = product
    clean = copy.deepcopy(built)
    _drift_a_description(built)
    github = FakeGitHub()
    _run(tmp_path, path, _commit(path, built), github)
    _run(tmp_path, path, _commit(path, clean), github)
    _run(tmp_path, path, _commit(path, built), github)
    assert [i["number"] for i in github.open()] == [2]


def test_an_issue_with_another_title_is_left_alone(tmp_path, product):
    path, built = product
    github = FakeGitHub()
    github.labels.add(drift.LABEL)
    github.issues[1] = {"number": 1, "state": "open", "title": "someone else's note", "body": "", "labels": [drift.LABEL]}
    github.comments[1] = []
    _drift_a_description(built)
    _run(tmp_path, path, _commit(path, built), github)
    assert sorted(i["number"] for i in github.open()) == [1, 2]
    assert github.comments[1] == []


@pytest.mark.parametrize("problem", [
    "could not read the pairing inputs: product checkout is at x, not y",
    "live coverage: simulation.epochs.list has bucket 'covered', not a, b or c",
])
def test_a_failure_that_is_not_product_drift_opens_nothing_and_fails(tmp_path, product, problem):
    path, built = product
    out = _pair(tmp_path, path, _commit(path, built))
    record = json.loads(out.read_text())
    record.update(problems=[problem], slice_matches=False)
    out.write_text(json.dumps(record))
    github = FakeGitHub()
    code = drift.main(["--pair", str(out), "--product", str(path), "--repo", REPO], github)
    assert code == 1 and github.calls == []


def test_the_body_is_neutral_and_bounded(tmp_path, product):
    path, built = product
    record = json.loads(_pair(tmp_path, path, _commit(path, built)).read_text())
    problems = [f"epoch: definition D{i} differs from the product contract" for i in range(drift.MAX_LINES + 5)]
    body = drift.report_body(record, problems, ["simulation.epochs.list"], [], "https://run")
    assert "… and 5 more" in body
    assert "TH-" not in body and "linear" not in body.lower()


def test_catalog_scope_agrees_with_the_scoped_sync_on_the_committed_contract():
    import sync_scoped_contract as ssc

    built = fixture.product()
    fixture.fingerprint(built["manifest"])
    _, in_scope, _ = ssc.check_scopes(built["source"], json.dumps(built["source"]).encode(), built["manifest"],
                                      yaml.safe_dump(built["tools_yaml"]).encode(), fixture.CATALOG["operations"])
    expected = {entry["id"]: scope for scope, entries in in_scope.items() for entry in entries}
    found = {e["id"]: ssc.catalog_scope(e) for e in fixture.CATALOG["operations"] if ssc.catalog_scope(e)}
    assert found == expected and set(found.values()) == set(ssc.SCOPES)


def test_a_clean_product_reports_no_drifted_operation_or_new_tool(tmp_path, product):
    path, built = product
    assert drift.drifted(path, _commit(path, built)) == ([], [])


def test_scopes_synced_from_different_commits_get_one_range_each(tmp_path, product):
    path, built = product
    record = json.loads(_pair(tmp_path, path, _commit(path, built)).read_text())
    sha = record["product"]["sha"]
    sources = record["contract_sources"]
    scopes = sorted(drift.sync_scoped_contract.SCOPES)
    sources[scopes[0]] = {**sources[scopes[0]], "backend_commit": "a" * 40}
    body = drift.report_body(record, ["drift"], [], [], "https://run")
    assert "per scope" in body
    assert f"- {scopes[0]}: `{'a' * 12}...{sha[:12]}`" in body
    assert sum(1 for line in body.splitlines() if line.startswith("- ") and "/compare/" in line) == len(scopes)
