"""``run_in_sandboxes`` / ``arun_in_sandboxes``: ``fi.experiments.run`` / ``arun`` with a sandbox task.

The engine keeps everything it already does (trials, concurrency, timeouts, journal, resume,
upload). Around it: the workspace's limits read once before the first trial, the engine's
``concurrency`` clamped to the sandboxes allowed at once, a task ``timeout_s`` long enough for the
agent and the verifier unless you give one, and a sweep in ``finally`` that deletes any sandbox of
this batch still there (one stderr line each). ``Sandboxes`` is where the sandboxes come from: the
environment, or a factory that builds the client inside the running loop (never one client shared
across loops: ``run()`` drives a private loop on its own thread).
"""

from __future__ import annotations

import inspect
import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from fi.experiments.sandbox._spec import SandboxEval

if TYPE_CHECKING:  # pragma: no cover
    from fi.experiments.results import ExperimentResult

#: Seconds on top of the agent, verifier and quota-wait bounds: create, setup, reward read, delete.
SLACK_S = 120
Closer = Optional[Callable[[], Any]]


async def quietly(*closers: Closer) -> None:
    for close in closers:
        try:
            if close is not None:
                await close()
        except Exception:
            pass


class Sandboxes:
    """Where sandboxes come from: the environment (``AsyncSandbox``), or the caller's factory, called
    inside the running loop, returning an ``AsyncFutureAGIClient`` (closed after use) or its
    ``.sandboxes``."""

    def __init__(self, factory: Optional[Callable[[], Any]]) -> None:
        self.factory = factory

    async def _open(self) -> Tuple[Any, Closer]:
        made = self.factory()  # type: ignore[misc]
        made = await made if inspect.isawaitable(made) else made
        api = getattr(made, "sandboxes", made)
        return api, (getattr(made, "aclose", None) if api is not made else None)

    @asynccontextmanager
    async def _api(self) -> AsyncIterator[Any]:
        api, close = await self._open()
        try:
            yield api
        finally:
            if close is not None:
                await close()

    async def create(self, body: Dict[str, Any]) -> Tuple[Any, Closer]:
        from fi.sandbox import AsyncSandbox

        if self.factory is None:
            return await AsyncSandbox.create(**body), None
        api, close = await self._open()
        try:
            return await api.create(body=body), close
        except BaseException:
            await quietly(close)
            raise

    async def settings(self) -> Any:
        from fi.sandbox import AsyncSandbox

        if self.factory is None:
            return await AsyncSandbox.settings()
        async with self._api() as api:
            return await api.settings.get()

    async def listed(self) -> Tuple[List[Any], Closer]:
        """Handles on the workspace's sandboxes, and what closes the factory's client after them."""
        from fi.sandbox import AsyncSandbox

        if self.factory is None:
            return list((await AsyncSandbox.list()).sandboxes), None
        api, close = await self._open()
        try:
            raw = await api.list()
        except BaseException:
            await quietly(close)
            raise
        return [AsyncSandbox(api, record) for record in raw.get("sandboxes", [])], close


def derived_timeout_s(spec: SandboxEval, quota_wait_s: float) -> float:
    """The task ``timeout_s`` used unless the caller gives one."""
    return float(spec.agent_timeout_s + spec.verifier_timeout_s + quota_wait_s + SLACK_S)


def engine_kwargs(spec: SandboxEval, max_active: Optional[int], quota_wait_s: float,
                  run_kwargs: Mapping[str, Any]) -> Dict[str, Any]:
    """``run_kwargs`` with ``concurrency`` clamped to ``max_active`` and ``timeout_s`` derived."""
    kwargs = dict(run_kwargs)
    if max_active is not None:
        kwargs["concurrency"] = max(1, min(int(kwargs.get("concurrency", 4)), int(max_active)))
    if "timeout_s" not in kwargs:
        kwargs["timeout_s"] = derived_timeout_s(spec, quota_wait_s)
    return kwargs


def _left_note(task: Any, exc: BaseException) -> None:
    from fi.experiments.sandbox._spec import describe

    print(f"fi.experiments.sandbox: could not look for leftover sandboxes of batch {task.batch_id}: "
          f"{describe(exc)}", file=sys.stderr)


def _declared_note(task: Any) -> None:
    """A run file read by ``futureagi-py run``: the CLI runs the declared run itself, so nothing here
    sweeps after it. One stderr line names the batch, so its leftovers can be deleted afterwards."""
    print(f"fi.experiments.sandbox: batch {task.batch_id} is declared for `futureagi-py run`, which does not "
          f"delete leftover sandboxes after the run; to delete them, run "
          f"asyncio.run(sandbox_task(spec, batch_id={task.batch_id!r}).sweep())", file=sys.stderr)


