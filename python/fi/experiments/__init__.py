"""``fi.experiments``: run your task over a dataset, score it, and keep the evidence.

    from fi import experiments
    experiments.run("rows.jsonl", task, [correct], upload=False)

Five concepts: dataset, task, evaluator, run, trial. Names are loaded lazily (PEP 562), so
``import fi.experiments`` imports no framework and no OpenTelemetry.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence

if TYPE_CHECKING:  # pragma: no cover
    from fi.experiments._limits import Limits
    from fi.experiments.results import ExperimentResult

_LAZY = {
    "dataset": "fi.experiments._dataset",
    "failed": "fi.experiments._dataset",
    "new_since": "fi.experiments._dataset",
    "sample": "fi.experiments._dataset",
    "Row": "fi.experiments._dataset",
    "param": "fi.experiments._params",
    "Limits": "fi.experiments._limits",
    "EvalScore": "fi.experiments.results",
    "ExperimentResult": "fi.experiments.results",
    "TrialResult": "fi.experiments.results",
    "TaskContext": "fi.experiments._context",
    "evaluator": "fi.experiments.evaluators.functions",
    "from_column": "fi.experiments._engine",
    "log_results": "fi.experiments._log_results",
    "template": "fi.experiments.evaluators.hosted",
    "evaluators": "fi.experiments.evaluators",
    "errors": "fi.experiments.errors",
    "adapters": "fi.experiments.adapters",
}

__all__ = ["run", "arun", *_LAZY]


def run(
    dataset: Any,
    task: Any,
    evaluators: Sequence[Any] = (),
    *,
    trials: int = 1,
    concurrency: int = 4,
    limit: Optional[int] = None,
    timeout_s: Optional[float] = 300.0,
    max_cost_usd: Optional[float] = None,
    judge_model: Optional[str] = None,
    params: Optional[Mapping[str, Any]] = None,
    name: Optional[str] = None,
    upload: bool = True,
    rows: Any = None,
    version: Any = None,
    experiment: Any = None,
    description: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    project: Optional[str] = None,
    limits: "Optional[Limits]" = None,
    trace: Any = True,
    instrument: Any = "auto",
    resume: Any = None,
    client: Any = None,
    progress: bool = True,
    error_policy: str = "zero",
) -> "ExperimentResult":
    """Run ``task`` over every selected row of ``dataset`` ``trials`` times and score each trial.

    Everyday options: ``trials``, ``concurrency``, ``limit``, ``timeout_s``, ``max_cost_usd``,
    ``judge_model``, ``params``, ``name``, ``upload``. Works from scripts and from inside a running
    event loop (it drives a private loop on its own thread). Ctrl-C raises ``RunInterrupted`` after
    the journal is flushed.

    ``timeout_s``: seconds for the task's attempts in each trial, including user and transient
    retries and their delays (default 300; None disables this task limit). It does not bound
    evaluators or the whole run. Evaluators use their own limits, such as judge or provider
    request timeouts; an evaluator timeout produces an error score. An evaluator without its
    own bound may wait indefinitely: it does not extend or reuse the task's ``timeout_s``.
    When the runner handles a task timeout, it sets ``ctx.cancelled``, abandons the attempt and
    records a timeout. The concurrency slot is released without waiting for a synchronous task's
    thread to return. Threads ignoring this cooperative stop signal can exceed ``concurrency``;
    there is no forced kill. Work a task starts in the default executor can also occupy workers
    until it returns. Async cancellation can be delayed; an async task that suppresses cancellation
    can currently have its late result recorded instead of a timeout, without ``ctx.cancelled``
    being set. This is being fixed.

    ``trace``: True (the SDK exports each trial's spans, scrubbed), False, or your own
    ``TracerProvider``. With your provider, spans go out through your exporter; the SDK redacts what
    it writes on the trial root, not your spans (see ``fi/experiments/README.md``). A traceAI
    ``register()`` provider keeps its exporter, and a processor you add after the run is added
    beside it. With ``upload=True, trace=True``, a failed OTLP batch raises
    ``errors.TraceExportError`` after export shutdown (CLI exit 3, code ``TRACE_EXPORT_FAILED``),
    with one ``TraceExportWarning`` per run even when ``progress=False``. Promoting warnings to
    errors does not replace the typed error or an existing primary failure (including interruption).
    The error names the collector endpoint and HTTP status or request failure, without response
    bodies or secrets. For future runs without tracing, use ``trace=False`` (CLI ``--no-trace``).
    Items may already be stored; spans are not journaled, so resume cannot recover lost spans.
    This terminal-batch check does not cover batch-processor queue drops, HTTP 200 OTLP partial
    rejections, or a caller-owned provider's exporter; it is not a full-delivery guarantee.
    ``futureagi-py doctor`` checks the collector route with GET: HTTP 404 is a setup problem;
    transport exceptions are inconclusive ("could not check"). It does not verify POST export.

    ``error_policy``: how a failed trial (the task raised or timed out) counts in ``summary()``'s pass rates and
    means and in the gate (``assert_passing``, CLI ``--fail-under``): ``"zero"`` (the default) counts it as 0 and a
    fail in every evaluator's mean and pass rate; ``"exclude"`` leaves it out, with its count shown. An evaluator's
    error scores (it raised or hit its own timeout, a judge answer held no verdict, a provider refused the call)
    are shown and left out of its mean and pass rate under either policy, and count toward
    ``summary().error_rate``, which ``--max-error-rate``
    gates on. A gate fails for an evaluator with no scored rows. These are the product's names and what the product
    does with an errored try and a score error (``fi.experiments.results``). An uploaded run does not carry the
    policy: the server has no field for it today. Any other name is a ``UsageError``.

    ``project``: the project an uploaded run's traces are stored in, default ``"<dataset> ·
    experiments"``. It is an Observe project: there is no experiment-typed project. The run is
    joined to its traces by run id (``fi.experiment.run_id`` on every span, and each trial's
    ``trace_id`` on its result and on the stored item).
    """
    kwargs = dict(locals())
    from fi.experiments import _registry

    if _registry.collecting():
        return _registry.declare(kwargs)  # type: ignore[return-value]
    from fi.experiments._engine import Engine, RunConfig
    from fi.experiments._sync import run_coroutine_sync

    cfg = RunConfig(**kwargs)
    return run_coroutine_sync(lambda: Engine(cfg).execute())


async def arun(
    dataset: Any,
    task: Any,
    evaluators: Sequence[Any] = (),
    *,
    trials: int = 1,
    concurrency: int = 4,
    limit: Optional[int] = None,
    timeout_s: Optional[float] = 300.0,
    max_cost_usd: Optional[float] = None,
    judge_model: Optional[str] = None,
    params: Optional[Mapping[str, Any]] = None,
    name: Optional[str] = None,
    upload: bool = True,
    rows: Any = None,
    version: Any = None,
    experiment: Any = None,
    description: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    project: Optional[str] = None,
    limits: "Optional[Limits]" = None,
    trace: Any = True,
    instrument: Any = "auto",
    resume: Any = None,
    client: Any = None,
    progress: bool = True,
    error_policy: str = "zero",
) -> "ExperimentResult":
    """The async form of :func:`run`, for callers that are already in an event loop.

    It has the same task-only ``timeout_s`` and cooperative cancellation contract as :func:`run`:
    task attempts (including retries) share the bound in each trial; evaluators keep their own
    limits and their timeouts produce error scores. An unbounded evaluator does not borrow the
    task's timeout. When the runner handles a task timeout, it sets ``ctx.cancelled``, abandons
    the attempt and records a timeout. The concurrency slot is released without waiting for a
    synchronous task's thread to return; threads ignoring the cooperative stop signal can exceed
    ``concurrency``. There is no forced kill. Work a task starts in the default executor can also
    occupy workers until it returns. Async cancellation can be delayed; an async task that
    suppresses cancellation can currently have its late result recorded instead of a timeout,
    without ``ctx.cancelled`` being set. This is being fixed.

    In a run file that ``futureagi-py run`` loads, it declares the run (like :func:`run`) instead
    of executing it.
    """
    kwargs = dict(locals())
    from fi.experiments import _registry

    if _registry.collecting():
        return _registry.declare(kwargs)  # type: ignore[return-value]
    from fi.experiments._engine import Engine, RunConfig

    return await Engine(RunConfig(**kwargs)).execute()


def __getattr__(name: str) -> Any:
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module 'fi.experiments' has no attribute {name!r}")
    mod = importlib.import_module(module)
    value = mod if module.endswith("." + name) else getattr(mod, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY))
