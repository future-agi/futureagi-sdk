"""Trace checks on the trial's captured spans: ``tool_called`` and ``tool_order`` (this release).

A check returns ``status="error"`` (never ``False``) when the trial captured no spans it can
judge: no capture at all, only the root span, or no instrumentor that emits tool spans. Then the
message names the package to install. It is also an error, not ``False``, when what the check looks
for is missing and the trial's capture left spans out (``CapturedSpans.dropped``, the per-trial
span and byte limits): those spans may hold it.

**The labelled fallback (F1, the dataset contract).** A plain-function agent's own tool code makes no span, so
``tool_called`` would find no TOOL span. When no tool span was traced and no framework instrumentor
that emits them is on, ``tool_called`` counts the tool calls the model *asked for* in its responses:
the ``tool_calls`` of the output messages on the trial's LLM spans (traceAI-openai / -anthropic write
``gen_ai.output.messages.N.message.tool_calls.M.tool_call.function.name``; the older
``llm.output_messages.*`` names and a JSON ``gen_ai.output.messages`` value are read too). Input
messages (the history a later call replays) are not counted, and of two nested LLM spans for one call
only the inner one is. The score's label and the start of its explanation say
``source: model_requested_tools (fallback)``, so it is never read as an executed tool call. With no
LLM span that records its output messages, the check stays an error.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional, Sequence

from fi.experiments.evaluators._base import EvalContext, Evaluator
from fi.experiments.results import EvalScore

_KIND_KEYS = ("fi.span.kind", "openinference.span.kind", "gen_ai.span.kind")
_NAME_KEYS = ("tool.name", "gen_ai.tool.name", "fi.tool.name")


def _attr(span: Any, key: str) -> Any:
    attrs = span.get("attributes", {}) if isinstance(span, dict) else getattr(span, "attributes", {})
    return (attrs or {}).get(key)


def is_tool_span(span: Any) -> bool:
    if any(str(_attr(span, k) or "").upper() == "TOOL" for k in _KIND_KEYS):
        return True
    return str(_attr(span, "gen_ai.operation.name") or "") == "execute_tool"


def tool_name(span: Any) -> str:
    for key in _NAME_KEYS:
        value = _attr(span, key)
        if value:
            return str(value)
    name = span.get("name") if isinstance(span, dict) else getattr(span, "name", "")
    return str(name or "")


def tool_calls(spans: Sequence[Any]) -> list[str]:
    tools = [s for s in spans if is_tool_span(s)]
    tools.sort(key=lambda s: (s.get("start_ns") or 0) if isinstance(s, dict) else 0)
    return [tool_name(s) for s in tools]


FALLBACK_SOURCE = "model_requested_tools (fallback)"
_OUT_PREFIX = r"(?:gen_ai\.output\.messages|llm\.output_messages)\.(\d+)\.message\."
_OUT_MESSAGE = re.compile(_OUT_PREFIX)
_OUT_TOOL_NAME = re.compile(_OUT_PREFIX + r"tool_calls\.(\d+)\.tool_call\.function\.name$")


def _attrs(span: Any) -> dict:
    return (span.get("attributes", {}) if isinstance(span, dict) else getattr(span, "attributes", {})) or {}


def _json_requests(value: str) -> Optional[list[str]]:
    """Tool names in a JSON ``gen_ai.output.messages`` value (OTel GenAI parts or OpenAI tool_calls)."""
    try:
        messages = json.loads(value)
    except ValueError:
        return None
    names: list[str] = []
    for msg in messages if isinstance(messages, list) else []:
        if not isinstance(msg, dict):
            continue
        for part in msg.get("parts") or []:
            if isinstance(part, dict) and part.get("type") == "tool_call" and part.get("name"):
                names.append(str(part["name"]))
        for call in msg.get("tool_calls") or []:
            fn = call.get("function") if isinstance(call, dict) else None
            if isinstance(fn, dict) and fn.get("name"):
                names.append(str(fn["name"]))
    return names


def _span_requests(span: Any) -> Optional[list[str]]:
    """The tool calls one LLM span's output messages ask for; None when it records no output messages."""
    attrs = _attrs(span)
    found: list[tuple[int, int, str]] = []
    seen = False
    for key, value in attrs.items():
        if key == "gen_ai.output.messages" and isinstance(value, str):
            names = _json_requests(value)
            if names is not None:
                seen = True
                found += [(0, i, n) for i, n in enumerate(names)]
            continue
        if not _OUT_MESSAGE.match(key):
            continue
        seen = True
        m = _OUT_TOOL_NAME.match(key)
        if m and value:
            found.append((int(m.group(1)), int(m.group(2)), str(value)))
    return [n for _, _, n in sorted(found)] if seen else None


