"""tool_called / tool_order on captured spans; status=error (never False) when spans are missing."""

from fi.experiments._dataset import load_local
from fi.experiments.evaluators import tool_called, tool_order
from fi.experiments.evaluators._base import EvalContext

ROW = load_local([{"q": "x"}]).rows[0]
ROOT = {"name": "experiment.trial", "attributes": {}, "start_ns": 0}


def tool(name, t, kind_key="fi.span.kind"):
    return {"name": f"{name}-span", "attributes": {kind_key: "TOOL", "tool.name": name}, "start_ns": t}


def llm(t):
    return {"name": "ChatOpenAI", "attributes": {"fi.span.kind": "LLM"}, "start_ns": t}


def ec(spans, expected=True):
    return EvalContext(row=ROW, output="o", trace=spans, tool_spans_expected=expected,
                       instrument_hint="traceAI-langchain")


def test_tool_called_true_false_and_counts():
    spans = [ROOT, llm(1), tool("lookup_order", 2), tool("refund_order", 3, "openinference.span.kind")]
    assert tool_called("lookup_order").evaluate(ec(spans))["tool_called:lookup_order"].value == 1.0
    assert tool_called("cancel").evaluate(ec(spans))["tool_called:cancel"].value == 0.0
    assert tool_called("lookup_order", min_calls=2).evaluate(ec(spans))["tool_called:lookup_order"].value == 0.0
    # no tool spans but the framework instrumentor is on and LLM spans exist: the model skipped it
    assert tool_called("lookup_order").evaluate(ec([ROOT, llm(1)]))["tool_called:lookup_order"].value == 0.0


def test_tool_order_subsequence():
    spans = [ROOT, tool("lookup_order", 1), tool("other", 2), tool("refund_order", 3)]
    name = "tool_order:lookup_order>refund_order"
    assert tool_order(["lookup_order", "refund_order"]).evaluate(ec(spans))[name].value == 1.0
    rev = "tool_order:refund_order>lookup_order"
    assert tool_order(["refund_order", "lookup_order"]).evaluate(ec(spans))[rev].value == 0.0


def test_error_when_no_spans_to_judge():
    s = tool_called("x").evaluate(ec(None))["tool_called:x"]
    assert s.status == "error" and "tracing is off" in s.explanation
    s = tool_called("x").evaluate(ec([ROOT]))["tool_called:x"]
    assert s.status == "error" and "traceAI-langchain" in s.explanation
    s = tool_called("x").evaluate(ec([ROOT, llm(1)], expected=False))["tool_called:x"]
    assert s.status == "error" and "no tool spans" in s.explanation


def test_real_traceai_langchain_keys():
    """Keys observed from traceAI-langchain 0.2.0 + langgraph 1.2.16 on 2026-10-21 (a real graph with a
    real @tool, no model): gen_ai.span.kind=TOOL and gen_ai.tool.name."""
    span = {"name": "lookup_order", "start_ns": 5,
            "attributes": {"gen_ai.tool.name": "lookup_order", "gen_ai.span.kind": "TOOL"}}
    agent = {"name": "agent", "start_ns": 1, "attributes": {"gen_ai.span.kind": "AGENT"}}
    s = tool_called("lookup_order").evaluate(ec([ROOT, agent, span]))["tool_called:lookup_order"]
    assert s.value == 1.0
