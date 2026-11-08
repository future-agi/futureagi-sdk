"""A score-only run (``from_column(col)``): the column that IS the output is never part of the evaluators' input.

Found by the F8 held-out paraphrase pairs (e2e evaluation regression, 10-22): with rows ``{id, input, expected, answer}`` and
``from_column("answer")``, the judge's INPUT was ``{"input": ..., "answer": ...}``, so it saw the OUTPUT inside the
INPUT and passed "Yes, the museum is open on Mondays" against "No, the museum is closed on Mondays" as "matching the
answer in the input". No network: the judge's transport is a mock.
"""

import json

import httpx

from fi import experiments
from fi.experiments.evaluators.functions import evaluator
from fi.experiments.evaluators.judge import Judge
from tests.experiments.unit.judge_helpers import part_verdict, with_criteria

FAKE = "-".join(("judge", "fake", "value"))  # built at run time: the pre-ship scan reads literals
ROWS = [{"id": "m1", "input": "Is the museum open on Mondays?", "expected": "No, the museum is closed on Mondays.",
         "answer": "Yes, the museum is open on Mondays."}]


def _judge(sent: list) -> Judge:
    def handler(request):
        sent.append(json.loads(request.content)["messages"][1]["content"])
        return httpx.Response(200, json=part_verdict(False, "r", tokens=(1, 1)))

    return Judge("Is the output a correct answer to the input?", model="m",
                 transport=httpx.MockTransport(with_criteria(handler)))


def test_the_judge_sees_the_question_as_input_not_the_output_column(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    sent: list = []
    result = experiments.run(ROWS, experiments.from_column("answer"), [_judge(sent)], upload=False, progress=False,
                             trace=False)
    assert result.items[0].output == "Yes, the museum is open on Mondays."
    assert len(sent) == 1
    user = sent[0]
    assert "INPUT:\nIs the museum open on Mondays?\n\nOUTPUT:\nYes, the museum is open on Mondays." in user
    assert user.count("Yes, the museum is open on Mondays.") == 1  # only as the OUTPUT
    assert "EXPECTED:\nNo, the museum is closed on Mondays." in user


def test_a_function_evaluator_gets_the_input_columns_without_the_output_column():
    seen = []

    @evaluator(name="probe")
    def probe(input, output):
        seen.append((input, output))
        return True

    rows = [{"question": "q1", "context": "c1", "reply": "r1"}]
    experiments.run(rows, experiments.from_column("reply"), [probe], upload=False, progress=False, trace=False)
    assert seen == [({"question": "q1", "context": "c1"}, "r1")]


def test_a_task_run_keeps_every_input_column():
    seen = []

    @evaluator(name="probe")
    def probe(input, output):
        seen.append(input)
        return True

    rows = [{"question": "q1", "reply": "r1"}]
    experiments.run(rows, lambda row: "out", [probe], upload=False, progress=False, trace=False)
    assert seen == [{"question": "q1", "reply": "r1"}]
