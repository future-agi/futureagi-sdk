"""``run_in_sandboxes``: the sandbox task inside the real engine (``upload=False``), over the mock
sandbox server of ``test_sandbox_task``. Fake credentials only."""

from __future__ import annotations

import json

import pytest

from fi import experiments
from fi.experiments.sandbox import SandboxEval, reward, run_in_sandboxes
from fi.experiments.sandbox._runner import derived_timeout_s
from tests.experiments.unit.test_sandbox_task import bodies, exec_answer, exit_frame, names, settings_answer
from tests.experiments.unit.test_sandbox_task import sandbox_env_fixture  # noqa: F401 (the fixture)

ROWS = [{"id": "r1", "q": 1}, {"id": "r2", "q": 2}, {"id": "r3", "q": 3}]
SPEC = SandboxEval(agent_command=lambda row: f"python3 solve.py {row['q']}",
                   verifier=lambda row: f"bash test.sh {row['q']}")


def _fails_on_two(body):
    return [exit_frame(1 if body["command"] == "bash test.sh 2" else 0)]


def test_three_rows_two_trials_six_outputs_six_deletes(sandbox_env):
    result = run_in_sandboxes(ROWS, SPEC, trials=2, upload=False, trace=False, progress=False)
    assert len(result.items) == 6 and all(item.status == "completed" for item in result.items)
    assert all(item.output["deleted"] is True for item in result.items)
    seen = names(sandbox_env)
    assert seen.count("sandboxes.create") == 6 and seen.count("sandboxes.kill") == 6
    assert len({body["name"] for body in bodies(sandbox_env, "sandboxes.create")}) == 6
    assert seen.count("sandboxes.settings.get") == 1  # read once, before the first trial
    assert seen[-1] == "sandboxes.list"  # the sweep, after the run


def test_concurrency_clamped_and_timeout_derived(sandbox_env, monkeypatch):
    calls = []
    monkeypatch.setattr(experiments, "run", lambda dataset, task, evaluators, **kw: calls.append(kw) or "done")
    sandbox_env.on("sandboxes.settings.get", settings_answer(sandbox_env, max_active=3))
    assert run_in_sandboxes(ROWS, SPEC, concurrency=10, upload=False) == "done"
    assert calls[-1]["concurrency"] == 3 and calls[-1]["timeout_s"] == 900 + 300 + 120 + 120
    assert derived_timeout_s(SPEC, 0) == 1320.0
    run_in_sandboxes(ROWS, SPEC, max_active=1, quota_wait_s=0, timeout_s=50, upload=False)
    assert calls[-1]["concurrency"] == 1 and calls[-1]["timeout_s"] == 50
    run_in_sandboxes(ROWS, SPEC, upload=False)
    assert calls[-1]["concurrency"] == 3  # the engine's default 4, lowered to the cap
    assert names(sandbox_env).count("sandboxes.list") == 3  # a sweep after every run


def test_reward_evaluator_scores(sandbox_env):
    sandbox_env.on("sandboxes.commands.run", exec_answer(_fails_on_two))
    result = run_in_sandboxes(ROWS, SPEC, [reward()], upload=False, trace=False, progress=False)
    by_row = {item.example_id: item.scores["reward"] for item in result.items}
    assert {k: (v.value, v.passed) for k, v in by_row.items()} == {
        "r1": (1.0, True), "r2": (0.0, False), "r3": (1.0, True)}
    missing = run_in_sandboxes(ROWS[:1], SPEC, [reward("style")], upload=False, trace=False, progress=False)
    assert missing.items[0].scores["style"].status == "error"


def test_client_factory_builds_each_client_in_the_loop_and_closes_it(sandbox_env, monkeypatch):
    from tests.platform._sandbox_mock import api

    monkeypatch.delenv("OMEGA_BASE_URL")  # nothing comes from the environment
    monkeypatch.delenv("FUTUREAGI_OMEGA_API_KEY")
    made, closed = [], []

    class Client:  # the part of AsyncFutureAGIClient used here: .sandboxes and aclose()
        def __init__(self):
            self.sandboxes = api(sandbox_env, "async", auth="bearer")
            made.append(self)

        async def aclose(self):
            closed.append(self)

    spec = SandboxEval(agent_command="true", template="python-data")
    result = run_in_sandboxes(ROWS[:2], spec, client_factory=Client, upload=False, trace=False, progress=False)
    assert [item.output["deleted"] for item in result.items] == [True, True]
    created = bodies(sandbox_env, "sandboxes.create")
    assert len(created) == 2 and all(b["template"] == "python-data" and b["name"].startswith("fi-eval-")
                                     for b in created)
    seen = names(sandbox_env)
    assert seen.count("sandboxes.settings.get") == 1 and seen.count("sandboxes.kill") == 2
    assert seen[-1] == "sandboxes.list"  # the sweep, through the factory
    assert len(made) == 4 and sorted(map(id, closed)) == sorted(map(id, made))  # settings, 2 creates, sweep

    sandbox_env.seen.clear()
    calls = []

    async def handles():  # an async factory that returns client.sandboxes: nothing to close
        calls.append(1)
        return api(sandbox_env, "async", auth="bearer")

    result = run_in_sandboxes(ROWS[:1], spec, client_factory=handles, upload=False, trace=False, progress=False)
    assert result.items[0].output["deleted"] is True and len(calls) == 3
    assert names(sandbox_env).count("sandboxes.create") == 1 and names(sandbox_env)[-1] == "sandboxes.list"


def test_run_file_declares_without_requests_and_names_the_batch(sandbox_env, capsys):
    from fi.experiments import _registry

    with _registry.collect() as bucket:
        declared = run_in_sandboxes(ROWS, SPEC, max_active=2, concurrency=8, upload=False)
    assert len(bucket) == 1 and declared is bucket[0]
    assert bucket[0].kwargs["concurrency"] == 2
    batch = bucket[0].kwargs["task"].batch_id
    err = capsys.readouterr().err
    assert batch in err and ".sweep()" in err and sandbox_env.seen == []


def test_phase_spans_under_trial_root(sandbox_env):
    pytest.importorskip("opentelemetry.sdk")
    captured = []

    @experiments.evaluator(name="spans")
    def spans(trace):
        captured.extend(trace or [])
        return 1.0

    result = run_in_sandboxes(ROWS[:1], SPEC, [spans], upload=False, trace=True, progress=False)
    item = result.items[0]
    phases = {span["name"]: span for span in captured if span["name"].startswith("sandbox.")}
    assert set(phases) == {"sandbox.create", "sandbox.setup", "sandbox.agent", "sandbox.verify", "sandbox.delete"}
    assert all(span["parent_id"] == item.root_span_id and span["trace_id"] == item.trace_id
               for span in phases.values())
    agent_env = bodies(sandbox_env, "sandboxes.commands.run")[0]["env"]
    assert agent_env["TRACEPARENT"].split("-")[1:3] == [item.trace_id, phases["sandbox.agent"]["span_id"]]
    assert json.dumps(item.output).count("TRACEPARENT") == 0
