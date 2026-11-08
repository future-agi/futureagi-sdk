"""dataset service decisions after wave 2b, against the contract stand-in; no network, no model.

- **S3 (a):** a rows file on an uploaded run needs a dataset name, exactly as the dataset contract is written ("inline rows or
  files"). The error comes before any request and shows the exact command (CLI, from this invocation's argv) or
  call (Python) with the file's stem filled in, so the fix is one copy-paste.
- **S1 under the atomic-create contract:** an existing dataset that is empty and has no version may take its first version without
  an opt-in only when the server checks "empty and unversioned" and creates the version in ONE conditional
  operation, so two concurrent first writes can never both land. The server's ``versions.create`` has no such
  condition yet, so the opt-in stays required for this case too. The case it is for: a first run created the
  dataset and stopped before its first version landed (a 503 on ``versions.create`` is never retried). The retry is
  refused before any write, the refusal says it saw an empty dataset with no version and how to opt in, and with
  ``add_version=True`` the output says it wrote that dataset's first version (``test_side_effect_datasets.py``).
"""

import json
import sys

import pytest

from fi import experiments
from fi.experiments._server_dataset import DatasetNameRequiredError, DatasetNotOwnedError
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer, client_for, err

ROWS = [{"id": "T0", "question": "where is order 1?", "expected": "shipped"},
        {"id": "T1", "question": "where is order 2?", "expected": "lost"}]


def task(row):
    return "shipped"


def _file(tmp_path, name="rows.jsonl"):
    path = tmp_path / name
    path.write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    return str(path)


def _run(server, dataset, **kw):
    return experiments.run(dataset, task, [], client=client_for(server), trace=False, progress=False, **kw)


# ---- S3 (a): a file needs a name --------------------------------------------------------------------


def test_a_rows_file_on_an_uploaded_run_needs_a_name_before_any_request(tmp_path):
    server = ContractServer()
    path = _file(tmp_path)
    with pytest.raises(DatasetNameRequiredError) as info:
        _run(server, path)
    message = str(info.value)
    assert f'experiments.dataset("{path}", name="rows")' in message  # the call, the stem filled in
    assert "(CLI: --dataset-name rows)" in message and "upload=False" in message
    assert "collide across the projects of one organization" in message
    assert info.value.get_error_code() == "DATASET_NAME_REQUIRED" and info.value.exit_code == 2
    assert server.requests == []  # nothing created, nothing even asked


def test_the_same_file_with_a_name_is_stored_under_that_name(tmp_path):
    server = ContractServer()
    result = _run(server, experiments.dataset(_file(tmp_path), name="support-cases"))
    [ds] = server.datasets.values()
    assert result.status == "completed" and ds["name"] == "support-cases" and len(ds["versions"]) == 1


def test_a_local_run_of_a_file_needs_no_name(tmp_path):
    result = experiments.run(_file(tmp_path), task, [], upload=False, trace=False, progress=False)
    assert result.status == "no_upload" and len(result.items) == 2


def test_log_results_with_a_file_needs_a_name_too(tmp_path):
    server = ContractServer()
    with pytest.raises(DatasetNameRequiredError, match="needs a dataset name"):
        experiments.log_results(_file(tmp_path), [{"id": "T0", "output": "x"}], client=client_for(server),
                                progress=False)
    assert server.requests == []


def test_cli_run_shows_the_exact_command_with_the_stem_filled_in(tmp_path, monkeypatch):
    (tmp_path / "agent.py").write_text("def support(row):\n    return 'shipped'\n")
    _file(tmp_path, "support.jsonl")
    argv = ["run", "agent.py:support", "--dataset", "support.jsonl", "--limit", "1"]  # a path: never a cached module
    monkeypatch.setattr(sys, "argv", ["futureagi-py", *argv])  # the CLI's own argv, as a console script sees it
    monkeypatch.setenv("FI_API_KEY", "k" * 16)
    monkeypatch.setenv("FI_SECRET_KEY", "s" * 16)
    code, out, err_text = cli(*argv)
    assert code == 2, err_text
    assert "futureagi-py run agent.py:support --dataset support.jsonl --limit 1 --dataset-name support" in err_text
    assert 'in a run file: experiments.dataset("support.jsonl", name="support")' in err_text
    assert "or add --no-upload to store nothing" in err_text


