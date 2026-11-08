"""Results: summary, gates, exit codes; cost arithmetic."""

import pytest

from fi import experiments
from fi.experiments import Limits
from fi.experiments._cost import Usage, lookup_price, priced_usd
from fi.experiments.results import EvalScore


def _result(monkeypatch=None):
    rows = [{"id": f"T{i}", "q": i} for i in range(1, 5)]

    def task(row):
        if row["q"] == 4:
            raise KeyError("missing")
        return row["q"]

    @experiments.evaluator(name="big", passing_score=2)
    def big(output):
        return output

    return experiments.run(rows, task, [big], upload=False, progress=False, limits=Limits(fail_fast=0))


def test_summary_numbers():
    s = _result().summary()
    assert (s.trials, s.completed, s.failed, s.skipped) == (4, 3, 1, 0)
    # the failed trial (T4) is 0 and a fail under the default error policy, zero
    assert s.evaluators["big"].mean == pytest.approx(1.5)
    assert s.evaluators["big"].pass_rate == pytest.approx(0.5)
    assert s.evaluators["big"].failed_trials == 1
    ex = _result().summary("exclude")  # left out under exclude
    assert ex.evaluators["big"].mean == pytest.approx(2.0) and ex.evaluators["big"].pass_rate == pytest.approx(2 / 3)
    assert s.errors_by_type == {"KeyError": 1}
    assert s.error_rate == pytest.approx(0.25)
    assert s.latency_ms["p50"] is not None


def test_assert_passing_and_exit_codes(monkeypatch):
    result = _result()
    assert result.assert_passing({"big": 0.5}, raise_on_fail=False).passed
    gate = result.assert_passing(0.9, raise_on_fail=False)
    assert not gate.passed and gate.exit_code == 1
    with pytest.raises(AssertionError):
        result.assert_passing(0.9)
    errs = result.assert_passing(max_error_rate=0.1, raise_on_fail=False)
    assert errs.exit_code == 5
    assert result.exit_code == 0
    monkeypatch.setenv("CI", "true")
    assert result.exit_code == 5


def test_evalscore_bool_and_frozen():
    s = EvalScore(True)
    assert (s.value, s.passed) == (1.0, True)
    with pytest.raises(Exception):
        s.value = 2  # frozen


def test_prices_and_reported_dollars():
    u = Usage()
    u.add_span({"gen_ai.request.model": "openai/gpt-x-2025-01-01", "gen_ai.usage.input_tokens": 2_000_000,
                "gen_ai.usage.output_tokens": 1_000_000})
    assert lookup_price("openai/gpt-x-2025-01-01", {"gpt-x": (1.0, 2.0)}) == (1.0, 2.0)
    assert priced_usd(u, {"gpt-x": (1.0, 2.0)}) == (pytest.approx(4.0), [])
    assert priced_usd(u, {}) == (None, ["openai/gpt-x-2025-01-01"])
    v = Usage()
    v.add_span({"llm.model_name": "claude-x", "llm.token_count.prompt": 10, "gen_ai.cost.total": 0.5})
    assert priced_usd(v, {}) == (pytest.approx(0.5), [])


def test_usage_counts_innermost_llm_spans_only():
    from fi.experiments._cost import usage_from_spans

    def span(sid, parent, tokens=None):
        attrs = {"gen_ai.request.model": "m"}
        if tokens:
            attrs.update({"gen_ai.usage.input_tokens": tokens, "gen_ai.usage.output_tokens": tokens})
        return {"span_id": sid, "parent_id": parent, "attributes": attrs}

    spans = [span("root", None), span("chat", "root", 100), span("client", "chat", 100), span("other", "root", 7)]
    u = usage_from_spans(spans)
    assert (u.input_tokens, u.output_tokens) == (107, 107)
