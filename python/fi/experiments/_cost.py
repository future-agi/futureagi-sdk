"""Cost and tokens: the span token meter, prices, and the run budget.

- Tokens come from LLM spans: ``gen_ai.usage.input_tokens`` / ``output_tokens`` (also the
  ``llm.token_count.prompt`` / ``completion`` names traceAI writes), by the model on the span.
- Price precedence, highest first: ``Limits(prices=...)``; dollars the framework reports (a
  reported $0 with tokens > 0 counts as unpriced); the server price list (SRV-6, later); the
  bundled table (a later release). No bundled ``prices.json`` in this build.
- ``max_cost_usd`` with a model that has no price raises ``UnpricedModelError``: a judge model
  before the first trial; a task model at the first trial that shows it (no new trial starts).
- ``judge()`` calls count toward the cap. Template evals do not: the platform bills them in its
  own credits, which the SDK cannot see; the run header and metadata say so.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

_INPUT_KEYS = ("gen_ai.usage.input_tokens", "gen_ai.usage.prompt_tokens", "llm.token_count.prompt")
_OUTPUT_KEYS = (
    "gen_ai.usage.output_tokens",
    "gen_ai.usage.completion_tokens",
    "llm.token_count.completion",
)
_MODEL_KEYS = ("gen_ai.response.model", "gen_ai.request.model", "llm.model_name")
_COST_KEYS = ("gen_ai.cost.total", "gen_ai.usage.cost", "llm.cost.total")
_DATE_SUFFIX = re.compile(r"-(\d{4}-\d{2}-\d{2}|\d{8})$")


def normalize_model(name: str) -> str:
    name = name.strip()
    if "/" in name:
        name = name.split("/", 1)[1]
    return name


def lookup_price(model: str, prices: Mapping[str, tuple[float, float]]) -> Optional[tuple[float, float]]:
    if not prices:
        return None
    for candidate in (model, normalize_model(model), _DATE_SUFFIX.sub("", normalize_model(model))):
        if candidate in prices:
            p = prices[candidate]
            return float(p[0]), float(p[1])
    return None


def _first(attrs: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for k in keys:
        if k in attrs and attrs[k] is not None:
            return attrs[k]
    return None


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    by_model: dict[str, list[int]] = field(default_factory=dict)  # model -> [in, out]
    reported_usd: float = 0.0
    added_usd: float = 0.0  # ctx.add_cost()

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add_span(self, attrs: Mapping[str, Any]) -> None:
        tin, tout = _first(attrs, _INPUT_KEYS), _first(attrs, _OUTPUT_KEYS)
        cost = _first(attrs, _COST_KEYS)
        if tin is None and tout is None and cost is None:
            return
        tin, tout = int(tin or 0), int(tout or 0)
        self.input_tokens += tin
        self.output_tokens += tout
        model = str(_first(attrs, _MODEL_KEYS) or "unknown")
        pair = self.by_model.setdefault(model, [0, 0])
        pair[0] += tin
        pair[1] += tout
        if cost is not None:
            try:
                self.reported_usd += float(cost)
            except (TypeError, ValueError):
                pass

    def add(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """One model call that no span shows (an evaluator's judge call)."""
        self.add_span({"gen_ai.request.model": model, "gen_ai.usage.input_tokens": input_tokens,
                       "gen_ai.usage.output_tokens": output_tokens})

    def to_json(self) -> dict[str, Any]:
        return {"input": self.input_tokens, "output": self.output_tokens, "total": self.total_tokens}


def has_usage(attrs: Mapping[str, Any]) -> bool:
    return any(_first(attrs, keys) is not None for keys in (_INPUT_KEYS, _OUTPUT_KEYS, _COST_KEYS))


def usage_attributes(attrs: Mapping[str, Any]) -> dict[str, Any]:
    """Only what the meter reads from a span: its model, token and cost attributes."""
    return {k: attrs[k] for k in (*_INPUT_KEYS, *_OUTPUT_KEYS, *_MODEL_KEYS, *_COST_KEYS) if k in attrs}


def usage_from_spans(spans: Iterable[Mapping[str, Any]]) -> Usage:
    """Sum usage over the innermost LLM spans only.

    Two instrumentors can describe one model call (traceAI-langchain's ChatOpenAI span and
    traceAI-openai's client span below it); counting both would double the tokens and the cost.
    A span with usage that has a descendant with usage is skipped.
    """
    spans = list(spans)
    parent_of = {s.get("span_id"): s.get("parent_id") for s in spans}
    with_usage = {s.get("span_id"): s for s in spans if has_usage(s.get("attributes") or {})}
    outer: set = set()
    for sid in with_usage:
        seen: set = set()
        p = parent_of.get(sid)
        while p and p not in seen:
            seen.add(p)
            if p in with_usage:
                outer.add(p)
            p = parent_of.get(p)
    usage = Usage()
    for sid, span in with_usage.items():
        if sid not in outer:
            usage.add_span(span.get("attributes") or {})
    return usage


def priced_usd(usage: Usage, prices: Mapping[str, tuple[float, float]]) -> tuple[Optional[float], list[str]]:
    """(dollars, unpriced models). Prices beat reported dollars; reported $0 with tokens is unpriced.
    ``None`` dollars when nothing was measured."""
    if not usage.by_model and not usage.reported_usd and not usage.added_usd:
        return None, []
    total = usage.added_usd
    unpriced: list[str] = []
    priced_any = False
    for model, (tin, tout) in usage.by_model.items():
        if tin == 0 and tout == 0:
            continue
        price = lookup_price(model, prices)
        if price is None:
            unpriced.append(model)
            continue
        priced_any = True
        total += tin / 1e6 * price[0] + tout / 1e6 * price[1]
    if unpriced and usage.reported_usd > 0:
        # the framework reported dollars for what the table cannot price
        return total + usage.reported_usd, []
    if not usage.by_model and usage.reported_usd > 0:
        return total + usage.reported_usd, []
    if unpriced:
        return (total if priced_any or usage.added_usd else None), unpriced
    return total, []


class RunBudget:
    """The run-level ``max_cost_usd`` hook: no new trial starts once spend >= cap."""

    def __init__(self, cap: Optional[float], prices: Mapping[str, tuple[float, float]]) -> None:
        self.cap = cap
        self.prices = dict(prices or {})
        self.spent = 0.0
        self.eval_spent = 0.0
        self.trials_measured = 0
        self.measured = False  # any trial showed usage the meter could price
        self.unpriced: list[str] = []
        self._lock = threading.Lock()

    @property
    def active(self) -> bool:
        return self.cap is not None

    def exhausted(self) -> bool:
        with self._lock:
            return self.cap is not None and self.spent >= self.cap

    def record(self, usage: Usage, *, evaluator: bool = False) -> tuple[Optional[float], list[str]]:
        usd, unpriced = priced_usd(usage, self.prices)
        with self._lock:
            if usd is not None:
                self.spent += usd
                if evaluator:
                    self.eval_spent += usd
                else:
                    self.measured = True
            if not evaluator:
                self.trials_measured += 1
            self.unpriced += [m for m in unpriced if m not in self.unpriced]
        return usd, unpriced

    def metadata(self, templates: bool) -> Optional[dict]:
        if self.cap is None:
            return None
        return {
            "usd": self.cap,
            "spent_usd": round(self.spent, 8),
            "judge_usd": round(self.eval_spent, 8),
            "enforced": self.measured,
            "unpriced_models": list(self.unpriced),
            "excludes": ["template evals (billed by the platform in credits)"] if templates else [],
        }
