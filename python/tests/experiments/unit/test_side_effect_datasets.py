"""Contract: datasets made as a side effect of an uploaded run.

- inline ``list[dict]`` rows need a dataset name (``experiments.dataset(rows, name=...)``); there are no
  ``rows <hash>`` names, and the refusal comes before any request;
- a rows file needs one too (dataset service decision after wave 2b, S3 (a)): ``test_dataset_name_files.py``;
- local rows never add a version to an existing dataset that fi.experiments did not create, unless the
  caller opts in (``add_version=True`` / ``--add-version``); the refusal names the dataset and the opt-in.
  An existing dataset that is empty and has no version needs the opt-in too (dataset service decision S1 under the atomic-create contract:
  no opt-in only through one conditional server create, which the server does not have yet); with it, the run
  header says it wrote that dataset's first version.

Against the contract stand-in (``contract_server.py``); no network, no model.
"""

import json

import pytest

from fi import experiments
from fi.experiments._server_dataset import DatasetNotOwnedError
from fi.experiments.errors import UsageError
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer, client_for

ROWS = [
    {"id": "T0", "question": "where is order 1?", "expected": "shipped"},
    {"id": "T1", "question": "where is order 2?", "expected": "lost"},
]
VERSION_POSTS = r"/model-hub/datasets/.*/versions/"


def task(row):
    return "shipped"


def _run(server, dataset, **kw):
    return experiments.run(dataset, task, [], client=client_for(server), trace=False, progress=False, **kw)


def _file(tmp_path, name="support.jsonl", rows=ROWS):
    path = tmp_path / name
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return str(path)


def _named(tmp_path, rows=ROWS, **kw):
    """A rows file with its dataset name (a file needs one: S3 (a))."""
    return experiments.dataset(_file(tmp_path, rows=rows), name="support", **kw)


# ---- inline rows need a name ----------------------------------------------------------------------


def test_inline_rows_on_an_uploaded_run_need_a_name_before_any_request():
    server = ContractServer()
    with pytest.raises(UsageError) as info:
        _run(server, ROWS)
    message = str(info.value)
    assert 'experiments.dataset(rows, name="support-cases")' in message and "upload=False" in message
    assert server.requests == []  # nothing was created, nothing was even asked


def test_log_results_with_inline_rows_needs_a_name_too():
    server = ContractServer()
    with pytest.raises(UsageError, match="a list has no name"):
        experiments.log_results(ROWS, [{"id": "T0", "output": "x"}], client=client_for(server), progress=False)
    assert server.requests == []


def test_named_inline_rows_land_in_that_dataset_and_no_hash_name_is_made():
    server = ContractServer()
    first = _run(server, experiments.dataset(ROWS, name="support-cases"))
    edited = [dict(ROWS[0], expected="delivered"), ROWS[1]]
    second = _run(server, experiments.dataset(edited, name="support-cases"))
    [ds] = server.datasets.values()
    assert ds["name"] == "support-cases" and len(ds["versions"]) == 2  # an edit is a new version, not a new dataset
    assert first.dataset_id == second.dataset_id
    assert not any(d["name"].startswith("rows ") for d in server.datasets.values())


def test_a_local_run_needs_no_name():
    result = experiments.run(ROWS, task, [], upload=False, trace=False, progress=False)
    assert result.status == "no_upload" and [i.status for i in result.items] == ["completed", "completed"]


def test_dataset_name_must_be_a_non_empty_string():
    with pytest.raises(UsageError, match="non-empty"):
        experiments.dataset(ROWS, name="  ")


# ---- never a version on a dataset the SDK did not create ------------------------------------------


def test_a_file_never_versions_a_ui_dataset_of_the_same_name(tmp_path):
    server = ContractServer()
    did = server.add_dataset("support", [{"question": "made in the UI", "expected": "x"}])
    with pytest.raises(DatasetNotOwnedError) as info:
        _run(server, _named(tmp_path))
    message = str(info.value)
    assert "dataset 'support' already exists" in message and "has table rows" in message
    assert "cannot tell that it made it" in message and "made in the UI or by another tool)" not in message
    assert "add_version=True" in message and "--add-version" in message and "--dataset-name" in message
    assert server.count("POST", VERSION_POSTS) == 0 and server.datasets[did]["versions"] == []
    assert server.count("POST", r"/model-hub/experiment-runs/") == 0


def test_an_empty_versionless_dataset_is_refused_without_the_opt_in_and_the_refusal_says_why(tmp_path):
    server = ContractServer()
    did = server.add_dataset("support")  # no rows, no versions
    with pytest.raises(DatasetNotOwnedError) as info:
        _run(server, _named(tmp_path))
    message = str(info.value)
    assert "dataset 'support' already exists on the server and is empty and has no version yet" in message
    assert "two runs started at once could otherwise both write one" in message
    assert "add_version=True" in message and "--dataset-name support --add-version" in message
    assert server.count("POST", VERSION_POSTS) == 0 and server.datasets[did]["versions"] == []
    assert server.count("POST", r"/model-hub/experiment-runs/") == 0


