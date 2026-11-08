"""F7 (reports/WAVE1.md section, e2e SDK regression diagnostic): a trial's span capture is limited by bytes
as well as by count, and never silently. Values are cut to 32 KB with a marker, a trial keeps at most
8 MiB of span data, the trial's root span always stays, and every cut shows: on the exported root span
(``fi.experiment.local_capture.*``), on the spans list evaluators get, in trace checks (error, not False),
in ``result.metadata["tracing"]`` and in the run summary. No network, no model; uploads go to the
in-process stand-in.

Tokens, cost and ``max_cost_usd`` never depend on these limits: an LLM span past a
limit is kept as a slim usage record, so the meter counts every one, once."""

import json

import pytest

pytest.importorskip("opentelemetry.sdk")  # trace=True needs it (absent on 3.14, TA-1)

from opentelemetry import trace  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402

from fi import experiments  # noqa: E402
from fi.experiments._tracing import capture as cap  # noqa: E402
from fi.experiments._tracing.capture import (  # noqa: E402
    MAX_BYTES_PER_TRIAL,
    MAX_VALUE_BYTES,
    TRUNCATED,
    TrialCapture,
    clip,
)
from tests.experiments.unit.contract_server import ContractServer, client_for  # noqa: E402

BIG = "d" * (64 * 1024)  # one 64 KB attribute value, shared by every span (the task itself stays small)


def _captured_bytes(spans) -> int:
    total = 0
    for s in spans:
        for v in list(s["attributes"].values()) + [v for e in s["events"] for v in e["attributes"].values()]:
            total += len(v.encode("utf-8")) if isinstance(v, str) else 8
    return total


def _heavy_task(n_spans: int, value: str = BIG, tool_at: int = -1):
    def task(row):
        tracer = trace.get_tracer("framework.like")
        for i in range(n_spans):
            attrs = {"retrieval.documents": value, "gen_ai.span.kind": "RETRIEVER"}
            if i == tool_at:
                attrs = {"fi.span.kind": "TOOL", "tool.name": "lookup", "tool.output": value}
            with tracer.start_as_current_span(f"step-{i}", attributes=attrs):
                pass
        return "ok"

    return task


def test_clip_keeps_values_within_the_limit_with_a_marker():
    small = "é" * 100
    assert clip(small, 1024) == (small, 200, False)
    text, size, cut = clip("x" * 5000, 1024)
    assert cut and text.endswith(TRUNCATED) and size == len(text.encode("utf-8")) and size <= 1024
    # a multibyte value is cut on a character boundary, never into an invalid sequence
    text, size, cut = clip("€" * 1000, 1024)
    assert cut and size <= 1024 and text.encode("utf-8").decode("utf-8") == text
    # the trial's own input/output truncation (session.truncate) is within the limit: not cut again
    from fi.experiments._tracing.session import truncate

    already = truncate("y" * 100_000)
    assert clip(already) == (already, len(already.encode("utf-8")), False)


def test_trial_capture_drops_past_the_byte_limit_and_always_keeps_the_root():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    capture = TrialCapture(max_spans=100, max_bytes=40_000, max_value_bytes=8_000)
    provider.add_span_processor(capture)
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("t")
    with tracer.start_as_current_span("experiment.trial") as root:
        capture.open(root.get_span_context().trace_id)
        for i in range(20):
            with tracer.start_as_current_span(f"child-{i}", attributes={"doc": "z" * 10_000}):
                pass
        stats = capture.stats(root.get_span_context().trace_id)
        assert stats.limited and stats.dropped > 0
    spans, stats = capture.close(root.get_span_context().trace_id)
    names = [s["name"] for s in spans]
    assert "experiment.trial" in names  # the root is kept past the limit
    children = [s for s in spans if s["name"] != "experiment.trial"]
    assert len(children) + stats.dropped == 20 and 0 < len(children) < 20
    assert all(s["attributes"]["doc"].endswith(TRUNCATED) for s in children)
    assert all(len(s["attributes"]["doc"].encode("utf-8")) <= 8_000 for s in children)
    assert stats.truncated_values == len(children) and stats.bytes <= 40_000 + 1_000
    assert spans.dropped == stats.dropped
    assert stats.marker()["fi.experiment.local_capture.max_value_bytes"] == 8_000  # the capture's own limits
    # the exported spans are the originals, uncut: only the local copy is limited
    assert {len(s.attributes["doc"]) for s in exporter.get_finished_spans() if s.name.startswith("child")} == {10_000}


