"""Hand-written additions to `client.simulation`.

Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
regeneration. The generated methods live in `fi.platform.resources.base`.

The wait helpers poll the generated read methods the way the futureagi CLI's `--wait`
does (`fi sim run`, `fi sim env status`, `fi agents push`, `fi sim runs insights`), so a
script gets the same notion of "finished":

    job = client.simulation.environments.run(env_id, scenario_ids=["1", "2"])
    run = client.simulation.wait_for_run(job.job_id, test_execution_id=job.test_execution_id)

Each returns the last thing it read; none of them treats a failed outcome as an error (read
`status.state` or the returned status). A wait that runs out of time raises `TimeoutError`.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, Optional

from .base import AsyncSimulationResource, SimulationResource

# The same terminal states as the CLI (internal/cli/sim_runs_status.go, sim_runs_insights.go).
JOB_TERMINAL = frozenset({"completed", "failed", "canceled"})
EXECUTION_TERMINAL = frozenset({"completed", "failed", "cancelled"})
INSIGHTS_TERMINAL = frozenset({"completed", "failed", "not_requested"})


def _get(obj: Any, dotted: str) -> Any:
    for key in dotted.split("."):
        if obj is None:
            return None
        obj = obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)
    return obj


def open_question(job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The builder's unanswered question on a job (`conversation.blocking_input`), or None.

    A question already answered by a message the builder has not processed yet counts as
    answered. Reply with `client.simulation.jobs.send_message(job_id, content=...,
    kind="user_response", reply_to=question["message_id"], client_request_id=...)`."""
    question = _get(job, "conversation.blocking_input")
    if not isinstance(question, dict):
        return None
    for message in _get(job, "conversation.messages") or []:
        if isinstance(message, dict) and message.get("reply_to") and message.get("reply_to") == question.get("message_id"):
            return None
    return question


def _job_settled(job: Dict[str, Any]) -> bool:
    return _get(job, "status.state") in JOB_TERMINAL or open_question(job) is not None


def _agent_version(versions: Any, version_id: str) -> Any:
    for version in _get(versions, "agent") or []:
        if _get(version, "id") == version_id:
            return version
    raise LookupError(f"agent version {version_id} is no longer listed for this environment")


def _check(timeout: float, poll_interval: float) -> None:
    if timeout <= 0 or poll_interval <= 0:
        raise ValueError("timeout and poll_interval must be positive")


def _poll(read: Callable[[], Any], done: Callable[[Any], bool], what: str, timeout: float, poll_interval: float) -> Any:
    _check(timeout, poll_interval)
    deadline = time.monotonic() + timeout
    while True:
        value = read()
        if done(value):
            return value
        if time.monotonic() + poll_interval > deadline:
            raise TimeoutError(f"{what} did not finish within {timeout:g}s")
        time.sleep(poll_interval)


async def _apoll(read: Callable[[], Any], done: Callable[[Any], bool], what: str, timeout: float, poll_interval: float) -> Any:
    _check(timeout, poll_interval)
    deadline = time.monotonic() + timeout
    while True:
        value = await read()
        if done(value):
            return value
        if time.monotonic() + poll_interval > deadline:
            raise TimeoutError(f"{what} did not finish within {timeout:g}s")
        await asyncio.sleep(poll_interval)