def test_cli_upload_shows_its_own_command_and_no_no_upload(tmp_path, monkeypatch):
    _file(tmp_path, "support.jsonl")
    (tmp_path / "results.jsonl").write_text(json.dumps({"id": "T0", "output": "shipped"}) + "\n")
    argv = ["upload", "results.jsonl", "--dataset", "support.jsonl", "--no-env-file"]
    monkeypatch.setattr(sys, "argv", ["futureagi-py", *argv])
    monkeypatch.setenv("FI_API_KEY", "k" * 16)
    monkeypatch.setenv("FI_SECRET_KEY", "s" * 16)
    code, out, err_text = cli(*argv, "--json")
    assert code == 2
    error = json.loads(out)["error"]
    assert error["code"] == "DATASET_NAME_REQUIRED"
    assert "futureagi-py upload results.jsonl --dataset support.jsonl --no-env-file --dataset-name support" in error[
        "message"]
    assert "--no-upload" not in error["message"]


def test_the_command_line_hides_a_secret_and_says_so(tmp_path, monkeypatch):
    (tmp_path / "agent.py").write_text("def support(row):\n    return 'shipped'\n")
    _file(tmp_path, "support.jsonl")
    fake = "e2e-fake-" + "not-a-key-0042"  # built at run time: the pre-ship scan reads literals
    argv = ["run", "agent.py:support", "--dataset", "support.jsonl", "--param", "api" + "_key=" + fake]
    monkeypatch.setattr(sys, "argv", ["futureagi-py", *argv])
    monkeypatch.setenv("FI_API_KEY", "k" * 16)
    monkeypatch.setenv("FI_SECRET_KEY", "s" * 16)
    code, out, err_text = cli(*argv)
    assert code == 2 and fake not in err_text
    assert "api_key=[redacted]" in err_text and "put the real value(s) back" in err_text


# ---- S1: an empty, versionless dataset (the atomic-create contract: the opt-in stays) -----------------------------------


class FirstVersionFails(ContractServer):
    """The SDK creates the dataset, then its first versions.create fails once (a 503: never retried on a POST)."""

    def __init__(self):
        super().__init__()
        self.fail_versions = [503]

    def _versions(self, did, method, body, q):
        if method == "POST" and self.fail_versions:
            return err(self.fail_versions.pop(0), "temporarily unavailable")
        return super()._versions(did, method, body, q)


def test_the_retry_after_an_interrupted_first_run_is_refused_then_the_opt_in_stores_the_rows_and_says_so(capsys):
    server = FirstVersionFails()
    ds = experiments.dataset(ROWS, name="support-cases")
    with pytest.raises(Exception):
        _run(server, ds)  # run 1: the dataset is made, its first version never lands
    [made] = server.datasets.values()
    assert made["name"] == "support-cases" and made["versions"] == [] and made["rows"] == []
    with pytest.raises(DatasetNotOwnedError) as refused:
        _run(server, ds)  # the same call again: refused before any write (no conditional create on the server)
    assert "is empty and has no version yet" in str(refused.value)
    assert 'name=\'support-cases\', add_version=True' in str(refused.value) and made["versions"] == []
    capsys.readouterr()
    opted = experiments.dataset(ROWS, name="support-cases", add_version=True)
    result = experiments.run(opted, task, [], client=client_for(server), trace=False)
    assert result.status == "completed" and result.dataset_id == made["id"] and len(made["versions"]) == 1
    printed = capsys.readouterr()
    text = printed.out + printed.err
    assert "wrote the first version of the existing empty dataset 'support-cases' (2 rows)" in text
    again = _run(server, ds)  # a third run, no opt-in: that version is the SDK's own, the rows are it, nothing new
    assert again.dataset_version_id == result.dataset_version_id and len(made["versions"]) == 1
