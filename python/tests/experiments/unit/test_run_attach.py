"""``futureagi-py run TARGET --run RUN``: add results to a run that was created elsewhere (for example in the app).

The run is read back from the contract stand-in (``contract_server.py``), which answers the run read and the items
list in the server's own response shapes. Nothing here touches a network.
"""

import shlex
import sys
import uuid
from pathlib import Path

import pytest

from fi.experiments import _upload
from fi.experiments._journal import load as load_journal
from tests.experiments.unit.cli_helpers import cli, write_rows
from tests.experiments.unit.contract_server import ContractServer, client_for

QUESTIONS = [f"where is order {i}?" for i in range(1, 6)]
ROWS = [{"question": q, "expected": "shipped"} for q in QUESTIONS]

TASK = '''\
from fi import experiments


def task(row):
    with open("calls.txt", "a", encoding="utf-8") as fh:
        fh.write(row["question"] + "\\n")
    return "shipped"


def correct(output, expected) -> bool:
    return output == expected

'''
RUN_FILE = TASK + 'experiments.run("support-rows", task, [correct])\n'
FLAGS = ("--dataset", "support-rows", "--no-trace", "--no-env-file")


@pytest.fixture
def server(monkeypatch):
    import fi.futureagi_client as client_module

    srv = ContractServer()
    client = client_for(srv)
    monkeypatch.setattr(client_module, "FutureAGIClient", lambda *a, **k: client)
    Path("attach_eval.py").write_text(RUN_FILE)
    write_rows(Path("rows.jsonl"), ROWS)
    return srv


def _app_run(server, recorded=2, **state):
    """A run made in the app on the version and metric a first run stored: a new id, a plan of 5 trials, ``recorded``
    of them already stored by someone else. ``state`` seeds its status, task kind or completion time."""
    code, _, err = cli("run", "attach_eval.py", "--dataset", "rows.jsonl", "--dataset-name", "support-rows",
                       "--no-trace", "--no-env-file", "--quiet")
    assert code == 0, err
    [first] = server.runs.values()
    run_id = str(uuid.uuid4())
    body = {**first["body"], "run_id": run_id, "metadata": {"name": "made in the app"}}
    planned = [(e["example_id"], e["trial_number"]) for e in body["expected_items"]]
    items = {}
    for example_id, trial in planned[:recorded]:
        payload = {"example_id": example_id, "trial_number": trial, "receipt_key": f"app-{example_id}",
                   "status": "completed", "output": "shipped", "error": None, "trace_id": None,
                   "root_span_id": None, "latency_ms": 1.0, "token_usage": None, "cost": None, "score_refs": []}
        items[(example_id, trial)] = {**payload, "_payload": payload}
    server.runs[run_id] = {"body": body, "items": items, **state}
    Path("calls.txt").unlink()
    server.requests.clear()
    server.queries.clear()
    return run_id, planned


def _question_of(server):
    [version] = next(d for d in server.datasets.values() if d["versions"])["versions"]
    return {it["example_id"]: it["input"]["question"] for it in version["items"]}


def _ran():
    path = Path("calls.txt")
    return sorted(path.read_text().splitlines()) if path.exists() else []


def _one_line(err):
    lines = [line for line in err.strip().splitlines() if line.strip()]
    assert len(lines) == 1, err
    return lines[0]


def test_run_adds_only_the_missing_trials_to_a_run_made_in_the_app(server):
    run_id, planned = _app_run(server)
    code, out, err = cli("run", "attach_eval.py", *FLAGS, "--run", run_id)
    assert code == 0, err
    question_of = _question_of(server)
    assert _ran() == sorted(question_of[e] for e, _ in planned[2:])  # only the 3 trials with no result yet
    assert "2 of 5" in err and "running 3" in err
    assert server.count("POST", r"/model-hub/experiment-runs/") == 0  # no run was created
    posts = [p for m, p, _ in server.requests if m == "POST" and p.endswith("/results/")]
    assert posts and set(posts) == {f"/model-hub/experiment-runs/{run_id}/results/"}
    stored = server.runs[run_id]["items"]
    assert set(stored) == set(planned)
    assert [stored[k]["receipt_key"] for k in planned[:2]] == [f"app-{e}" for e, _ in planned[:2]]  # untouched
    [metric_id] = server.runs[run_id]["body"]["evaluator_metric_ids"]
    for key in planned[2:]:
        assert [ref["metric_id"] for ref in stored[key]["score_refs"]] == [metric_id]
    journal = load_journal(run_id)  # the same journal a normal run keeps
    assert sorted(journal.records) == sorted(planned[2:]) and all(r.acked for r in journal.records.values())


def test_recorded_items_are_listed_page_by_page_with_a_status_filter(server):
    run_id, planned = _app_run(server, recorded=3)
    server.items_page = 1  # the server answers one item per page
    code, _, err = cli("run", "attach_eval.py", *FLAGS, "--run", run_id, "--quiet")
    assert code == 0, err
    assert len(_ran()) == 2
    reads = [q for m, p, q in server.queries if m == "GET" and p == f"/model-hub/experiment-runs/{run_id}/items/"]
    assert len(reads) >= 3 and [int(q.get("offset", 0)) for q in reads[:3]] == [0, 1, 2]
    for q in reads:  # an item still pending or running belongs to someone else's trial
        assert {"pending", "running", "completed", "failed", "skipped"} <= set(q["status"].split(","))
        assert 1 <= int(q["limit"]) <= 500
    assert set(server.runs[run_id]["items"]) == set(planned)