def run_in_sandboxes(dataset: Any, spec: SandboxEval, evaluators: Sequence[Any] = (), *,
                     max_active: Optional[int] = None, quota_wait_s: float = 120.0,
                     client_factory: Optional[Callable[[], Any]] = None,
                     **run_kwargs: Any) -> "ExperimentResult":
    """``fi.experiments.run(dataset, sandbox_task(spec), evaluators, **run_kwargs)``: one sandbox per
    (row, trial), every one deleted, even on a failure or Ctrl-C.

    ``run_kwargs`` is any ``run`` argument (``trials``, ``concurrency``, ``limit``, ``name``,
    ``upload``, ``experiment``, ``project``, ``trace``...). ``concurrency`` is lowered to the
    sandboxes allowed at once; ``timeout_s`` defaults to ``agent_timeout_s + verifier_timeout_s +
    quota_wait_s + 120``. In a run file that ``futureagi-py run`` loads, the run is declared and the
    CLI runs it: no sweep follows it and ``concurrency`` is lowered only to a ``max_active`` you give
    (see the README, section 6)."""
    from fi import experiments
    from fi.experiments import _registry
    from fi.experiments._sync import run_coroutine_sync
    from fi.experiments.sandbox._task import sandbox_task

    task = sandbox_task(spec, max_active=max_active, quota_wait_s=quota_wait_s, client_factory=client_factory)
    if _registry.collecting():  # a run file read by the CLI: declare it, run nothing here, no sweep
        _declared_note(task)
        return experiments.run(dataset, task, evaluators, **engine_kwargs(spec, max_active, quota_wait_s, run_kwargs))
    allowed, _ = run_coroutine_sync(task.batch.limits)
    try:
        return experiments.run(dataset, task, evaluators, **engine_kwargs(spec, allowed, quota_wait_s, run_kwargs))
    finally:
        try:
            run_coroutine_sync(task.sweep)
        except Exception as exc:  # never hides the run's own result or error
            _left_note(task, exc)


async def arun_in_sandboxes(dataset: Any, spec: SandboxEval, evaluators: Sequence[Any] = (), *,
                            max_active: Optional[int] = None, quota_wait_s: float = 120.0,
                            client_factory: Optional[Callable[[], Any]] = None,
                            **run_kwargs: Any) -> "ExperimentResult":
    """The async form of :func:`run_in_sandboxes` (``fi.experiments.arun``)."""
    from fi import experiments
    from fi.experiments import _registry
    from fi.experiments.sandbox._task import sandbox_task

    task = sandbox_task(spec, max_active=max_active, quota_wait_s=quota_wait_s, client_factory=client_factory)
    if _registry.collecting():
        _declared_note(task)
        return await experiments.arun(dataset, task, evaluators,
                                      **engine_kwargs(spec, max_active, quota_wait_s, run_kwargs))
    allowed, _ = await task.batch.limits()
    try:
        return await experiments.arun(dataset, task, evaluators,
                                      **engine_kwargs(spec, allowed, quota_wait_s, run_kwargs))
    finally:
        try:
            await task.sweep()
        except Exception as exc:
            _left_note(task, exc)


def reward(key: str = "reward", *, passing_score: Optional[float] = 1.0) -> Callable[..., Any]:
    """A local evaluator named ``key`` that scores ``output["rewards"][key]`` (the reward file's
    value, or 1.0 / 0.0 from the verifier's exit). A trial with no such reward gets an error score."""
    from fi.experiments.errors import UsageError
    from fi.experiments.evaluators.functions import evaluator

    if not isinstance(key, str) or not key:
        raise UsageError("reward() takes the reward's name, a non-empty string")

    def score(output: Any) -> float:
        rewards = output.get("rewards") if isinstance(output, Mapping) else None
        if not isinstance(rewards, Mapping) or key not in rewards:
            have = sorted(rewards) if isinstance(rewards, Mapping) else []
            raise KeyError(f"the trial's output has no reward {key!r} (it has {have})")
        return float(rewards[key])

    score.__name__ = score.__qualname__ = f"reward_{key}"
    return evaluator(score, name=key, passing_score=passing_score)


__all__ = ["run_in_sandboxes", "arun_in_sandboxes", "reward", "derived_timeout_s", "engine_kwargs"]
