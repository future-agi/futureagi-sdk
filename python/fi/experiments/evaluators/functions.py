"""Local function evaluators: arguments bound by name, the return forms, declared names.

``def correct(output, expected) -> bool``. Arguments are bound by name from ``row, input, output,
expected, metadata, trace, state, ctx``. A dict return needs its names declared up front with
``@experiments.evaluator(names=[...])``. An exception becomes ``EvalScore(status="error")``.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Mapping, Optional, Sequence

from fi.experiments.adapters._base import is_async_callable, qualname
from fi.experiments.errors import UsageError
from fi.experiments.evaluators._base import ARGUMENT_NAMES, EvalContext, Evaluator, error_score, to_score
from fi.experiments.results import EvalScore

_META = "__fi_evaluator__"


def evaluator(
    fn: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    names: Optional[Sequence[str]] = None,
    passing_score: Optional[float] = None,
) -> Any:
    """Declare a local evaluator's score name(s) and pass threshold. Returns the same function."""

    def mark(f: Callable[..., Any]) -> Callable[..., Any]:
        if name and names:
            raise UsageError("pass name= or names=, not both")
        setattr(f, _META, {"name": name, "names": tuple(names) if names else None, "passing_score": passing_score})
        return f

    return mark(fn) if fn is not None else mark


def _bound_names(fn: Callable[..., Any]) -> tuple[list[str], bool]:
    sig = inspect.signature(fn)
    wanted: list[str] = []
    takes_kwargs = False
    for p in sig.parameters.values():
        if p.kind == p.VAR_KEYWORD:
            takes_kwargs = True
            continue
        if p.kind == p.VAR_POSITIONAL:
            continue
        if p.name not in ARGUMENT_NAMES:
            if p.default is not p.empty:
                continue
            raise UsageError(
                f"evaluator {qualname(fn)} takes {p.name!r}; evaluator arguments are bound by name "
                f"from {', '.join(ARGUMENT_NAMES)}"
            )
        wanted.append(p.name)
    return wanted, takes_kwargs


class FunctionEvaluator(Evaluator):
    kind = "local"

    def __init__(self, fn: Callable[..., Any]) -> None:
        meta = getattr(fn, _META, None) or {}
        self.fn = fn
        self.declared: Optional[tuple[str, ...]] = meta.get("names")
        self.names: tuple[str, ...] = self.declared or (meta.get("name") or qualname(fn).split(".")[-1],)
        if self.names == ("<lambda>",):
            raise UsageError("a lambda evaluator needs a name: experiments.evaluator(lambda ..., name='x')")
        self.passing_score: Optional[float] = meta.get("passing_score")
        bound: tuple[list[str], bool] = _bound_names(fn)
        self.wanted: list[str] = bound[0]
        self.kwargs: bool = bound[1]
        self.is_async: bool = is_async_callable(fn)

    def _call_args(self, ec: EvalContext) -> dict[str, Any]:
        names = ARGUMENT_NAMES if self.kwargs else self.wanted
        return {n: ec.argument(n) for n in names}

    def _normalize(self, value: Any) -> dict[str, EvalScore]:
        if isinstance(value, Mapping) and not isinstance(value, EvalScore):
            if not self.declared:
                raise TypeError(
                    f"{self.names[0]} returned a dict; declare its names first: "
                    f"@experiments.evaluator(names=[{', '.join(repr(k) for k in value)}])"
                )
            extra = [k for k in value if k not in self.declared]
            if extra:
                raise TypeError(f"{self.names[0]} returned undeclared name(s) {extra}; declared: {list(self.declared)}")
            return {n: to_score(value.get(n), self.passing_score) for n in self.declared}
        if self.declared and len(self.declared) > 1:
            raise TypeError(f"{self.names} are declared, so the evaluator must return a dict with them")
        return {self.names[0]: to_score(value, self.passing_score)}

    def _errors(self, exc: BaseException) -> dict[str, EvalScore]:
        return {n: error_score(exc) for n in self.names}

    def evaluate(self, ec: EvalContext) -> dict[str, EvalScore]:
        try:
            return self._normalize(self.fn(**self._call_args(ec)))
        except Exception as exc:  # never crashes the run
            return self._errors(exc)

    async def aevaluate(self, ec: EvalContext) -> dict[str, EvalScore]:
        try:
            return self._normalize(await self.fn(**self._call_args(ec)))
        except Exception as exc:
            return self._errors(exc)