def test_with_the_opt_in_an_empty_versionless_dataset_gets_its_first_version_and_the_header_says_so(tmp_path, capsys):
    server = ContractServer()
    did = server.add_dataset("support")
    result = experiments.run(_named(tmp_path, add_version=True), task, [], client=client_for(server), trace=False)
    assert result.status == "completed" and result.dataset_id == did
    assert len(server.datasets[did]["versions"]) == 1
    printed = capsys.readouterr()
    assert "wrote the first version of the existing empty dataset 'support' (2 rows)" in printed.out + printed.err


def test_a_dataset_with_a_version_the_sdk_did_not_write_still_needs_the_opt_in(tmp_path):
    server = ContractServer()
    did = server.add_dataset("support")
    server.datasets[did]["versions"].append({"id": "6f1c8a52-0000-4000-8000-000000000001", "dataset": did,
                                             "parent_version": None, "metadata": {}, "items": [],
                                             "created_at": "2026-10-01T00:00:00Z"})  # made in the app
    with pytest.raises(DatasetNotOwnedError, match="has a first version that fi.experiments did not write"):
        _run(server, _named(tmp_path))
    assert server.count("POST", VERSION_POSTS) == 0


def test_add_version_is_the_explicit_opt_in(tmp_path):
    server = ContractServer()
    did = server.add_dataset("support", [{"question": "made in the UI", "expected": "x"}])
    result = _run(server, _named(tmp_path, add_version=True))
    assert result.status == "completed" and result.dataset_id == did
    assert len(server.datasets[did]["versions"]) == 1


def test_another_name_keeps_the_rows_apart(tmp_path):
    server = ContractServer()
    ui = server.add_dataset("support", [{"question": "made in the UI", "expected": "x"}])
    result = _run(server, experiments.dataset(_file(tmp_path), name="support-sdk"))
    assert result.dataset_id != ui and server.datasets[result.dataset_id]["name"] == "support-sdk"
    assert server.datasets[ui]["versions"] == []


def test_a_dataset_the_sdk_made_gets_new_versions_without_opt_in(tmp_path):
    server = ContractServer()
    first = _run(server, _named(tmp_path))
    edited = [dict(ROWS[0], expected="delivered"), ROWS[1]]
    second = _run(server, _named(tmp_path, rows=edited))  # a later run, a fresh process: found by name
    assert second.dataset_id == first.dataset_id
    assert len(server.datasets[first.dataset_id]["versions"]) == 2


def test_rows_equal_to_the_latest_version_add_nothing_so_nothing_is_refused(tmp_path):
    server = ContractServer()
    first = _run(server, _named(tmp_path))
    again = _run(server, _named(tmp_path))
    assert again.dataset_version_id == first.dataset_version_id
    assert server.count("POST", VERSION_POSTS) == 1


def test_a_server_dataset_named_explicitly_is_still_snapshotted():
    server = ContractServer()
    server.add_dataset("Support tickets", [{"question": "q", "expected": "x"}])
    result = _run(server, "Support tickets")  # its own name: the caller chose that server dataset
    assert result.status == "completed" and server.count("POST", VERSION_POSTS) == 1


# ---- the CLI ---------------------------------------------------------------------------------------


@pytest.fixture
def cli_server(monkeypatch):
    server = ContractServer()
    import fi.experiments._log_results as lr

    real = lr.log_results
    monkeypatch.setattr(lr, "log_results", lambda *a, **k: real(*a, client=client_for(server), **k))
    return server


def test_cli_upload_refuses_then_add_version_or_dataset_name(tmp_path, monkeypatch, cli_server):
    monkeypatch.chdir(tmp_path)
    did = cli_server.add_dataset("support", [{"question": "made in the UI", "expected": "x"}])
    _file(tmp_path)
    (tmp_path / "results.jsonl").write_text(json.dumps({"id": "T0", "output": "shipped"}) + "\n")
    code, out, err = cli("upload", "results.jsonl", "--dataset", "support.jsonl", "--dataset-name", "support",
                         "--no-env-file")
    assert code == 2 and "dataset 'support' already exists" in err and "--add-version" in err
    assert cli_server.datasets[did]["versions"] == []
    code, out, err = cli("upload", "results.jsonl", "--dataset", "support.jsonl", "--dataset-name", "support-sdk",
                         "--json", "--no-env-file")
    assert code == 0, err
    assert [d["name"] for d in cli_server.datasets.values()] == ["support", "support-sdk"]
    code, out, err = cli("upload", "results.jsonl", "--dataset", "support.jsonl", "--dataset-name", "support",
                         "--add-version", "--json", "--no-env-file")
    assert code == 0, err
    assert len(cli_server.datasets[did]["versions"]) == 1
