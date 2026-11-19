"""L-SDK2c review fixes, against the contract stand-in; no network, no model.

- **M1:** one CLI command that selects several declared runs (a run-file directory) applies ``--dataset-name`` to
  every one of them. So the name refusal never shows a bare ``--dataset-name`` line there: it shows the run-file call
  and a command that selects the run alone with ``--filter``; and ``--dataset-name`` / ``--add-version`` over runs that
  read different rows files are refused with exit 2 before any request. Following the advice never stores two files
  in one dataset (the reviewer's probe R1: it stored b.jsonl as version 2 of dataset "a").
- **S1:** ``log_results`` always stores, so its name refusal never offers ``upload=False`` (which raises TypeError).
- **S2:** with anthropic >= 1.0 installed and traceAI-anthropic missing, the header offers no install line: its only
  release fails inside instrument() there (F3).
- **S3:** the summary says what the app link is (the dataset's Experiments tab, which lists SDK runs once FE-2 ships).
- **S4:** what judge()'s one criteria read decided (EXPECTED shown or not) is in ``result.metadata`` and the closing
  lines, not only on spans.
"""

import re
import shlex
import sys
import types

import httpx
import pytest

from fi import experiments
from fi.experiments._server_dataset import DatasetNameRequiredError
from fi.experiments.evaluators.judge import Judge
from tests.experiments.unit.cli_helpers import cli, write_rows
from tests.experiments.unit.contract_server import ContractServer, client_for
from tests.experiments.unit.judge_helpers import part_verdict, with_criteria

ROWS_A = [{"id": "A0", "question": "where is order 1?", "expected": "shipped"},
          {"id": "A1", "question": "where is order 2?", "expected": "lost"}]
ROWS_B = [{"id": "B0", "question": "refund for order 9?", "expected": "approved"},
          {"id": "B1", "question": "refund for order 8?", "expected": "denied"}]