def test_a_run_into_an_app_run_resumes_with_resume(server, monkeypatch):
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    monkeypatch.setattr(_upload, "GIVE_UP_S", 0.0)
    run_id, planned = _app_run(server)
    argv = ["run", "attach_eval.py", *FLAGS, "--run", run_id]
    monkeypatch.setattr(sys, "argv", ["futureagi-py", *argv])
    server.fail_ingest = [503]
    code, _, err = cli(*argv)
    assert code == 3, err
    line = shlex.split(err.split("send the rest with: ", 1)[1].strip())
    assert line[-2:] == ["--resume", run_id] and "--run" not in line
    assert len(server.runs[run_id]["items"]) == 2  # nothing of ours was stored
    Path("calls.txt").unlink()
    monkeypatch.setattr(sys, "argv", line)
    code, _, err = cli(*line[1:])
    assert code == 0, err
    assert _ran() == []  # every trial was journaled: nothing runs again
    assert set(server.runs[run_id]["items"]) == set(planned)
    assert server.count("POST", r"/model-hub/experiment-runs/") == 0


def test_a_run_journaled_here_is_continued_with_resume_not_run(server):
    run_id, _ = _app_run(server)
    assert cli("run", "attach_eval.py", *FLAGS, "--run", run_id, "--quiet")[0] == 0
    server.requests.clear()
    code, _, err = cli("run", "attach_eval.py", *FLAGS, "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert f"--resume {run_id}" in line
    assert not [r for r in server.requests if r[0] == "POST"]


@pytest.mark.parametrize("flags, named", [
    (["--resume", "RUNID"], "--resume"),
    (["--experiment", "7d8b1d7e-6a3c-4f4f-9c0e-6e2b0d6b1a11"], "--experiment"),
    (["--no-upload"], "--no-upload"),
    (["--trials", "2"], "--trials"),
    (["--limit", "1"], "--limit"),
    (["--rows", "1,2"], "--rows"),
])
def test_flags_that_cannot_go_with_run_are_refused_in_one_line(server, flags, named):
    run_id = str(uuid.uuid4())
    code, _, err = cli("run", "attach_eval.py", *FLAGS, "--run", run_id, *[run_id if f == "RUNID" else f for f in flags])
    assert code == 2
    line = _one_line(err)
    assert "--run" in line and named in line and "do not go together" in line
    assert server.requests == []  # refused before any request


def test_a_run_id_that_is_not_a_uuid_is_refused(server):
    code, _, err = cli("run", "attach_eval.py", *FLAGS, "--run", "run-42")
    assert code == 2
    line = _one_line(err)
    assert "--run" in line and "'run-42'" in line and "UUID" in line
    assert server.requests == []


def test_an_unknown_or_hidden_run_is_refused(server):
    _app_run(server)
    missing = str(uuid.uuid4())
    code, _, err = cli("run", "attach_eval.py", *FLAGS, "--run", missing)
    assert code == 2
    line = _one_line(err)
    assert missing in line and "not found" in line and "workspace" in line
    assert not [r for r in server.requests if r[0] == "POST"]
    assert _ran() == []


@pytest.mark.parametrize("recorded, state, word", [
    (5, {}, "completed"),
    (2, {"status": "cancelled"}, "cancelled"),
    (2, {"status": "failed"}, "failed"),
    (2, {"completed_at": "2026-10-23T00:00:00Z", "status": "partial"}, "closed"),
])
def test_a_run_that_takes_no_more_results_is_refused(server, recorded, state, word):
    run_id, _ = _app_run(server, recorded=recorded, **state)
    code, _, err = cli("run", "attach_eval.py", *FLAGS, "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert run_id in line and word in line and "takes no more results" in line
    assert not [r for r in server.requests if r[0] == "POST"]  # nothing was written, not even a metric
    assert _ran() == []


def test_a_run_whose_task_runs_on_the_platform_is_refused(server):
    run_id, _ = _app_run(server, task_kind="prompt")
    code, _, err = cli("run", "attach_eval.py", *FLAGS, "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert run_id in line and "prompt" in line
    assert not [r for r in server.requests if r[0] == "POST"]


def test_evaluators_that_differ_from_the_runs_are_named(server):
    run_id, _ = _app_run(server)
    Path("more_eval.py").write_text(
        TASK + "def short(output) -> bool:\n    return len(output) < 20\n\n\n"
        'experiments.run("support-rows", task, [correct, short])\n')
    code, _, err = cli("run", "more_eval.py", *FLAGS, "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert "short" in line and "evaluators" in line
    Path("none_eval.py").write_text(TASK + 'experiments.run("support-rows", task, [])\n')
    code, _, err = cli("run", "none_eval.py", *FLAGS, "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert "correct" in line and "evaluators" in line
    assert not [p for m, p, _ in server.requests if m == "POST" and "/experiment-runs/" in p]
    assert _ran() == []


def test_a_rows_file_or_another_dataset_is_refused(server):
    run_id, _ = _app_run(server)
    code, _, err = cli("run", "attach_eval.py", "--dataset", "rows.jsonl", "--no-trace", "--no-env-file",
                       "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert "--run" in line and "--dataset" in line and "name or id" in line
    server.add_dataset("other tickets", ROWS)
    code, _, err = cli("run", "attach_eval.py", "--dataset", "other tickets", "--no-trace", "--no-env-file",
                       "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert "'other tickets'" in line and server.runs[run_id]["body"]["dataset_version_id"][:8] in line
    assert not [r for r in server.requests if r[0] == "POST"]
    assert _ran() == []


def test_run_is_listed_in_help_all():
    code, out, _ = cli("run", "--help-all")
    assert code == 0
    rows = [line for line in out.splitlines() if line.strip().startswith("--run ")]
    assert len(rows) == 1 and "created elsewhere" in rows[0]
