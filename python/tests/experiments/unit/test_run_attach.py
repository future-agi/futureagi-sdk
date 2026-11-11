"""``futureagi-py run TARGET --run RUN``: run a target into a run that was created elsewhere (for example in the app).

The run, its recorded items, its experiment and its dataset version are read back from the contract stand-in
(``contract_server.py``) in the server's own response shapes; the run's evaluators are the ones pinned on it, loaded
from the hosted eval API's catalog. Nothing here touches a network.
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
from tests.experiments.unit.test_hosted_mapping import FIXTURE

QUESTIONS = [f"where is order {i}?" for i in range(1, 6)]
ROWS = [{"question": q, "expected": "shipped"} for q in QUESTIONS]
TEMPLATES = {r["name"]: r for r in FIXTURE["response"]["result"]}

TASK = '''\
def run(row):
    with open("calls.txt", "a", encoding="utf-8") as fh:
        fh.write(row["question"] + "\\n")
    return "shipped"


def correct(output, expected) -> bool:
    return output == expected

'''
RUN_FILE = "from fi import experiments\n" + TASK + 'experiments.run("support-rows", run, [correct])\n'
CODE = ("--no-trace", "--no-env-file")  # a code object needs no --dataset with --run


@pytest.fixture
def server(monkeypatch):
    import fi.futureagi_client as client_module

    srv = ContractServer()
    srv.eval_catalog = FIXTURE["response"]
    client = client_for(srv)
    monkeypatch.setattr(client_module, "FutureAGIClient", lambda *a, **k: client)
    Path("agent.py").write_text(TASK)
    Path("run_eval.py").write_text(RUN_FILE)
    write_rows(Path("rows.jsonl"), ROWS)
    return srv


def _first_run(server):
    """The rows stored once by an ordinary run: a dataset named support-rows, its version and the local metric
    ``correct``."""
    if not server.runs:
        code, _, err = cli("run", "run_eval.py", "--dataset", "rows.jsonl", "--dataset-name", "support-rows",
                           "--no-trace", "--no-env-file", "--quiet")
        assert code == 0, err
        Path("calls.txt").unlink()
    return next(iter(server.runs.values()))


def _dataset_id(server):
    return next(d["id"] for d in server.datasets.values() if d["versions"])


def _app_run(server, recorded=2, evaluators=("contains",), experiment=True, header_dataset_id=False, **state):
    """A run made in the app, with the app's create body: a client v4 UUID, the version the first run stored, a plan
    of 5 trials, ``evaluator_metric_ids`` (a dataset metric per template name in ``evaluators``, ``"correct"`` for the
    first run's local metric, none for ``()``), the experiment, ``model_config`` {} and ``metadata``
    {"name": "Your code"}. ``recorded`` planned trials already have a result. ``state`` seeds the run's status, task
    kind or completion time."""
    first = _first_run(server)
    dataset_id = _dataset_id(server)
    metric_ids = []
    for name in evaluators:
        if name == "correct":
            metric_ids += first["body"]["evaluator_metric_ids"]
            continue
        metric_id = str(uuid.uuid4())
        # the app's mapping names the dataset's columns by id
        server.metrics[metric_id] = {"name": f"app-{name}", "dataset": dataset_id, "kind": "template",
                                     "template_id": TEMPLATES[name]["id"], "version": str(uuid.uuid4()),
                                     "config": {"mapping": {"text": str(uuid.uuid4())},
                                                "config": {"keyword": "shipped"} if name == "contains" else {}},
                                     "model": None}
        metric_ids.append(metric_id)
    experiment_id = None
    if experiment:
        experiment_id = str(uuid.uuid4())
        server.experiments[experiment_id] = {"name": "support replies", "dataset_id": dataset_id}
    run_id = str(uuid.uuid4())
    body = {"run_id": run_id, "dataset_version_id": first["body"]["dataset_version_id"],
            "expected_items": [{"example_id": e["example_id"], "trial_number": e["trial_number"]}
                               for e in first["body"]["expected_items"]],
            "evaluator_metric_ids": metric_ids, "experiment_id": experiment_id, "model_config": {},
            "metadata": {"name": "Your code"}}
    planned = [(e["example_id"], e["trial_number"]) for e in body["expected_items"]]
    items = {}
    for example_id, trial in planned[:recorded]:
        payload = {"example_id": example_id, "trial_number": trial, "receipt_key": f"app-{example_id}",
                   "status": "completed", "output": "shipped", "error": None, "trace_id": None,
                   "root_span_id": None, "latency_ms": 1.0, "token_usage": None, "cost": None, "score_refs": []}
        items[(example_id, trial)] = {**payload, "_payload": payload}
    server.runs[run_id] = {"body": body, "items": items, **({"header_dataset_id": True} if header_dataset_id else {}),
                           **state}
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


def _writes(server):
    return [p for m, p, _ in server.requests if m == "POST" and "/sdk/api/v1/" not in p]


def test_a_code_object_runs_only_the_missing_trials_of_a_run_made_in_the_app(server):
    run_id, planned = _app_run(server)
    assert server.runs[run_id]["body"]["model_config"] == {}  # the app sends no model configuration
    code, out, err = cli("run", "agent.py:run", *CODE, "--run", run_id)
    assert code == 0, err
    question_of = _question_of(server)
    assert _ran() == sorted(question_of[e] for e, _ in planned[2:])  # only the 3 trials with no result yet
    assert "2 of 5" in err and "running 3" in err
    assert server.count("POST", r"/model-hub/experiment-runs/") == 0  # no run was created
    assert set(_writes(server)) == {f"/model-hub/experiment-runs/{run_id}/results/"}  # no version, no metric
    assert server.count("GET", r"/model-hub/experiments/v2/[^/]+/") == 1  # the dataset came from the experiment
    stored = server.runs[run_id]["items"]
    assert set(stored) == set(planned)
    assert [stored[k]["receipt_key"] for k in planned[:2]] == [f"app-{e}" for e, _ in planned[:2]]  # untouched
    [metric_id] = server.runs[run_id]["body"]["evaluator_metric_ids"]
    pinned = server.metrics[metric_id]["version"]
    for key in planned[2:]:  # the run's own evaluator scored each new trial
        assert [(r["metric_id"], r["evaluator_version_id"], r["status"]) for r in stored[key]["score_refs"]] == [
            (metric_id, pinned, "assessed")]
    # the pinned template and its settings; its column mapping falls back to the task output
    assert [c["eval_name"] for c in server.eval_calls] == ["contains"] * 3
    assert all(c["inputs"] == {"text": "shipped"} and c["config"] == {"params": {"keyword": "shipped"}}
               for c in server.eval_calls)
    journal = load_journal(run_id)  # the same journal a normal run keeps
    assert sorted(journal.records) == sorted(planned[2:]) and all(r.acked for r in journal.records.values())


def test_the_dataset_comes_from_the_run_header_when_it_names_one(server):
    run_id, planned = _app_run(server, experiment=False, header_dataset_id=True)
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", run_id, "--quiet")
    assert code == 0, err
    assert len(_ran()) == 3
    assert server.count("GET", r"/model-hub/experiments/v2/[^/]+/") == 0
    assert set(server.runs[run_id]["items"]) == set(planned)


def test_a_run_that_names_no_dataset_asks_for_dataset(server):
    run_id, planned = _app_run(server, experiment=False)
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert run_id in line and "--dataset" in line
    assert _writes(server) == [] and _ran() == []
    code, _, err = cli("run", "agent.py:run", *CODE, "--dataset", "support-rows", "--run", run_id, "--quiet")
    assert code == 0, err
    assert len(_ran()) == 3 and set(server.runs[run_id]["items"]) == set(planned)


@pytest.mark.parametrize("by", ["name", "id"])
def test_a_dataset_given_with_run_is_accepted_when_it_is_the_runs(server, by):
    run_id, planned = _app_run(server)
    dataset = "support-rows" if by == "name" else _dataset_id(server)
    code, _, err = cli("run", "agent.py:run", *CODE, "--dataset", dataset, "--run", run_id, "--quiet")
    assert code == 0, err
    assert len(_ran()) == 3 and set(server.runs[run_id]["items"]) == set(planned)


def test_another_dataset_or_a_rows_file_is_refused(server):
    run_id, _ = _app_run(server)
    server.add_dataset("other tickets", ROWS)
    code, _, err = cli("run", "agent.py:run", *CODE, "--dataset", "other tickets", "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert "'other tickets'" in line and _dataset_id(server) in line
    code, _, err = cli("run", "agent.py:run", *CODE, "--dataset", "rows.jsonl", "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert "--run" in line and "--dataset" in line and "name or id" in line
    assert _writes(server) == [] and _ran() == []


def test_a_version_the_given_dataset_does_not_have_is_refused(server):
    run_id, _ = _app_run(server, experiment=False)
    server.add_dataset("other tickets", ROWS)
    code, _, err = cli("run", "agent.py:run", *CODE, "--dataset", "other tickets", "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert server.runs[run_id]["body"]["dataset_version_id"] in line and "'other tickets'" in line
    assert _writes(server) == [] and _ran() == []


def test_eval_that_names_the_runs_evaluators_is_accepted(server):
    run_id, planned = _app_run(server)
    code, _, err = cli("run", "agent.py:run", *CODE, "--eval", "contains", "--run", run_id, "--quiet")
    assert code == 0, err
    assert [c["eval_name"] for c in server.eval_calls] == ["contains"] * 3
    assert all(c["config"] == {"params": {"keyword": "shipped"}} for c in server.eval_calls)  # the run's settings
    [metric_id] = server.runs[run_id]["body"]["evaluator_metric_ids"]
    stored = server.runs[run_id]["items"]
    assert all([r["metric_id"] for r in stored[k]["score_refs"]] == [metric_id] for k in planned[2:])


def test_eval_that_differs_from_the_runs_evaluators_is_refused(server):
    run_id, _ = _app_run(server)
    code, _, err = cli("run", "agent.py:run", *CODE, "--eval", "is_json", "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert "--eval" in line and "is_json" in line and "contains" in line
    assert _writes(server) == [] and _ran() == [] and server.eval_calls == []


def test_a_run_with_no_evaluators_records_unscored_results(server):
    run_id, planned = _app_run(server, evaluators=())
    code, _, err = cli("run", "agent.py:run", *CODE, "--eval", "contains", "--run", run_id)
    assert code == 2  # --eval must name exactly the run's evaluators: it has none
    assert "contains" in _one_line(err)
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", run_id)
    assert code == 0, err
    assert "has no evaluators" in err and "unscored" in err
    stored = server.runs[run_id]["items"]
    assert set(stored) == set(planned) and all(stored[k]["score_refs"] == [] for k in planned[2:])
    assert server.eval_calls == [] and server.count("GET", r"/sdk/api/v1/get-evals/") == 0


def test_a_metric_scored_by_local_code_needs_the_run_file_that_declares_it(server):
    run_id, planned = _app_run(server, evaluators=("correct",))
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", run_id)
    assert code == 2  # a code object has no evaluator code
    line = _one_line(err)
    assert "correct" in line and run_id in line
    Path("more_eval.py").write_text(
        RUN_FILE.replace("[correct]", "[correct, short]").replace(
            "experiments.run(", "def short(output) -> bool:\n    return len(output) < 20\n\n\nexperiments.run("))
    code, _, err = cli("run", "more_eval.py", *CODE, "--run", run_id)
    assert code == 2  # the run file's evaluators must be exactly the run's
    line = _one_line(err)
    assert "short" in line and "evaluators" in line
    assert _writes(server) == [] and _ran() == []
    code, _, err = cli("run", "run_eval.py", *CODE, "--run", run_id, "--quiet")
    assert code == 0, err
    [metric_id] = server.runs[run_id]["body"]["evaluator_metric_ids"]
    stored = server.runs[run_id]["items"]
    assert all([r["metric_id"] for r in stored[k]["score_refs"]] == [metric_id] for k in planned[2:])


def test_recorded_items_are_listed_page_by_page_with_a_status_filter(server):
    run_id, planned = _app_run(server, recorded=3)
    server.items_page = 1  # the server answers one item per page
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", run_id, "--quiet")
    assert code == 0, err
    assert len(_ran()) == 2
    reads = [q for m, p, q in server.queries if m == "GET" and p == f"/model-hub/experiment-runs/{run_id}/items/"]
    assert len(reads) >= 3 and [int(q.get("offset", 0)) for q in reads[:3]] == [0, 1, 2]
    for q in reads:  # an item still pending or running belongs to someone else's trial
        assert {"pending", "running", "completed", "failed", "skipped"} <= set(q["status"].split(","))
        assert 1 <= int(q["limit"]) <= 500
    assert set(server.runs[run_id]["items"]) == set(planned)


def test_a_run_into_an_app_run_continues_with_resume(server, monkeypatch):
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    monkeypatch.setattr(_upload, "GIVE_UP_S", 0.0)
    run_id, planned = _app_run(server)
    argv = ["run", "agent.py:run", *CODE, "--run", run_id]
    monkeypatch.setattr(sys, "argv", ["futureagi-py", *argv])
    server.fail_ingest = [503]
    code, _, err = cli(*argv)
    assert code == 3, err
    line = shlex.split(err.split("send the rest with: ", 1)[1].strip())
    assert line[-2:] == ["--resume", run_id] and "--run" not in line and "--dataset" not in line
    assert len(server.runs[run_id]["items"]) == 2  # nothing of ours was stored
    Path("calls.txt").unlink()
    calls = len(server.eval_calls)
    monkeypatch.setattr(sys, "argv", line)
    code, _, err = cli(*line[1:])
    assert code == 0, err
    assert _ran() == [] and len(server.eval_calls) == calls  # every trial was journaled: nothing runs again
    assert set(server.runs[run_id]["items"]) == set(planned)
    assert server.count("POST", r"/model-hub/experiment-runs/") == 0


def test_a_run_journaled_here_is_continued_with_resume_not_run(server):
    run_id, _ = _app_run(server)
    assert cli("run", "agent.py:run", *CODE, "--run", run_id, "--quiet")[0] == 0
    server.requests.clear()
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", run_id)
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
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", run_id, *[run_id if f == "RUNID" else f for f in flags])
    assert code == 2
    line = _one_line(err)
    assert "--run" in line and named in line and "do not go together" in line
    assert server.requests == []  # refused before any request


def test_a_run_id_that_is_not_a_uuid_is_refused(server):
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", "run-42")
    assert code == 2
    line = _one_line(err)
    assert "--run" in line and "'run-42'" in line and "UUID" in line
    assert server.requests == []


def test_an_unknown_or_hidden_run_is_refused(server):
    _app_run(server)
    missing = str(uuid.uuid4())
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", missing)
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
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert run_id in line and word in line and "takes no more results" in line
    assert not [r for r in server.requests if r[0] == "POST"]  # nothing was written, not even a metric
    assert _ran() == []


def test_a_run_whose_task_runs_on_the_platform_is_refused(server):
    run_id, _ = _app_run(server, task_kind="prompt")
    code, _, err = cli("run", "agent.py:run", *CODE, "--run", run_id)
    assert code == 2
    line = _one_line(err)
    assert run_id in line and "prompt" in line
    assert not [r for r in server.requests if r[0] == "POST"]


def test_run_is_listed_in_help_all():
    code, out, _ = cli("run", "--help-all")
    assert code == 0
    rows = [line for line in out.splitlines() if line.strip().startswith("--run ")]
    assert len(rows) == 1 and "created elsewhere" in rows[0]