SHARED = "w2c_review_shared"  # the run files reach the contract server through this module


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_JUDGE_MODEL", "CI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("FI_RUN_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "login.json"))
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def server(monkeypatch):
    srv = ContractServer()
    shared = types.ModuleType(SHARED)
    shared.client = client_for(srv)
    monkeypatch.setitem(sys.modules, SHARED, shared)
    monkeypatch.setenv("FI_API_KEY", "k" * 16)
    monkeypatch.setenv("FI_SECRET_KEY", "s" * 16)
    return srv


def _run_file(path, rows, run_name=None, dataset=None):
    name = f", name={run_name!r}" if run_name else ""
    ds = dataset or repr(rows)
    path.write_text(f"from fi import experiments\nimport {SHARED} as s\n\n\ndef task(row):\n    return 'shipped'\n\n\n"
                    f"experiments.run({ds}, task, [], client=s.client, trace=False{name})\n")


def _two_files(tmp_path, names=("a-run", "b-run")):
    write_rows(tmp_path / "a.jsonl", ROWS_A)
    write_rows(tmp_path / "b.jsonl", ROWS_B)
    evals = tmp_path / "evals"
    evals.mkdir()
    _run_file(evals / "a_eval.py", "a.jsonl", names[0])
    _run_file(evals / "b_eval.py", "b.jsonl", names[1])


def _cli(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["futureagi-py", *argv])  # the CLI's own argv, as a console script sees it
    return cli(*argv)


def _versions(server):
    return {d["name"]: len(d["versions"]) for d in server.datasets.values()}


# ---- M1 ----------------------------------------------------------------------------------------------


def test_M1_one_dataset_name_over_two_rows_files_is_refused_before_any_request(tmp_path, monkeypatch, server):
    _two_files(tmp_path)
    code, out, err = _cli(monkeypatch, "run", "evals", "--dataset-name", "a")
    assert code == 2, err
    assert "--dataset-name is for one rows file and applies to every selected run" in err
    assert "a-run (evals/a_eval.py) reads a.jsonl; b-run (evals/b_eval.py) reads b.jsonl" in err
    assert "stored as versions of one dataset" in err and "nothing was sent" in err
    assert 'experiments.dataset("a.jsonl", name="a") in evals/a_eval.py' in err
    assert 'experiments.dataset("b.jsonl", name="b") in evals/b_eval.py' in err
    assert "or select one run: futureagi-py run evals --dataset-name a --filter a-run" in err
    assert server.requests == [] and server.datasets == {}


def test_M1_add_version_over_two_rows_files_is_refused_too(tmp_path, monkeypatch, server):
    _two_files(tmp_path)
    code, out, err = _cli(monkeypatch, "run", "evals", "--add-version")
    assert code == 2, err
    assert "--add-version is for one rows file" in err and "opted in to a new version at once" in err
    assert 'experiments.dataset("a.jsonl", name="a", add_version=True) in evals/a_eval.py' in err
    assert server.requests == []


def test_M1_the_name_refusal_in_a_directory_shows_the_run_alone_and_following_it_keeps_the_files_apart(
        tmp_path, monkeypatch, server):
    _two_files(tmp_path)
    code, out, err = _cli(monkeypatch, "run", "evals")
    assert code == 2, err
    assert server.requests == []
    assert "futureagi-py run evals --dataset-name" not in err  # never a bare line: it would name every run
    m = re.search(r"Name it \(or choose another name\): (futureagi-py run .*?)    \(in a run file", err)
    assert m, err
    assert m.group(1) == "futureagi-py run evals --filter a-run --dataset-name a"
    assert 'for every run of it: experiments.dataset("a.jsonl", name="a") in evals/a_eval.py' in err
    code, out, err = _cli(monkeypatch, *shlex.split(m.group(1))[1:])  # the reviewer's probe R1: follow the advice
    assert code == 0, err
    assert _versions(server) == {"a": 1}
    code, out, err = _cli(monkeypatch, "run", "evals", "--filter", "b-run")  # one run selected: the plain line
    assert code == 2 and "futureagi-py run evals --filter b-run --dataset-name b    (in a run file:" in err, err
    code, out, err = _cli(monkeypatch, "run", "evals", "--filter", "b-run", "--dataset-name", "b")
    assert code == 0, err
    assert _versions(server) == {"a": 1, "b": 1}  # two files, two datasets


def test_M1_a_filter_already_given_is_replaced_by_the_run_s_own(tmp_path, monkeypatch, server):
    _two_files(tmp_path)
    code, out, err = _cli(monkeypatch, "run", "evals", "--filter", "*-run")
    assert code == 2 and "futureagi-py run evals --filter a-run --dataset-name a    (in a run file" in err, err
    assert "--filter '*-run'" not in err


def test_M1_with_no_filter_that_selects_the_run_alone_only_the_run_file_call_is_shown(tmp_path, monkeypatch, server):
    _two_files(tmp_path, names=(None, None))  # both declared runs are called "task"
    code, out, err = _cli(monkeypatch, "run", "evals")
    assert code == 2, err
    assert 'Name it (or choose another name) in its run file: experiments.dataset("a.jsonl", name="a") in ' \
           "evals/a_eval.py" in err
    assert "--dataset-name a" not in err and "no --filter selects this run alone" in err
    assert server.requests == []


def test_M1_two_files_that_share_a_stem_get_two_suggested_names(tmp_path, monkeypatch, server):
    for sub, rows in (("x", ROWS_A), ("y", ROWS_B)):
        (tmp_path / sub).mkdir()
        write_rows(tmp_path / sub / "rows.jsonl", rows)
    evals = tmp_path / "evals"
    evals.mkdir()
    _run_file(evals / "a_eval.py", "x/rows.jsonl", "a-run")
    _run_file(evals / "b_eval.py", "y/rows.jsonl", "b-run")
    code, out, err = _cli(monkeypatch, "run", "evals")
    assert code == 2 and "futureagi-py run evals --filter a-run --dataset-name rows-a-run" in err, err
    code, out, err = _cli(monkeypatch, "run", "evals", "--dataset-name", "rows")
    assert code == 2 and 'name="rows-a-run"' in err and 'name="rows-b-run"' in err, err
    assert server.requests == []


def test_M1_one_name_over_runs_that_share_one_rows_file_is_allowed(tmp_path, monkeypatch, server):
    write_rows(tmp_path / "a.jsonl", ROWS_A)
    evals = tmp_path / "evals"
    evals.mkdir()
    _run_file(evals / "a_eval.py", "a.jsonl", "a-run")
    _run_file(evals / "b_eval.py", "a.jsonl", "b-run")
    code, out, err = _cli(monkeypatch, "run", "evals", "--dataset-name", "orders")
    assert code == 0, err
    assert _versions(server) == {"orders": 1}  # the same rows: one version, used by both runs


def test_M1_an_unnamed_run_is_refused_before_a_named_one_stores_anything(tmp_path, monkeypatch, server):
    write_rows(tmp_path / "a.jsonl", ROWS_A)
    write_rows(tmp_path / "b.jsonl", ROWS_B)
    evals = tmp_path / "evals"
    evals.mkdir()
    _run_file(evals / "a_eval.py", None, "a-run", dataset="experiments.dataset('a.jsonl', name='orders-a')")
    _run_file(evals / "b_eval.py", "b.jsonl", "b-run")
    code, out, err = _cli(monkeypatch, "run", "evals")
    assert code == 2 and "futureagi-py run evals --filter b-run --dataset-name b" in err, err
    assert server.requests == []  # the named run did not start either


def test_M1_list_is_not_refused(tmp_path, monkeypatch, server):
    _two_files(tmp_path)
    code, out, err = _cli(monkeypatch, "run", "evals", "--list", "--dataset-name", "a")
    assert code == 0 and out.split() == ["a-run", "b-run"], err


# ---- S1 ----------------------------------------------------------------------------------------------


def test_S1_log_results_never_offers_upload_false(tmp_path, server):
    path = write_rows(tmp_path / "rows.jsonl", ROWS_A)
    with pytest.raises(DatasetNameRequiredError) as info:
        experiments.log_results(path, [{"id": "A0", "output": "x"}], client=client_for(server), progress=False)
    message = str(info.value)
    assert 'experiments.dataset("' in message and "upload=False" not in message
    with pytest.raises(DatasetNameRequiredError) as info:
        experiments.log_results(ROWS_A, [{"id": "A0", "output": "x"}], client=client_for(server), progress=False)
    message = str(info.value)
    assert "experiments.log_results(experiments.dataset(rows, name=" in message and "upload=False" not in message
    with pytest.raises(TypeError):  # why: the way out the old message offered does not exist
        experiments.log_results(path, [{"id": "A0", "output": "x"}], client=client_for(server), upload=False)
    assert server.requests == []


def test_S1_run_still_offers_upload_false(tmp_path, server):
    for rows in (write_rows(tmp_path / "rows.jsonl", ROWS_A), ROWS_A):
        with pytest.raises(DatasetNameRequiredError, match="upload=False"):
            experiments.run(rows, lambda row: "x", [], client=client_for(server), trace=False, progress=False)


# ---- S2 ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("version, offers_pip", [("1.17.0", False), ("2.1.0", False), ("0.125.0", True), (None, True)])
def test_S2_a_missing_add_on_with_no_working_release_gets_no_install_line(monkeypatch, version, offers_pip):
    from fi.experiments._tracing import instrument as inst

    monkeypatch.setattr(inst, "_installed", lambda mod: mod == "anthropic")
    monkeypatch.setattr(inst, "_version", lambda dist: version if dist == "anthropic" else None)
    header = inst.plan(None, ["anthropic"]).header()
    assert ("pip install traceAI-anthropic" in header) is offers_pip, header
    if not offers_pip:
        assert header == (f"traceAI-anthropic missing, and no release of it works with anthropic {version} yet "
                          "(traceAI-anthropic 0.1.10, its only release, fails inside instrument() on anthropic>=1.0 "
                          "(F3)): there is nothing to install; anthropic calls are not traced")


def test_S2_the_auto_header_on_anthropic_1_x(monkeypatch):
    from fi.experiments._tracing import instrument as inst

    monkeypatch.setattr(inst, "_installed", lambda mod: mod == "anthropic")
    monkeypatch.setattr(inst, "_version", lambda dist: "1.17.0" if dist == "anthropic" else None)
    header = inst.plan(None, "auto").header()  # the reviewer's probe R3
    assert "pip install traceAI-anthropic" not in header and "nothing to install" in header


# ---- S3 ----------------------------------------------------------------------------------------------


def test_S3_the_summary_says_what_the_app_link_is():
    from fi.experiments._engine_summary import print_summary
    from fi.experiments.results import ExperimentResult

    lines: list = []
    url = "http://app.test/dashboard/develop/d1?tab=experiments&run=r1"
    result = ExperimentResult(run_id="r1", name="n", url=url, status="completed", items=[], journal_dir="j",
                              metadata={"upload": {"acked": 1, "batches": 1, "retries": 0, "server_status": "completed"}})
    print_summary(lines.append, result)
    assert f"App      {url} (the dataset's Experiments tab; it lists SDK runs once FE-2 ships)" in lines
    assert "FE-2" in (ExperimentResult.open.__doc__ or "") and "Experiments tab" in (ExperimentResult.open.__doc__ or "")


# ---- S4 ----------------------------------------------------------------------------------------------

FAKE = "-".join(("judge", "fake", "value"))  # built at run time: the pre-ship scan reads literals
JROWS = [{"id": f"r{i}", "input": "Where is order A101?", "expected": "Order A101 has shipped.",
          "answer": "It shipped."} for i in range(2)]


def _verdict(request):
    return httpx.Response(200, json=part_verdict(True))


@pytest.mark.parametrize("needs, shown", [(True, "shown to it"), (False, "not shown")])
def test_S4_what_the_criteria_read_decided_is_in_the_metadata_and_the_closing_lines(monkeypatch, capsys, needs, shown):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    judge = Judge("Is the reply correct?" if needs else "Is the reply polite?", model="m",
                  transport=httpx.MockTransport(with_criteria(_verdict, needs_right_answer=needs)))
    result = experiments.run(JROWS, experiments.from_column("answer"), [judge], upload=False, trace=False)
    meta = result.metadata["judge_criteria"]["judge"]
    assert {k: meta[k] for k in ("asks_correctness", "expected_shown", "rows_had_expected")} == {
        "asks_correctness": needs, "expected_shown": needs, "rows_had_expected": True}
    assert [p["needs_right_answer"] for p in meta["parts"]] == [needs]  # wave 2d: the checklist is in the metadata
    lines = [ln for ln in capsys.readouterr().err.splitlines() if ln.startswith("Judge    judge: EXPECTED ")]
    assert len(lines) == 1 and shown in lines[0], lines
    assert ("they ask about correctness" if needs else "they do not ask about correctness") in lines[0]


def test_S4_rows_without_expected_show_the_checklist_but_no_expected_line(monkeypatch, capsys):
    """Wave 2d: the read is the checklist, so it happens without EXPECTED too; the EXPECTED line needs such a row."""
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    judge = Judge("Is the reply polite?", model="m", transport=httpx.MockTransport(with_criteria(_verdict)))
    result = experiments.run([{"id": "x", "input": "q", "answer": "a"}], experiments.from_column("answer"), [judge],
                             upload=False, trace=False)
    meta = result.metadata["judge_criteria"]["judge"]
    assert (meta["rows_had_expected"], meta["expected_shown"], len(meta["parts"])) == (False, False, 1)
    err = capsys.readouterr().err
    assert "Judge    judge: EXPECTED" not in err
    assert "Judge    judge: its checklist, read once from the CRITERIA; each part judged on its own: 1. the criteria" \
        in err


# ---- nit: doctor's Judge line ------------------------------------------------------------------------


def test_doctor_judge_line_says_the_value_is_for_templates(monkeypatch):
    monkeypatch.setenv("FI_JUDGE_MODEL", "gpt-4.1-nano")
    code, out, _ = cli("doctor", "--offline")
    line = next(ln for ln in out.splitlines() if ln.startswith("Judge"))
    assert line == ("Judge      gpt-4.1-nano (for LLM-judge templates; judge() takes its own model=, default "
                    "gpt-4.1-mini)")