def test_a_heavy_trial_is_capped_by_bytes_and_says_so(capsys):
    """300 spans x 64 KB (19 MB of attribute data) in one trial: the evaluator's copy stays within
    8 MiB, each value within 32 KB, and the run says what it cut."""
    seen = {}

    @experiments.evaluator(name="spans")
    def spans(trace):
        seen["trace"] = trace
        return float(len(trace))

    result = experiments.run([{"id": "T1", "q": 1}], _heavy_task(300), [spans], upload=False, progress=True,
                             instrument=False)
    got = seen["trace"]
    assert result.items[0].status == "completed"
    assert _captured_bytes(got) <= MAX_BYTES_PER_TRIAL
    values = [s["attributes"]["retrieval.documents"] for s in got if s["name"].startswith("step-")]
    assert values and all(v.endswith(TRUNCATED) and len(v.encode("utf-8")) <= MAX_VALUE_BYTES for v in values)
    assert got.dropped > 0 and len(values) + got.dropped == 300
    root = next(s for s in got if s["name"] == "experiment.trial")
    assert root["attributes"]["fi.experiment.local_capture.truncated"] is True
    assert root["attributes"]["fi.experiment.local_capture.dropped_spans"] == got.dropped
    assert root["attributes"]["fi.experiment.local_capture.max_bytes"] == MAX_BYTES_PER_TRIAL
    meta = result.metadata["tracing"]["capture"]
    assert meta["trials"] == 1 and meta["dropped_spans"] == got.dropped and meta["truncated_values"] == len(values)
    out = capsys.readouterr().err
    assert "Tracing  1 trial(s) hit the local span capture limit (2000 spans and 8 MiB per trial" in out
    assert f"{got.dropped} span(s) not kept" in out


def test_the_count_limit_is_not_silent_either(monkeypatch):
    monkeypatch.setattr(cap, "TrialCapture", lambda: TrialCapture(max_spans=5))  # setup_run_tracing's capture
    seen = {}

    @experiments.evaluator(name="n")
    def n(trace):
        seen["trace"] = trace
        return 1.0

    result = experiments.run([{"q": 1}], _heavy_task(12, value="small"), [n], upload=False, progress=False,
                             instrument=False)
    assert len(seen["trace"]) == 6 and seen["trace"].dropped == 7  # 5 children + the root; 7 not kept
    assert result.metadata["tracing"]["capture"]["dropped_spans"] == 7


def test_a_trial_under_the_limits_is_unmarked():
    seen = {}

    @experiments.evaluator(name="n")
    def n(trace):
        seen["trace"] = trace
        return 1.0

    result = experiments.run([{"q": 1}], _heavy_task(3, value="small"), [n], upload=False, progress=False,
                             instrument=False)
    root = next(s for s in seen["trace"] if s["name"] == "experiment.trial")
    assert not any(k.startswith("fi.experiment.local_capture.") for k in root["attributes"])
    assert seen["trace"].dropped == 0 and "tracing" not in result.metadata


def test_tool_called_is_an_error_not_false_when_the_tool_span_was_past_the_limit():
    from fi.experiments.evaluators import tool_called

    result = experiments.run([{"q": 1}], _heavy_task(400, tool_at=399), [tool_called("lookup")], upload=False,
                             progress=False, instrument=False)
    score = result.items[0].scores["tool_called:lookup"]
    assert score.status == "error" and score.passed is None
    assert "past the capture limit" in score.explanation and "not kept" in score.explanation
    # a tool span inside the limit still scores, whatever was dropped after it
    found = experiments.run([{"q": 1}], _heavy_task(400, tool_at=0), [tool_called("lookup")], upload=False,
                            progress=False, instrument=False)
    assert found.items[0].scores["tool_called:lookup"].passed is True


def test_the_uploaded_trace_carries_the_truncation_marker(monkeypatch):
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._upload_session import UploadSession

    mem = InMemorySpanExporter()

    def factory(self, **kw):
        creds = self.client.auth
        return exporter_factory(base_url=self.base_url, api_key=creds.api_key, secret_key=creds.secret_key,
                                inner=mem, **kw)

    monkeypatch.setattr(UploadSession, "exporter_factory", factory)
    server = ContractServer()
    result = experiments.run(experiments.dataset([{"question": "q1", "expected": "ok"}], name="t-capture"), _heavy_task(300), [],
                             client=client_for(server),
                             progress=False, trace=True, instrument=False)
    roots = [s for s in mem.get_finished_spans() if s.name == "experiment.trial"]
    assert len(roots) == 1
    attrs = dict(roots[0].attributes)
    assert attrs["fi.experiment.local_capture.truncated"] is True and attrs["fi.experiment.local_capture.dropped_spans"] > 0
    assert attrs["fi.experiment.local_capture.max_value_bytes"] == MAX_VALUE_BYTES
    assert json.dumps(result.metadata["tracing"]["capture"])  # JSON-friendly for the result file


CALLS, IN_T, OUT_T = 120, 1000, 100
HISTORY = "m" * (30 * 1024)  # one ~30 KB message per attribute (under the 32 KB value cut)


