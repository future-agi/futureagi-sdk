"""Local function evaluators: binding by name, return forms, declared names, exceptions."""

import pytest

from fi import experiments
from fi.experiments._dataset import load_local
from fi.experiments.errors import UsageError
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.functions import FunctionEvaluator
from fi.experiments.results import EvalScore

ROW = load_local([{"id": "T1", "question": "q", "expected": "A", "metadata.tier": "gold"}]).rows[0]


def _ec(output="A"):
    return EvalContext(row=ROW, output=output, trace=[{"name": "experiment.trial", "attributes": {}}])


def test_binds_arguments_by_name():
    seen = {}

    def ev(metadata, expected, output, input, row, trace, state, ctx):
        seen.update(metadata=metadata, expected=expected, output=output, input=input, row=row.id,
                    trace=len(trace), state=state, ctx=ctx)
        return True

    assert FunctionEvaluator(ev).evaluate(_ec())["ev"].value == 1.0
    assert seen == {"metadata": {"tier": "gold"}, "expected": "A", "output": "A", "input": "q", "row": "T1",
                    "trace": 1, "state": None, "ctx": None}


def test_unknown_argument_name_refused_before_the_run():
    def ev(answer):
        return 1

    with pytest.raises(UsageError) as info:
        FunctionEvaluator(ev)
    assert "bound by name" in str(info.value)


@pytest.mark.parametrize(
    "ret, value, passed, status",
    [(True, 1.0, True, "assessed"), (False, 0.0, False, "assessed"), (0.4, 0.4, None, "assessed"),
     (None, None, None, "skipped"), (EvalScore(0.7, label="ok"), 0.7, None, "assessed")],
)
def test_return_forms(ret, value, passed, status):
    def ev(output):
        return ret

    score = FunctionEvaluator(ev).evaluate(_ec())["ev"]
    assert (score.value, score.passed, score.status) == (value, passed, status)


def test_passing_score_sets_pass():
    @experiments.evaluator(passing_score=0.5)
    def close(output):
        return 0.6

    assert FunctionEvaluator(close).evaluate(_ec())["close"].passed is True


def test_declared_names_for_dict_returns():
    @experiments.evaluator(names=["accuracy", "tone"])
    def multi(output):
        return {"accuracy": 1, "tone": 0.5}

    scores = FunctionEvaluator(multi).evaluate(_ec())
    assert scores["accuracy"].value == 1.0 and scores["tone"].value == 0.5

    def undeclared(output):
        return {"a": 1}

    s = FunctionEvaluator(undeclared).evaluate(_ec())["undeclared"]
    assert s.status == "error" and "names=" in s.explanation

    @experiments.evaluator(names=["a"])
    def extra(output):
        return {"a": 1, "b": 2}

    assert FunctionEvaluator(extra).evaluate(_ec())["a"].status == "error"


def test_exception_becomes_error_score_and_run_completes():
    def boom(output):
        raise ValueError("row 3 is weird")

    result = experiments.run([{"q": 1}, {"q": 2}], lambda r: 1, [boom], upload=False, progress=False)
    assert result.status == "no_upload"
    assert all(i.scores["boom"].status == "error" and "row 3 is weird" in i.scores["boom"].explanation
               for i in result.items)


def test_async_evaluator_and_duplicate_names():
    async def slow(output):
        return output == 1

    result = experiments.run([{"q": 1}], lambda r: 1, [slow], upload=False, progress=False)
    assert result.items[0].scores["slow"].value == 1.0

    def a(output):
        return 1

    with pytest.raises(UsageError):
        experiments.run([{"q": 1}], lambda r: 1, [a, experiments.evaluator(lambda output: 1, name="a")],
                        upload=False, progress=False)
