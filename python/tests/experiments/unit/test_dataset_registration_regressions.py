"""L-SDK2b regression coverage, S2 and S4, against the contract stand-in (``contract_server.py``); no network, no model.

- S1: the refusal to version a dataset says only what it saw. The SDK's own dataset whose first ``versions.create``
  failed (a POST is never retried) is empty and versionless. The dataset service decision after wave 2b (S1) lets such a dataset
  take its first version without an opt-in only through one conditional server operation, which the
  server does not have yet, so the retry is refused for what was seen and ``add_version=True`` stores the rows. An
  SDK-made dataset with rows added in the app is refused for its table rows, never with a claim about who made it.
- S2: ``name=`` / ``--dataset-name`` / ``--add-version`` are refused on a server dataset (exit 2), never ignored; with
  ``--no-upload`` the CLI refuses them and ``upload=False`` warns.
- S4: two templates whose names fold to one slug get two metric names.
"""

import json
import re

import pytest

from fi import experiments
from fi.experiments._server_dataset import DatasetNotOwnedError
from fi.experiments.errors import UsageError
from fi.experiments.evaluators.hosted import Template, metric_name
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer, client_for, err

ROWS = [{"id": "T0", "question": "where is order 1?", "expected": "shipped"},
        {"id": "T1", "question": "where is order 2?", "expected": "lost"}]
VERSION_POSTS = r"/model-hub/datasets/.*/versions/"


def task(row):
    return "shipped"


def _run(server, dataset, **kw):
    return experiments.run(dataset, task, [], client=client_for(server), trace=False, progress=False, **kw)


class FirstVersionFails(ContractServer):
    """The SDK creates the dataset, then its first versions.create fails once (a 503: never retried on a POST)."""

    def __init__(self):
        super().__init__()
        self.fail_versions = [503]

    def _versions(self, did, method, body, q):
        if method == "POST" and self.fail_versions:
            return err(self.fail_versions.pop(0), "temporarily unavailable")
        return super()._versions(did, method, body, q)


# ---- S1 ----------------------------------------------------------------------------------------------


def test_S1_the_retry_after_a_failed_first_version_is_refused_for_what_was_seen_and_stored_with_the_opt_in():
    """The dataset run 1 made is empty and has no version. Without a conditional create on the server
    the same call again is refused before any write, saying what it saw; add_version=True stores the rows."""
    server = FirstVersionFails()
    ds = experiments.dataset(ROWS, name="support-cases")
    with pytest.raises(Exception) as first:
        _run(server, ds)
    assert not isinstance(first.value, DatasetNotOwnedError)
    [made] = server.datasets.values()
    assert made["name"] == "support-cases" and made["versions"] == []  # made by run 1; no version landed
    posts = server.count("POST", VERSION_POSTS)
    with pytest.raises(DatasetNotOwnedError) as again:
        _run(server, ds)  # the same call again, no opt-in
    message = str(again.value)
    assert "'support-cases' already exists on the server and is empty and has no version yet" in message
    assert "An earlier run that stopped before storing its rows" in message and "Nothing was stored" in message
    assert "add_version=True" in message and "--add-version" in message
    assert "was not created by fi.experiments" not in message
    assert server.count("POST", VERSION_POSTS) == posts and made["versions"] == []
    result = _run(server, experiments.dataset(ROWS, name="support-cases", add_version=True))
    assert result.status == "completed" and len(made["versions"]) == 1


def test_S1_an_sdk_dataset_with_rows_added_in_the_app_is_refused_for_what_was_seen(tmp_path):
    server = ContractServer()
    first = _run(server, experiments.dataset(ROWS, name="support-cases"))
    server.datasets[first.dataset_id]["rows"].append({"row_id": "app-row"})  # a row added in the app
    with pytest.raises(DatasetNotOwnedError) as info:
        _run(server, experiments.dataset([dict(ROWS[0], expected="delivered"), ROWS[1]], name="support-cases"))
    message = str(info.value)
    assert "has table rows, which fi.experiments never writes" in message
    assert "was not created by fi.experiments" not in message


