"""Tests for model retirement and judge request scheduling. No network, no model.

- A 404 counts as a retirement only if it mentions the model and a retirement term in the same clause.
  "The model `x` does not exist; the endpoint /v1/engines is deprecated" does not count because
  "deprecated" describes the endpoint rather than the model.
- Before an endpoint responds, the judge sends calls for one row at a time, including when a resumed run
  already has its checklist in the journal and can skip reading the criteria.
  Once the endpoint responds, the judge can process rows concurrently.
"""

import asyncio
import json

import httpx
import pytest

from fi import experiments
from fi.experiments import _provider_errors
from fi.experiments.evaluators._judge_prompt import Part
from fi.experiments.evaluators.judge import CRITERIA_SYSTEM, Judge
from tests.experiments.unit.judge_helpers import part_verdict

FAKE = "-".join(("judge", "fake", "value"))
RETIRED = {"error": {"message": "The model `gpt-4.1-nano` has been deprecated", "type": "invalid_request_error",
                     "code": "model_not_found"}}
TWO_PARTS = (Part("Is the reply polite?", "", False, False, True), Part("Is it in English?", "", False, False, True))
ROWS = [{"id": str(i), "input": "hi", "answer": "Hello!"} for i in range(8)]


class _Counting(httpx.AsyncBaseTransport):
    def __init__(self, status, body, delay=0.05):
        self.calls, self.reads, self.in_flight, self.peak = 0, 0, 0, 0
        self.status, self.body, self.delay = status, body, delay

    async def handle_async_request(self, request):
        if json.loads(request.content)["messages"][0]["content"] == CRITERIA_SYSTEM:
            self.reads += 1
        self.calls += 1
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        await asyncio.sleep(self.delay)
        self.in_flight -= 1
        return httpx.Response(self.status, json=self.body)


def _run(judge):
    import os

    os.environ["OPENAI_API_KEY"] = FAKE
    os.environ.pop("OPENAI_BASE_URL", None)
    return experiments.run(ROWS, experiments.from_column("answer"), [judge], upload=False, progress=False,
                           trace=False, concurrency=8)


def test_a_known_checklist_and_a_retired_model_get_one_rows_calls_not_concurrency_times_parts():
    slow = _Counting(404, RETIRED)
    judge = Judge("Is the reply polite and in English?", model="gpt-4.1-nano", transport=slow)
    judge.parts = TWO_PARTS  # as a resume restores it: no criteria read
    res = _run(judge)
    assert slow.reads == 0 and slow.calls == 2  # only the first row's two part calls were sent
    assert all("the model 'gpt-4.1-nano' was retired by the provider" in it.scores["judge"].explanation
               for it in res.items)


def test_once_the_endpoint_has_answered_rows_go_concurrently():
    fast = _Counting(200, part_verdict(True))
    judge = Judge("Is the reply polite and in English?", model="gpt-4.1-mini", transport=fast)
    judge.parts = TWO_PARTS
    res = _run(judge)
    assert all(it.scores["judge"].passed is True for it in res.items)
    assert fast.calls == 16 and fast.peak > 2  # only the first row went alone


@pytest.mark.parametrize("message,model", [
    ("The model `gpt-4o` does not exist; the endpoint /v1/engines is deprecated.", None),
    ("The model `gpt-4o` does not exist or you do not have access to it. The engines endpoint is deprecated.", None),
    ("gpt-4o was not found. Legacy completions are no longer supported", "gpt-4o"),
])
def test_a_word_in_another_clause_than_the_model_is_not_a_retirement(message, model):
    assert _provider_errors.retirement(404, {"error": {"message": message, "code": "model_not_found"}},
                                       model=model) is None


@pytest.mark.parametrize("message,model,named", [
    ("The model `gpt-4.1-nano` has been deprecated, learn more here: https://platform.openai.com/docs/deprecations",
     None, "gpt-4.1-nano"),
    ("Deprecated model `gpt-3.5-turbo-0301`; use gpt-3.5-turbo", None, "gpt-3.5-turbo-0301"),
    ("gpt-old-1 has been retired.", "gpt-old-1", "gpt-old-1"),
    ("Sorry. This model has been retired.", None, None),
])
def test_a_word_in_the_models_clause_is_a_retirement(message, model, named):
    found = _provider_errors.retirement(404, {"error": {"message": message}}, model=model)
    assert found is not None and found.model == named
