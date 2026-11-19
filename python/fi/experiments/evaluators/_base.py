"""The evaluator protocol the engine drives, and score normalization."""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence

from fi.experiments.results import EvalScore

ARGUMENT_NAMES = ("row", "input", "output", "expected", "metadata", "trace", "state", "ctx")


@dataclass
class EvalContext:
    row: Any
    output: Any
    ctx: Any = None
    trace: Optional[list[Any]] = None  # captured spans; None when the trial captured none
    state: Any = None  # the Environment end state (a later release)
    tool_spans_expected: bool = False  # a framework instrumentor that emits tool spans is on
    instrument_hint: str = "traceAI-langchain"
    # (model, input tokens, output tokens) for each model call an evaluator made (judge());
    # the engine counts them toward max_cost_usd
    usage: list[tuple[str, int, int]] = field(default_factory=list)
    # start(name, attributes) -> a started span, child of the trial's root span (judge()'s own span);
    # None when the trial is not traced
    start_span: Optional[Callable[[str, Mapping[str, Any]], Any]] = None
    # price(model, input tokens, output tokens) -> dollars, or None when the run has no price for it
    price: Optional[Callable[[str, int, int], Optional[float]]] = None
    # a score-only run (``from_column(col)``): the column that IS the output. It is never part of ``input``,
    # so a judge is not shown the OUTPUT inside the INPUT (F8: it then compared the output with itself)
    output_column: Optional[str] = None

    @property
    def input(self) -> Any:
        inputs = getattr(self.row, "inputs", None)
        if isinstance(inputs, dict) and self.output_column in inputs:
            inputs = {k: v for k, v in inputs.items() if k != self.output_column}
        if isinstance(inputs, dict) and len(inputs) == 1:
            return next(iter(inputs.values()))
        return inputs

    @property
    def expected(self) -> Any:
        return getattr(self.row, "expected", None)

    @property
    def metadata(self) -> dict[str, Any]:
        return dict(getattr(self.row, "metadata", {}) or {})

    def argument(self, name: str) -> Any:
        return getattr(self, name)


class Evaluator:
    """Base class: ``names`` are fixed before the run (metrics are pinned when it is created)."""

    names: tuple[str, ...] = ()
    kind: str = "local"  # "local" | "trace" | "judge" | "template"
    is_async: bool = False
    passing_score: Optional[float] = None

    def evaluate(self, ec: EvalContext) -> Mapping[str, EvalScore]:  # sync evaluators
        raise NotImplementedError

    async def aevaluate(self, ec: EvalContext) -> Mapping[str, EvalScore]:  # async evaluators
        raise NotImplementedError

    def describe(self) -> str:
        return ", ".join(self.names)


def error_score(exc: BaseException) -> EvalScore:
    tb = "".join(traceback.format_exception_only(type(exc), exc)).strip()
    return EvalScore(status="error", explanation=tb[:2000])


def to_score(value: Any, passing_score: Optional[float] = None) -> EvalScore:
    """bool, number, None, EvalScore → EvalScore (dicts are handled by the caller)."""
    if isinstance(value, EvalScore):
        score = value
    elif value is None:
        return EvalScore(status="skipped", explanation="the evaluator returned None")
    elif isinstance(value, bool):
        return EvalScore(value)
    elif isinstance(value, (int, float)):
        score = EvalScore(float(value))
    else:
        num = getattr(value, "item", None)  # numpy scalars
        if callable(num):
            return to_score(num(), passing_score)
        raise TypeError(
            f"an evaluator returned {type(value).__name__}; return a bool, a number, None, "
            "an EvalScore or a dict of declared names"
        )
    if score.passed is None and passing_score is not None and score.value is not None and score.status == "assessed":
        score = score.model_copy(update={"passed": score.value >= passing_score})
    return score


def unique_names(evaluators: Sequence[Evaluator]) -> None:
    from fi.experiments.errors import UsageError

    seen: dict[str, int] = {}
    for ev in evaluators:
        for n in ev.names:
            seen[n] = seen.get(n, 0) + 1
    dup = [n for n, c in seen.items() if c > 1]
    if dup:
        raise UsageError(f"two evaluators produce the score name(s) {dup}; give one a name=")