# ---- S2 ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("spec", [dict(name="support-copy"), dict(add_version=True)])
def test_S2_name_or_add_version_on_a_server_dataset_is_refused_before_any_request(spec):
    server = ContractServer()
    server.add_dataset("Support tickets", [{"question": "q", "expected": "x"}])
    with pytest.raises(UsageError) as info:
        _run(server, experiments.dataset("Support tickets", **spec))
    assert "'Support tickets' is a server dataset" in str(info.value) and "--dataset-name" in str(info.value)
    assert server.requests == []


def test_S2_log_results_refuses_them_too():
    server = ContractServer()
    server.add_dataset("Support tickets", [{"id": "T0", "question": "q", "expected": "x"}])
    with pytest.raises(UsageError, match="is a server dataset"):
        experiments.log_results(experiments.dataset("Support tickets", name="elsewhere"), [{"id": "T0", "output": "x"}],
                                client=client_for(server), progress=False)
    assert server.requests == []


@pytest.fixture
def cli_server(monkeypatch):
    server = ContractServer()
    import fi.experiments._log_results as lr

    real = lr.log_results
    monkeypatch.setattr(lr, "log_results", lambda *a, **k: real(*a, client=client_for(server), **k))
    return server


@pytest.mark.parametrize("flags", [["--dataset-name", "elsewhere"], ["--add-version"]])
def test_S2_cli_upload_with_a_server_dataset_exits_2(tmp_path, monkeypatch, cli_server, flags):
    monkeypatch.chdir(tmp_path)
    did = cli_server.add_dataset("Support tickets", [{"id": "T0", "question": "where is order 1?", "expected": "x"}])
    (tmp_path / "results.jsonl").write_text(json.dumps({"id": "T0", "output": "shipped"}) + "\n")
    code, out, err_ = cli("upload", "results.jsonl", "--dataset", "Support tickets", *flags, "--json", "--no-env-file")
    said = out + err_  # --json puts the error object on stdout
    assert code == 2 and "--dataset-name" in said and "is a server dataset" in said, (code, out[-300:], err_[-300:])
    assert [d["name"] for d in cli_server.datasets.values()] == ["Support tickets"]
    assert cli_server.datasets[did]["versions"] == [] and cli_server.requests == []


@pytest.mark.parametrize("flags", [["--dataset-name", "support-sdk"], ["--add-version"]])
def test_S2_cli_run_no_upload_refuses_dataset_name_and_add_version(tmp_path, monkeypatch, flags):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "rows.jsonl").write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    code, out, err_ = cli("run", "--from-column", "expected", "--dataset", "rows.jsonl", "--no-upload", *flags,
                          "--no-trace", "--no-env-file")
    assert code == 2 and "--no-upload nothing is stored" in err_, (code, err_[-300:])


def test_S2_upload_false_with_a_name_warns():
    with pytest.warns(UserWarning, match="uploads nothing"):
        result = experiments.run(experiments.dataset(ROWS, name="support-cases"), task, [], upload=False,
                                 trace=False, progress=False)
    assert result.status == "no_upload"


# ---- S4 ----------------------------------------------------------------------------------------------

SERVER_EVAL_NAME = re.compile(r"^(?![-_])(?!.*(_-|-_))[a-z0-9_-]{1,50}(?<![-_])$")  # validate_eval_name


def test_S4_two_templates_that_fold_to_one_slug_get_two_metric_names():
    a = metric_name(Template("Is JSON", {}), {"text": "output"}, None)
    b = metric_name(Template("is-json", {}), {"text": "output"}, None)
    assert a != b and a.startswith("sdk-is-json-") and b.startswith("sdk-is-json-")
    assert a == metric_name(Template("Is JSON", {}), {"text": "output"}, None)  # still deterministic
    assert SERVER_EVAL_NAME.match(a) and SERVER_EVAL_NAME.match(b)


def test_a_taken_name_says_how_to_choose_another():
    server = ContractServer()
    server.add_dataset("support", [{"question": "q"}], listed=False)  # a source get-datasets-names does not list
    with pytest.raises(UsageError) as info:
        _run(server, experiments.dataset(ROWS, name="support"))
    assert "name=" in str(info.value) and "--dataset-name NAME" in str(info.value)
    assert "Rename the file" not in str(info.value)
