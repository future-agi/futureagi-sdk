"""F1: ``tool_called`` on a plain-function agent, the labelled fallback.

The spans are recorded from the real traceAI-openai / traceAI-anthropic 0.1.10 instrumentors over
canned provider responses (``fixtures/f1_requested_tools.json``, made by
``fixtures/make_f1_requested_tools.py``; no network, no model call). Before the fallback every case
below that is "assessed" was ``status="error"`` ("no tool spans captured"), which kept the real rows
FW-16aL / FW-16bL RED.
"""

import copy
import json
from pathlib import Path

from fi.experiments._dataset import load_local
from fi.experiments.evaluators import tool_called
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.trace_checks import FALLBACK_SOURCE, requested_tools

REC = json.loads((Path(__file__).parent / "fixtures" / "f1_requested_tools.json").read_text(encoding="utf-8"))
ROW = load_local([{"q": "Where is order A101?"}]).rows[0]
KEY = "tool_called:lookup_order"


class _Captured(list):
    """CapturedSpans' shape (a list with .dropped) without importing the capture module, which needs
    OpenTelemetry (absent on 3.14, TA-1): the fallback itself needs none, so these tests run on 3.14 too."""

    dropped = 0


def _tree(recorded, parent="r0"):
    """The trial root and the recorded LLM spans below it, with ids and start times."""
    spans = [{"name": "experiment.trial", "span_id": "r0", "parent_id": None, "attributes": {}, "start_ns": 0}]
    for i, s in enumerate(copy.deepcopy(recorded), 1):
        spans.append({**s, "span_id": f"s{i}", "parent_id": parent, "start_ns": i})
    return spans


def _ec(spans, expected=False):
    return EvalContext(row=ROW, output="Order A101 has shipped.", trace=spans, tool_spans_expected=expected,
                       instrument_hint="traceAI-openai")


def test_openai_tool_loop_scores_the_requested_call_labelled_as_a_fallback():
    score = tool_called("lookup_order").evaluate(_ec(_tree(REC["openai_tool_loop"])))[KEY]
    assert score.status == "assessed" and score.value == 1.0 and score.passed is True
    assert score.label == FALLBACK_SOURCE == "model_requested_tools (fallback)"
    assert score.explanation.startswith("source: model_requested_tools (fallback).")
    assert "not executed calls" in score.explanation and "lookup_order requested 1 time(s)" in score.explanation


def test_the_history_a_later_call_replays_is_not_counted_again():
    # the second ChatCompletion span carries the first call's tool_calls in its INPUT messages
    spans = _tree(REC["openai_tool_loop"])
    assert any(".input.messages.1.message.tool_calls.0" in k for k in spans[2]["attributes"])
    assert requested_tools(spans) == ["lookup_order"]
    two = tool_called("lookup_order", min_calls=2).evaluate(_ec(spans))[KEY]
    assert two.status == "assessed" and two.value == 0.0 and two.label == FALLBACK_SOURCE


def test_a_tool_the_model_never_asked_for_is_false_not_an_error():
    score = tool_called("refund_order").evaluate(_ec(_tree(REC["openai_tool_loop"])))["tool_called:refund_order"]
    assert score.status == "assessed" and score.value == 0.0 and score.label == FALLBACK_SOURCE
    assert "requested tools: ['lookup_order']" in score.explanation


def test_anthropic_tool_use_blocks_count():
    score = tool_called("lookup_order").evaluate(_ec(_tree(REC["anthropic_tool_use"])))[KEY]
    assert score.status == "assessed" and score.value == 1.0 and score.label == FALLBACK_SOURCE


def test_llm_spans_that_hide_their_outputs_stay_an_error():
    spans = _tree(REC["openai_tool_loop"])
    for s in spans[1:]:  # FI_HIDE_OUTPUTS-style: no output messages recorded
        s["attributes"] = {k: v for k, v in s["attributes"].items() if "output" not in k}
    score = tool_called("lookup_order").evaluate(_ec(spans))[KEY]
    assert score.status == "error" and "no tool spans captured" in score.explanation


def test_two_nested_spans_for_one_call_count_once():
    inner = copy.deepcopy(REC["openai_tool_loop"][0])
    outer = {"name": "ChatOpenAI", "attributes": copy.deepcopy(inner["attributes"])}
    spans = _tree([outer])
    spans.append({**inner, "span_id": "s9", "parent_id": "s1", "start_ns": 5})
    assert requested_tools(spans) == ["lookup_order"]


def test_a_json_output_messages_value_is_read():
    value = json.dumps([{"role": "assistant", "parts": [{"type": "tool_call", "name": "lookup_order", "id": "c1"}]}])
    spans = _tree([{"name": "chat", "attributes": {"gen_ai.output.messages": value, "gen_ai.span.kind": "LLM"}}])
    assert tool_called("lookup_order").evaluate(_ec(spans))[KEY].value == 1.0


def test_a_traced_tool_span_wins_and_is_not_labelled():
    spans = _tree(REC["openai_tool_loop"])
    spans.append({"name": "lookup_order", "span_id": "t1", "parent_id": "r0", "start_ns": 3,
                  "attributes": {"fi.span.kind": "TOOL", "tool.name": "lookup_order"}})
    score = tool_called("lookup_order").evaluate(_ec(spans))[KEY]
    assert score.value == 1.0 and score.label is None and "source:" not in score.explanation


def test_with_a_framework_instrumentor_on_a_missing_tool_span_means_not_called():
    # traceAI-langchain on: tools that ran have spans, so none means none ran (no fallback)
    score = tool_called("lookup_order").evaluate(_ec(_tree(REC["openai_tool_loop"]), expected=True))[KEY]
    assert score.status == "assessed" and score.value == 0.0 and score.label is None


def test_a_capture_past_its_limit_cannot_say_false():
    spans = _Captured(_tree(REC["openai_tool_loop"][1:]))  # the requesting span was not kept
    spans.dropped = 3
    score = tool_called("lookup_order").evaluate(_ec(spans))[KEY]
    assert score.status == "error" and "past the capture limit" in score.explanation
