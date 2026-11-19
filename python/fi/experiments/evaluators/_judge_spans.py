"""The judge's spans: one ``experiment.judge`` span per row's verdict (all its part requests) and one
``experiment.judge.criteria`` span for the criteria read, with the model, tokens, cost, latency, the checklist and the
verdict or the error. Split out of ``judge.py`` (the 400-line module rule; L-SDK2e review fixes).

Tracing never breaks a score: every failure here is swallowed.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators._judge_prompt import Part
from fi.experiments.results import EvalScore


def _start_span(ec: EvalContext, span_name: str, judge: Any, kind: str = "EVALUATOR") -> Any:
    """The judge's span (a row's verdict, or the criteria read) under the trial's root span; None untraced."""
    if ec.start_span is None:
        return None
    try:
        return ec.start_span(span_name, {
            "fi.span.kind": kind, "gen_ai.span.kind": kind, "gen_ai.evaluation.name": judge.names[0],
            "gen_ai.operation.name": "chat", "gen_ai.request.model": judge.model,
            "server.address": str(httpx.URL(judge._base()).host or ""), "fi.experiment.judge.criteria":
                judge.criteria[:2000],
        })
    except Exception:  # tracing never breaks a score
        return None


def _usage_attrs(ec: EvalContext, model: str, datas: Any, latency_ms: float) -> dict[str, Any]:
    """The answering model, tokens, cost (or ``cost_unpriced``) and latency of one judge call, or of a row's part
    calls together (their tokens summed)."""
    attrs: dict[str, Any] = {"fi.experiment.judge.latency_ms": round(latency_ms, 3)}
    datas = [d for d in (datas if isinstance(datas, list) else [datas]) if isinstance(d, dict)]
    usages = [d.get("usage") or {} for d in datas]
    first_model = next((d["model"] for d in datas if d.get("model")), None)
    if first_model:
        attrs["gen_ai.response.model"] = str(first_model)
    if any(usages):
        tin = sum(int(u.get("prompt_tokens") or 0) for u in usages)
        tout = sum(int(u.get("completion_tokens") or 0) for u in usages)
        attrs.update({"gen_ai.usage.input_tokens": tin, "gen_ai.usage.output_tokens": tout,
                      "gen_ai.usage.total_tokens": tin + tout})
        usd = ec.price(model, tin, tout) if ec.price is not None else None
        if usd is not None:
            attrs["gen_ai.cost.total"] = float(usd)
        else:
            attrs["fi.experiment.judge.cost_unpriced"] = True
    return attrs


def _end_criteria_span(span: Any, ec: EvalContext, model: str, data: Any, parts: Optional[tuple[Part, ...]],
                       error: Any, latency_ms: float) -> None:
    if span is None:
        return
    try:
        attrs = _usage_attrs(ec, model, data, latency_ms)
        attrs["fi.experiment.judge.status"] = "error" if error is not None else "assessed"
        if parts is not None:
            attrs["fi.experiment.judge.asks_correctness"] = any(p.needs_right_answer for p in parts)
            attrs["fi.experiment.judge.parts"] = json.dumps([p.as_dict() for p in parts], ensure_ascii=False)[:4000]
        span.set_attributes(attrs)
        if error is not None:
            from opentelemetry.trace import Status, StatusCode

            span.set_status(Status(StatusCode.ERROR, str(error)[:500]))
    except Exception:
        pass
    finally:
        span.end()


def _end_span(span: Any, ec: EvalContext, model: str, datas: Any, result: EvalScore, latency_ms: float,
              uses_expected: Optional[bool] = None, uses_input: Optional[bool] = None,
              parts: Optional[tuple[int, Optional[int]]] = None,
              counted: Optional[tuple[int, int]] = None) -> None:
    """Model, tokens, cost, latency, the checklist count and the verdict on the judge's span; the error when it
    failed. ``counted``: (parts whose count the SDK made, parts sent to the model); a row whose every part is a
    count-only part makes no call, so its span has no tokens and no answering model (wave 2f)."""
    if span is None:
        return
    try:
        attrs = _usage_attrs(ec, model, datas, latency_ms)
        attrs["fi.experiment.judge.status"] = result.status
        if uses_expected is not None:  # the row had an expected answer: was it shown to the judge (for some part)?
            attrs["fi.experiment.judge.uses_expected"] = bool(uses_expected)
        if uses_input is not None:
            attrs["fi.experiment.judge.uses_input"] = bool(uses_input)
        if parts is not None:
            attrs["fi.experiment.judge.parts_total"] = parts[0]
            if parts[1] is not None:
                attrs["fi.experiment.judge.parts_met"] = parts[1]
        if counted is not None:
            attrs["fi.experiment.judge.parts_counted"] = counted[0]
            attrs["fi.experiment.judge.parts_asked"] = counted[1]
        if result.status == "assessed":
            attrs["gen_ai.evaluation.score.value"] = float(result.value or 0.0)
            if result.passed is not None:
                attrs["fi.experiment.judge.passed"] = bool(result.passed)
                attrs["gen_ai.evaluation.score.label"] = "pass" if result.passed else "fail"
        if result.explanation:
            attrs["gen_ai.evaluation.explanation"] = result.explanation[:2000]
        span.set_attributes(attrs)
        if result.status == "error":
            from opentelemetry.trace import Status, StatusCode

            span.set_status(Status(StatusCode.ERROR, (result.explanation or "judge failed")[:500]))
    except Exception:
        pass
    finally:
        span.end()
