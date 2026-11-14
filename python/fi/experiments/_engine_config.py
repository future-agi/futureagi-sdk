"""Run configuration and the helpers that need no event loop: ``RunConfig``, the default run name,
git metadata, ``from_column`` and turning ``evaluators=`` arguments into evaluators.

Split out of ``_engine.py`` (the 400-line module rule); ``_engine`` re-exports these names.
"""

from __future__ import annotations

import datetime as _dt
import inspect
import json
import subprocess
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from fi.experiments._dataset import Row
from fi.experiments._limits import Limits
from fi.experiments._plan import to_jsonable
from fi.experiments.adapters import TaskRunner
from fi.experiments.adapters.callable import FactoryRunner
from fi.experiments.errors import UsageError
from fi.experiments.evaluators._base import Evaluator, unique_names


# ---- configuration -----------------------------------------------------------------------------


@dataclass
class RunConfig:
    dataset: Any
    task: Any
    evaluators: Sequence[Any] = ()
    trials: int = 1
    concurrency: int = 4
    limit: Optional[int] = None
    timeout_s: Optional[float] = 300.0
    max_cost_usd: Optional[float] = None
    judge_model: Optional[str] = None
    params: Optional[Mapping[str, Any]] = None
    name: Optional[str] = None
    upload: bool = True
    rows: Any = None
    version: Any = None
    experiment: Any = None
    description: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None
    project: Optional[str] = None
    limits: Optional[Limits] = None
    trace: Any = True
    instrument: Any = "auto"
    resume: Any = None
    attach: Any = None  # CLI --run: the id of a run created elsewhere that this run adds its results to
    client: Any = None
    progress: bool = True
    error_policy: str = "zero"  # how a failed trial counts in summary() and the gate (results.py)
    # CLI context
    argv: Optional[list[str]] = None
    resume_label: Optional[str] = None  # the declared run's name when a run file declares several
    # several declared runs selected: this one's run file, the --filter that selects it alone (None when none can)
    # and the dataset name to suggest; the dataset-name refusal shows a fix for this run only
    declared: Optional[Mapping[str, Any]] = None
    journal_root: Any = None
    stream: Any = None

    def name_fix(self) -> dict[str, Any]:
        """``check_local_name``'s context: the CLI argv, the declared run (CLI file mode, several runs) and whether
        the task always stores (log_results, whose name refusal offers no upload=False)."""
        d = self.declared or {}
        return {"argv": self.argv, "run_file": d.get("run_file"), "run_filter": d.get("run_filter"),
                "suggest": d.get("suggest"), "stores_always": bool(getattr(self.task, "stores_always", False))}

    def validate(self) -> None:
        if int(self.trials) < 1:
            raise UsageError("trials must be >= 1")
        if int(self.concurrency) < 1:
            raise UsageError("concurrency must be >= 1")
        if self.timeout_s is not None and self.timeout_s <= 0:
            raise UsageError("timeout_s must be > 0 (or None for no limit)")
        if self.max_cost_usd is not None and self.max_cost_usd <= 0:
            raise UsageError("max_cost_usd must be > 0")
        if self.attach is not None:
            from fi.experiments._attach import check_flags

            check_flags(self)
        if self.experiment is not None and not self.upload:
            raise UsageError(
                "experiment= (CLI --experiment) attaches the stored run to an experiment, and upload=False "
                "(CLI --no-upload) stores no run. Drop one of them."
            )
        if self.limits is not None and not isinstance(self.limits, Limits):
            raise UsageError("limits= takes experiments.Limits(...)")
        from fi.experiments.results import check_error_policy

        check_error_policy(self.error_policy)


# ---- helpers -----------------------------------------------------------------------------------


def _git_metadata() -> dict[str, Any]:
    def git(*args: str) -> Optional[str]:
        try:
            out = subprocess.run(["git", *args], capture_output=True, text=True, timeout=3)
        except (OSError, subprocess.SubprocessError):
            return None
        return out.stdout.strip() if out.returncode == 0 else None

    sha = git("rev-parse", "HEAD")
    if not sha:
        return {}
    return {
        "git_sha": sha,
        "git_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")),
    }


def _task_label(task: Any, runner: TaskRunner) -> str:
    if isinstance(runner, FactoryRunner):
        return getattr(runner.factory, "__name__", "factory")
    for attr in ("name", "__name__"):
        value = getattr(task, attr, None)
        if isinstance(value, str) and value and value != "<lambda>":
            return value
    return type(task).__name__ if not callable(task) or inspect.isclass(type(task)) else "task"


def default_run_name(task_label: str, params: Mapping[str, Any], framework: str) -> str:
    model = params.get("model") if params else None
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{task_label} · {model or framework} · {stamp}"


def _text(value: Any) -> str:
    return value if isinstance(value, str) else json.dumps(to_jsonable(value), ensure_ascii=False)


class FromColumn:
    """``experiments.from_column("answer")``: score a column that already holds the outputs."""

    def __init__(self, column: str) -> None:
        self.column = column
        self.__name__ = f"from_column:{column}"

    def __call__(self, row: Row) -> Any:
        if self.column not in row:
            raise KeyError(f"row {row.id} has no column {self.column!r}")
        return row[self.column]


def from_column(column: str) -> FromColumn:
    """Score-only: the task output is this column's value (no task runs)."""
    return FromColumn(column)


def resolve_evaluators(evaluators: Sequence[Any], judge_model: Optional[str]) -> list[Evaluator]:
    from fi.experiments.evaluators.functions import FunctionEvaluator

    out: list[Evaluator] = []
    for ev in evaluators or ():
        if isinstance(ev, Evaluator):
            out.append(ev)
        elif isinstance(ev, str) or type(ev).__name__ == "Template":
            try:
                from fi.experiments.evaluators.hosted import as_template_evaluator
            except ImportError:
                raise UsageError(
                    f"platform templates by name ({ev!r}) run through the hosted eval API, which this "
                    "build does not include yet; use a local function, tool_called/tool_order or judge()"
                ) from None
            out.append(as_template_evaluator(ev, judge_model=judge_model))
        elif callable(ev):
            out.append(FunctionEvaluator(ev))
        else:
            raise UsageError(f"{ev!r} is not an evaluator (a template name, a function or experiments.evaluators.*)")
    unique_names(out)
    return out