def requested_tools(spans: Sequence[Any]) -> Optional[list[str]]:
    """The tool calls the model asked for, in time order, over the innermost LLM spans that record their
    output messages (two nested spans for one call count once); None when no span records them."""
    per_span = {id(s): r for s in spans if (r := _span_requests(s)) is not None}
    if not per_span:
        return None
    dicts = [s for s in spans if isinstance(s, dict)]
    parent_of = {s.get("span_id"): s.get("parent_id") for s in dicts}
    with_output = {s.get("span_id") for s in dicts if id(s) in per_span and s.get("span_id")}
    outer: set = set()
    for sid in with_output:  # an output span with an output span below it is the outer of two for one call
        seen: set = set()
        p = parent_of.get(sid)
        while p and p not in seen:
            seen.add(p)
            if p in with_output:
                outer.add(p)
            p = parent_of.get(p)
    kept = [s for s in spans if id(s) in per_span and not (isinstance(s, dict) and s.get("span_id") in outer)]
    kept.sort(key=lambda s: (s.get("start_ns") or 0) if isinstance(s, dict) else 0)
    return [n for s in kept for n in per_span[id(s)]]


def _fallback(ec: EvalContext, tool: str, min_calls: int) -> Optional[EvalScore]:
    """F1: no tool span was traced, so count what the model asked for, labelled as such."""
    requested = requested_tools(ec.trace or [])
    if requested is None:
        return None
    n = sum(1 for t in requested if t == tool)
    why = (f"source: {FALLBACK_SOURCE}. No tool span was traced (a plain function's own tool code makes none), "
           f"so this counts the tool calls the model asked for in its responses, not executed calls: {tool} "
           f"requested {n} time(s); requested tools: {requested or 'none'}")
    if n < min_calls and getattr(ec.trace, "dropped", 0):
        return _partial(ec, why)
    return EvalScore(n >= min_calls, label=FALLBACK_SOURCE, explanation=why)


def _partial(ec: EvalContext, why: str) -> Optional[EvalScore]:
    dropped = getattr(ec.trace, "dropped", 0)
    if not dropped:
        return None
    return EvalScore(
        status="error",
        explanation=f"cannot judge: {why}, but {dropped} span(s) of this trial were past the capture limit "
                    "(spans and bytes per trial) and were not kept",
    )


def _cannot_judge(ec: EvalContext) -> Optional[EvalScore]:
    spans = ec.trace
    if spans is None:
        return EvalScore(status="error", explanation="no spans captured (tracing is off); run with trace=True")
    children = [s for s in spans if (s.get("name") if isinstance(s, dict) else None) != "experiment.trial"]
    if not children:
        return EvalScore(
            status="error",
            explanation=f"no spans captured below the trial; install {ec.instrument_hint}",
        )
    if not any(is_tool_span(s) for s in spans) and not ec.tool_spans_expected:
        return _partial(ec, "no tool spans among the captured spans") or EvalScore(
            status="error",
            explanation=f"no tool spans captured; install {ec.instrument_hint}",
        )
    return None


class ToolCalled(Evaluator):
    kind = "trace"

    def __init__(self, tool: str, *, min_calls: int = 1, name: Optional[str] = None) -> None:
        self.tool = tool
        self.min_calls = min_calls
        self.names: tuple[str, ...] = (name or f"tool_called:{tool}",)

    def evaluate(self, ec: EvalContext) -> dict[str, EvalScore]:
        bad = _cannot_judge(ec)
        if bad is not None:
            no_tool_spans = ec.trace is not None and not ec.tool_spans_expected and not any(
                is_tool_span(s) for s in ec.trace)
            fallback = _fallback(ec, self.tool, self.min_calls) if no_tool_spans else None
            return {self.names[0]: fallback or bad}
        calls = tool_calls(ec.trace or [])
        n = sum(1 for c in calls if c == self.tool)
        ok = n >= self.min_calls
        why = f"{self.tool} called {n} time(s); tool calls: {calls or 'none'}"
        return {self.names[0]: (None if ok else _partial(ec, why)) or EvalScore(ok, explanation=why)}


class ToolOrder(Evaluator):
    kind = "trace"

    def __init__(self, tools: Sequence[str], *, name: Optional[str] = None) -> None:
        if not tools:
            raise ValueError("tool_order() needs at least one tool name")
        self.tools: list[str] = list(tools)
        self.names: tuple[str, ...] = (name or "tool_order:" + ">".join(self.tools),)

    def evaluate(self, ec: EvalContext) -> dict[str, EvalScore]:
        bad = _cannot_judge(ec)
        if bad is not None:
            return {self.names[0]: bad}
        calls = tool_calls(ec.trace or [])
        it = iter(calls)
        ok = all(any(c == want for c in it) for want in self.tools)  # in-order subsequence
        why = f"expected {' > '.join(self.tools)}; tool calls: {calls or 'none'}"
        return {self.names[0]: (None if ok else _partial(ec, why)) or EvalScore(ok, explanation=why)}


def tool_called(tool: str, *, min_calls: int = 1, name: Optional[str] = None) -> ToolCalled:
    """True when the trial's spans show ``tool`` called at least ``min_calls`` times."""
    return ToolCalled(tool, min_calls=min_calls, name=name)


def tool_order(tools: Sequence[str], *, name: Optional[str] = None) -> ToolOrder:
    """True when the tools appear in this order among the trial's tool calls (others may sit between)."""
    return ToolOrder(tools, name=name)
