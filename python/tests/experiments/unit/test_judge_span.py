"""Contract: ``judge()`` gets its own span, a child of the trial's root span, with the model, tokens,
cost, latency and the verdict (or the error). No network, no model: the judge answers through an
httpx.MockTransport and the spans go to an in-memory exporter on the caller's own provider.
"""

import json

import httpx
import pytest

pytest.importorskip("opentelemetry.sdk")  # trace=provider needs it (absent on 3.14, TA-1)

from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402
from opentelemetry.trace import StatusCode  # noqa: E402

from fi import experiments  # noqa: E402
from fi.experiments.evaluators.judge import CRITERIA_SPAN_NAME, SPAN_NAME, Judge  # noqa: E402
from tests.experiments.unit.judge_helpers import part_verdict, with_criteria  # noqa: E402

FAKE = "-".join(("judge", "fake", "value"))  # built at run time: the pre-ship scan reads literals
ROWS = [{"id": "a", "question": "Where is order A101?", "expected": "Order A101 has shipped."},
        {"id": "b", "question": "Where is order B202?", "expected": "Order B202 is delayed."}]


def _provider():
    mem = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(mem))
    return provider, mem


def _judge(handler):
    return Judge("Is the answer correct?", model="gpt-4.1-nano", api_key_env="JUDGE_KEY",
                 base_url="http://judge.test/v1", transport=httpx.MockTransport(with_criteria(handler)))


def _verdict(passed=True, reason="same facts", tokens=(120, 30)):
    def handler(request):
        return httpx.Response(200, json=part_verdict(passed, reason, model="gpt-4.1-nano-2025-04-14", tokens=tokens))
    return handler


def _task(row):
    return f"{row['question']} It shipped."


def test_each_judge_call_is_a_child_span_of_its_trial_with_model_tokens_cost_latency_and_verdict(monkeypatch):
    monkeypatch.setenv("JUDGE_KEY", FAKE)
    provider, mem = _provider()
    result = experiments.run(ROWS, _task, [_judge(_verdict())], upload=False, progress=False, trace=provider,
                             instrument=False, limits=experiments.Limits(prices={"gpt-4.1-nano": (0.1, 0.4)}))
    spans = mem.get_finished_spans()
    roots = {s.context.span_id: s for s in spans if s.name == "experiment.trial"}
    judges = [s for s in spans if s.name == SPAN_NAME]
    assert len(roots) == 2 and len(judges) == 2
    for j in judges:
        assert j.parent is not None and j.parent.span_id in roots  # a child of its own trial's root
        assert j.context.trace_id == roots[j.parent.span_id].context.trace_id
        a = j.attributes
        assert a["fi.span.kind"] == "EVALUATOR" and a["gen_ai.evaluation.name"] == "judge"
        assert a["gen_ai.request.model"] == "gpt-4.1-nano" and a["gen_ai.response.model"] == "gpt-4.1-nano-2025-04-14"
        assert (a["gen_ai.usage.input_tokens"], a["gen_ai.usage.output_tokens"]) == (120, 30)
        assert a["gen_ai.cost.total"] == pytest.approx(120 / 1e6 * 0.1 + 30 / 1e6 * 0.4)
        assert a["fi.experiment.judge.latency_ms"] >= 0 and a["fi.experiment.judge.status"] == "assessed"
        assert a["gen_ai.evaluation.score.value"] == 1.0 and a["fi.experiment.judge.passed"] is True
        assert a["gen_ai.evaluation.score.label"] == "pass" and a["gen_ai.evaluation.explanation"] == "same facts"
        assert a["fi.experiment.example_id"] in {"a", "b"}  # the trial's identity rides along (baggage)
        assert a["server.address"] == "judge.test" and FAKE not in json.dumps(dict(a))
        assert a["fi.experiment.judge.uses_expected"] is True  # the criteria ask about correctness
        assert a["fi.experiment.judge.uses_input"] is True and a["fi.experiment.judge.parts_total"] == 1
        assert a["fi.experiment.judge.parts_met"] == 1
    # the criteria read once for the whole run, on its own span (model, tokens, cost, latency, the answer)
    [read] = [s for s in spans if s.name == CRITERIA_SPAN_NAME]
    assert read.parent is not None and read.parent.span_id in roots
    assert read.attributes["fi.experiment.judge.asks_correctness"] is True
    assert json.loads(read.attributes["fi.experiment.judge.parts"])[0]["needs_right_answer"] is True
    assert (read.attributes["gen_ai.usage.input_tokens"], read.attributes["gen_ai.usage.output_tokens"]) == (3, 2)
    assert read.attributes["gen_ai.request.model"] == "gpt-4.1-nano" and "gen_ai.cost.total" in read.attributes
    # the judge's tokens are the judge's: not in the task's per-trial tokens (they count toward the cap apart)
    assert all(i.tokens is None for i in result.items)


def test_a_failed_judge_call_marks_its_span_as_an_error(monkeypatch):
    monkeypatch.setenv("JUDGE_KEY", FAKE)
    provider, mem = _provider()
    result = experiments.run(ROWS[:1], _task, [_judge(lambda r: httpx.Response(503, text="overloaded"))],
                             upload=False, progress=False, trace=provider, instrument=False)
    assert result.items[0].scores["judge"].status == "error"
    [j] = [s for s in mem.get_finished_spans() if s.name == SPAN_NAME]
    assert j.status.status_code == StatusCode.ERROR and "503" in j.status.description
    assert j.attributes["fi.experiment.judge.status"] == "error"
    assert "gen_ai.evaluation.score.value" not in j.attributes


def test_an_unpriced_judge_model_says_so_on_its_span(monkeypatch):
    monkeypatch.setenv("JUDGE_KEY", FAKE)
    provider, mem = _provider()
    experiments.run(ROWS[:1], _task, [_judge(_verdict(False, "another status"))], upload=False, progress=False,
                    trace=provider, instrument=False)
    [j] = [s for s in mem.get_finished_spans() if s.name == SPAN_NAME]
    assert j.attributes["fi.experiment.judge.cost_unpriced"] is True and "gen_ai.cost.total" not in j.attributes
    assert j.attributes["fi.experiment.judge.passed"] is False and j.attributes["gen_ai.evaluation.score.label"] == "fail"


def test_an_untraced_run_makes_no_judge_span(monkeypatch):
    monkeypatch.setenv("JUDGE_KEY", FAKE)
    result = experiments.run(ROWS[:1], _task, [_judge(_verdict())], upload=False, progress=False, trace=False)
    assert result.items[0].scores["judge"].value == 1.0