def _agent_loop(row):
    """A long agent loop (regression coverage probe): 120 LLM spans of 1,000 / 100 tokens, each carrying 3 messages of
    history (~92 KB), so the trial passes 8 MiB long before 2,000 spans."""
    tracer = trace.get_tracer("framework.like")
    for i in range(CALLS):
        attrs = {"fi.span.kind": "LLM", "llm.model_name": "gpt-4.1-nano",
                 "llm.token_count.prompt": IN_T, "llm.token_count.completion": OUT_T}
        for j in range(3):
            attrs[f"llm.input_messages.{j}.message.content"] = HISTORY
        with tracer.start_as_current_span(f"llm-{i}", attributes=attrs):
            pass
    return "ok"


def test_tokens_and_spend_count_llm_spans_past_the_byte_limit(capsys):
    """M3: on the recorded revision this measured 99,000 tokens instead of 132,000 (cost 25% low, cost cap 'enforced')."""
    seen = {}

    @experiments.evaluator(name="n")
    def n(trace):
        seen["trace"] = trace
        return 1.0

    result = experiments.run([{"q": 1}], _agent_loop, [n], upload=False, progress=True, instrument=False,
                             max_cost_usd=100.0, limits=experiments.Limits(prices={"gpt-4.1-nano": (1.0, 4.0)}))
    item = result.items[0]
    got = seen["trace"]
    kept = sum(1 for s in got if s["name"].startswith("llm-"))
    assert (kept, got.dropped) == (90, 30)  # the byte limit cut the evaluator's copy (as on the recorded revision)...
    assert item.tokens == {"input": CALLS * IN_T, "output": CALLS * OUT_T, "total": 132_000}  # ...not the meter
    assert item.cost_usd == pytest.approx(CALLS * (IN_T * 1.0 + OUT_T * 4.0) / 1e6)  # $0.168
    assert result.metadata["spent_usd"] == pytest.approx(0.168) and result.metadata["cost_cap"]["enforced"]
    assert len(got.usage_only) == got.dropped  # one slim record per LLM span past the limit
    assert all(set(r["attributes"]) == {"llm.model_name", "llm.token_count.prompt", "llm.token_count.completion"}
               for r in got.usage_only)
    root = next(s for s in got if s["name"] == "experiment.trial")
    assert root["attributes"]["fi.experiment.local_capture.usage_records"] == got.dropped
    assert root["attributes"]["fi.experiment.local_capture.usage_spans_lost"] == 0
    assert "tokens and cost count every span" in capsys.readouterr().err


def test_the_innermost_llm_span_dedup_holds_across_spans_past_the_limit():
    """Two instrumentors describe one call (an outer framework LLM span, a chain span, the client's LLM span);
    with all three past the limit, the call counts once."""
    capture = TrialCapture(max_spans=1)
    provider = TracerProvider()
    provider.add_span_processor(capture)
    tracer = provider.get_tracer("t")
    usage = {"llm.model_name": "m", "llm.token_count.prompt": 10, "llm.token_count.completion": 5}
    with tracer.start_as_current_span("experiment.trial") as root:
        tid = root.get_span_context().trace_id
        capture.open(tid)
        with tracer.start_as_current_span("filler"):
            pass
        for _ in range(3):
            with tracer.start_as_current_span("framework.llm", attributes=usage):
                with tracer.start_as_current_span("chain", attributes={"x": "y"}):
                    with tracer.start_as_current_span("client.llm", attributes=usage):
                        pass
        with tracer.start_as_current_span("unrelated", attributes={"x": "y"}):
            pass
    spans, stats = capture.close(tid)
    from fi.experiments._cost import usage_from_spans

    assert stats.dropped == 10 and [s["name"] for s in spans] == ["filler", "experiment.trial"]
    assert sorted(r["name"] for r in spans.usage_only) == ["chain"] * 3 + ["client.llm"] * 3 + ["framework.llm"] * 3
    assert usage_from_spans([*spans, *spans.usage_only]).to_json() == {"input": 30, "output": 15, "total": 45}


def test_usage_spans_past_the_record_limit_are_counted_and_said(monkeypatch, capsys):
    monkeypatch.setattr(cap, "TrialCapture", lambda: TrialCapture(max_spans=2, max_usage_records=5))
    result = experiments.run([{"q": 1}], _agent_loop, [], upload=False, progress=True, instrument=False)
    meta = result.metadata["tracing"]["capture"]
    assert meta["usage_spans_lost"] == CALLS - 2 - 5  # 2 kept in full, 5 slim records
    assert result.items[0].tokens["total"] == 7 * (IN_T + OUT_T)
    assert f"{CALLS - 7} LLM span(s) past the capture's usage records are NOT in the tokens" in capsys.readouterr().err
