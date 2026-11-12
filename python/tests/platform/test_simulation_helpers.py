"""client.simulation's hand-written wait helpers, against an in-process httpx MockTransport."""

from __future__ import annotations

import asyncio

import fi.platform as fp
import httpx
import pytest
from fi.platform.resources import simulation as sim

BASE = "http://backend.test"


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(sim.time, "sleep", lambda s: None)

    async def instant(_):
        return None

    monkeypatch.setattr(sim.asyncio, "sleep", instant)


def _ok(result):
    return httpx.Response(200, json={"status": True, "result": result})


def _scripted(routes):
    """routes: {path: [response, response, ...]}; the last response repeats. Records the paths."""
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        seen.append(path)
        queue = routes[path]
        return queue.pop(0) if len(queue) > 1 else queue[0]

    return handler, seen


def _client(handler):
    return fp.Client(api_key="k", secret_key="s", base_url=BASE, http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def _async_client(handler):
    return fp.AsyncClient(api_key="k", secret_key="s", base_url=BASE, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def _job(state, **extra):
    return {"job": {"job_id": "j1"}, "status": {"state": state}, **extra}


JOB = "/simulate/api/harness-jobs/j1/"


def test_wait_for_job_polls_until_a_terminal_state():
    handler, seen = _scripted({JOB: [_ok(_job("running")), _ok(_job("running")), _ok(_job("completed"))]})
    job = _client(handler).simulation.wait_for_job("j1")
    assert job["status"]["state"] == "completed"
    assert seen == [JOB] * 3


def test_wait_for_job_stops_at_an_open_question_but_not_an_answered_one():
    question = {"message_id": "q1", "prompt": "Docker or Python?"}
    asked = _job("running", conversation={"blocking_input": question, "messages": []})
    answered = _job("running", conversation={"blocking_input": question, "messages": [{"reply_to": "q1"}]})
    handler, seen = _scripted({JOB: [_ok(answered), _ok(asked)]})
    job = _client(handler).simulation.wait_for_job("j1")
    assert sim.open_question(job) == question
    assert len(seen) == 2  # the answered-but-unprocessed question did not stop the wait
    assert sim.open_question(answered) is None


def test_wait_for_job_times_out():
    handler, _ = _scripted({JOB: [_ok(_job("running"))]})
    with pytest.raises(TimeoutError, match="job j1"):
        _client(handler).simulation.wait_for_job("j1", timeout=0.01, poll_interval=0.01)
    with pytest.raises(ValueError):
        _client(handler).simulation.wait_for_job("j1", timeout=0)


def test_wait_for_run_waits_for_grading_after_the_job():
    te = "/simulate/test-executions/te1/"
    handler, seen = _scripted({
        JOB: [_ok(_job("completed"))],
        te: [httpx.Response(200, json={"status": "evaluating"}), httpx.Response(200, json={"status": "completed"})],
    })
    run = _client(handler).simulation.wait_for_run("j1", test_execution_id="te1")
    assert run["job"]["status"]["state"] == "completed" and run["execution_status"] == "completed"
    assert seen == [JOB, te, te]


def test_wait_for_run_does_not_wait_for_grading_of_a_failed_job():
    handler, seen = _scripted({JOB: [_ok(_job("failed"))]})
    run = _client(handler).simulation.wait_for_run("j1", test_execution_id="te1")
    assert run == {"job": _job("failed"), "execution_status": None}
    assert seen == [JOB]


def _versions(check):
    return _ok({"agent": [{"id": "v1", "status": "active", "preflight_status": "passed"}, {"id": "v2", "status": "draft", "preflight_status": check}], "environment": [], "suite": []})


VERSIONS = "/simulate/api/harness-environments/e1/versions/"


def test_wait_for_agent_version_polls_until_the_check_leaves_pending():
    handler, seen = _scripted({VERSIONS: [_versions("pending"), _versions("failed")]})
    version = _client(handler).simulation.wait_for_agent_version("e1", "v2")
    assert version.id == "v2" and version.preflight_status == "failed"
    assert len(seen) == 2


def test_wait_for_agent_version_fails_when_the_version_disappears():
    handler, _ = _scripted({VERSIONS: [_ok({"agent": [], "environment": [], "suite": []})]})
    with pytest.raises(LookupError, match="v2"):
        _client(handler).simulation.wait_for_agent_version("e1", "v2")


def test_wait_for_insights_polls_until_terminal():
    path = "/simulate/test-executions/te1/debug-analysis/"
    base = {"test_execution_id": "te1", "generation": 1, "job_id": None, "error_message": None, "report": None, "findings": [], "summary": None, "goals": [], "one_offs": []}
    handler, seen = _scripted({path: [_ok({**base, "status": "running"}), _ok({**base, "status": "completed"})]})
    analysis = _client(handler).simulation.wait_for_insights("te1")
    assert analysis.status == "completed" and len(seen) == 2


def test_async_helpers_match_the_sync_ones():
    te = "/simulate/test-executions/te1/"
    handler, seen = _scripted({
        JOB: [_ok(_job("running")), _ok(_job("completed"))],
        te: [httpx.Response(200, json={"status": "completed"})],
        VERSIONS: [_versions("pending"), _versions("passed")],
    })

    still_running, _ = _scripted({JOB: [_ok(_job("running"))]})

    async def go():
        client = _async_client(handler)
        run = await client.simulation.wait_for_run("j1", test_execution_id="te1")
        version = await client.simulation.wait_for_agent_version("e1", "v2")
        with pytest.raises(TimeoutError):
            await _async_client(still_running).simulation.wait_for_job("j1", timeout=0.01, poll_interval=0.01)
        return run, version

    run, version = asyncio.run(go())
    assert run["execution_status"] == "completed" and version.preflight_status == "passed"