class Simulation(SimulationResource):
    """`client.simulation`: every generated `simulation.*` method, plus the hand-written additions in this module."""

    def wait_for_job(self, job_id: str, *, timeout: float = 3600, poll_interval: float = 5) -> Dict[str, Any]:
        """Poll a harness job (an environment build, or a run's job) until it is completed, failed
        or canceled, or until the builder asks a question (see `open_question`). Returns the job."""
        return _poll(lambda: self.jobs.get(job_id), _job_settled, f"job {job_id}", timeout, poll_interval)

    def wait_for_run(self, job_id: str, *, test_execution_id: Optional[str] = None, timeout: float = 3600, poll_interval: float = 5) -> Dict[str, Any]:
        """Wait for a run started with `environments.run`: its job settles, then (when
        `test_execution_id` is given, as `environments.run` returns it) its test execution, whose
        grading can outlast the job. Returns `{"job": ..., "execution_status": ...}`."""
        deadline = time.monotonic() + timeout
        job = self.wait_for_job(job_id, timeout=timeout, poll_interval=poll_interval)
        status = None
        if test_execution_id and _get(job, "status.state") == "completed":
            left = max(deadline - time.monotonic(), poll_interval)
            status = _poll(
                lambda: _get(self._t.raw("GET", f"/simulate/test-executions/{test_execution_id}/", query={"limit": 1}), "status"),
                lambda s: s in EXECUTION_TERMINAL,
                f"test execution {test_execution_id}",
                left,
                poll_interval,
            )
        return {"job": job, "execution_status": status}

    def wait_for_agent_version(self, environment_id: str, version_id: str, *, timeout: float = 3600, poll_interval: float = 5) -> Any:
        """Poll an environment's agent version until its connection check leaves `pending`
        (`preflight_status`), after `versions.create_agent`, `versions.retry_agent` or
        `jobs.set_secret_values`. Returns the version."""
        return _poll(
            lambda: _agent_version(self.environments.versions.list(environment_id), version_id),
            lambda v: _get(v, "preflight_status") != "pending",
            f"agent version {version_id}",
            timeout,
            poll_interval,
        )

    def wait_for_insights(self, test_execution_id: str, *, timeout: float = 1800, poll_interval: float = 5) -> Any:
        """Poll a run's Insights (after `executions.insights.start`) until completed or failed."""
        return _poll(
            lambda: self.executions.insights.get(test_execution_id),
            lambda a: _get(a, "status") in INSIGHTS_TERMINAL,
            f"insights of {test_execution_id}",
            timeout,
            poll_interval,
        )


class AsyncSimulation(AsyncSimulationResource):
    """`client.simulation` for `AsyncClient`: the same methods as `Simulation`, awaited."""

    async def wait_for_job(self, job_id: str, *, timeout: float = 3600, poll_interval: float = 5) -> Dict[str, Any]:
        """See `Simulation.wait_for_job`."""
        return await _apoll(lambda: self.jobs.get(job_id), _job_settled, f"job {job_id}", timeout, poll_interval)

    async def wait_for_run(self, job_id: str, *, test_execution_id: Optional[str] = None, timeout: float = 3600, poll_interval: float = 5) -> Dict[str, Any]:
        """See `Simulation.wait_for_run`."""
        deadline = time.monotonic() + timeout
        job = await self.wait_for_job(job_id, timeout=timeout, poll_interval=poll_interval)
        status = None
        if test_execution_id and _get(job, "status.state") == "completed":

            async def read() -> Any:
                return _get(await self._t.raw("GET", f"/simulate/test-executions/{test_execution_id}/", query={"limit": 1}), "status")

            status = await _apoll(read, lambda s: s in EXECUTION_TERMINAL, f"test execution {test_execution_id}", max(deadline - time.monotonic(), poll_interval), poll_interval)
        return {"job": job, "execution_status": status}

    async def wait_for_agent_version(self, environment_id: str, version_id: str, *, timeout: float = 3600, poll_interval: float = 5) -> Any:
        """See `Simulation.wait_for_agent_version`."""

        async def read() -> Any:
            return _agent_version(await self.environments.versions.list(environment_id), version_id)

        return await _apoll(read, lambda v: _get(v, "preflight_status") != "pending", f"agent version {version_id}", timeout, poll_interval)

    async def wait_for_insights(self, test_execution_id: str, *, timeout: float = 1800, poll_interval: float = 5) -> Any:
        """See `Simulation.wait_for_insights`."""
        return await _apoll(lambda: self.executions.insights.get(test_execution_id), lambda a: _get(a, "status") in INSIGHTS_TERMINAL, f"insights of {test_execution_id}", timeout, poll_interval)
