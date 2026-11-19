"""dataset service decisions after wave 2d (wave 2e). No network, no model: an httpx.MockTransport answers.

- A provider's retirement answer (OpenAI's 404 ``model_not_found`` "has been deprecated", seen for gpt-4.1-nano on
  10-23; Groq's 400 ``model_decommissioned``) is a clear error that names the model and says the provider retired it,
  never a generic "judge HTTP 404": in judge()'s score, and in a trial's error when the task's own call got it.
- After one retirement answer the judge makes no more calls to that model.
- A 404 that does not say the model is retired stays the provider's own error.
- A malformed judge answer (a part answer with no true/false verdict) is an error cell, never a pass: not passed, no
  value, counted under the summary's errors, and the span says error.
"""

import asyncio
import json

import httpx
import pytest

from fi import experiments
from fi.experiments import _provider_errors
from fi.experiments._dataset import load_local
from fi.experiments.errors import ModelRetiredError
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.judge import CRITERIA_SYSTEM, Judge
from tests.experiments.unit.judge_helpers import criteria_answer, part_verdict

FAKE = "-".join(("judge", "fake", "value"))
OPENAI_RETIRED = {"error": {"message": "The model `gpt-4.1-nano` has been deprecated, learn more here: "
                                       "https://platform.openai.com/docs/deprecations",
                            "type": "invalid_request_error", "param": None, "code": "model_not_found"}}
GROQ_RETIRED = {"error": {"message": "The model `gemma2-9b-it` has been decommissioned and is no longer supported.",
                          "type": "invalid_request_error", "code": "model_decommissioned"}}
UNKNOWN = {"error": {"message": "The model `gpt-4.1-nanoo` does not exist or you do not have access to it.",
                     "type": "invalid_request_error", "param": None, "code": "model_not_found"}}
ROW = load_local([{"question": "where is my order?"}]).rows[0]


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


def _answering(status, body, calls):
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(status, json=body)
    return httpx.MockTransport(handler)


# ---- the classifier -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("status,body,model", [
    (404, OPENAI_RETIRED, "gpt-4.1-nano"),
    (400, GROQ_RETIRED, "gemma2-9b-it"),
    (410, {"error": {"message": "This model has been retired."}}, None),
    (404, json.dumps(OPENAI_RETIRED), "gpt-4.1-nano"),  # a body still as text
    (404, OPENAI_RETIRED["error"], "gpt-4.1-nano"),     # the error object itself (openai's exc.body)
])
def test_a_retirement_answer_is_found_and_names_the_model(status, body, model):
    found = _provider_errors.retirement(status, body)
    assert found is not None and found.status == status and found.model == model


@pytest.mark.parametrize("status,body", [
    (404, UNKNOWN),                                      # a typo: the provider does not say retired
    (400, {"error": {"code": "invalid_value", "message": "max_tokens is too large"}}),
    (429, {"error": {"code": "rate_limit_exceeded", "message": "deprecated"}}),  # not a refusal status
    (500, OPENAI_RETIRED),
    (200, OPENAI_RETIRED),
])
def test_other_answers_are_not_a_retirement(status, body):
    assert _provider_errors.retirement(status, body) is None


def test_the_message_names_the_model_says_retired_and_quotes_the_provider():
    exc = ModelRetiredError("gpt-4.1-nano", status=404, provider_code="model_not_found",
                            provider_message=OPENAI_RETIRED["error"]["message"], provider="api.openai.com")
    text = str(exc)
    assert text.startswith("the model 'gpt-4.1-nano' was retired by the provider at api.openai.com (HTTP 404 "
                           "model_not_found: \"The model `gpt-4.1-nano` has been deprecated")
    assert "Name a model the provider still serves" in text and "/models" in text
    assert exc.get_error_code() == "MODEL_RETIRED" and exc.to_json()["code"] == "MODEL_RETIRED"
    # internal: no run ends with it, so it is no public name and maps to no CLI exit code
    assert "ModelRetiredError" not in experiments.errors.__all__


# ---- judge() --------------------------------------------------------------------------------------------------------

def test_the_judge_names_a_retired_model_and_stops_calling_it():
    calls: list = []
    judge = Judge("Is the reply polite?", model="gpt-4.1-nano", transport=_answering(404, OPENAI_RETIRED, calls))
    first = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="It shipped.")))["judge"]
    assert first.status == "error" and first.passed is None and first.value is None
    assert "ModelRetiredError: the model 'gpt-4.1-nano' was retired by the provider at api.openai.com (HTTP" in \
        first.explanation
    assert "judge HTTP 404" not in first.explanation
    assert len(calls) == 1  # the criteria read got the answer
    second = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="It shipped.")))["judge"]
    assert second.status == "error" and second.explanation == first.explanation and len(calls) == 1


def test_a_run_with_a_retired_judge_model_shows_the_error_on_every_row():
    calls: list = []
    judge = Judge("Is the reply polite?", model="gpt-4.1-nano", transport=_answering(404, OPENAI_RETIRED, calls))
    rows = [{"id": str(i), "input": "hi", "answer": "Hello!"} for i in range(3)]
    res = experiments.run(rows, experiments.from_column("answer"), [judge], upload=False, progress=False, trace=False)
    scores = [it.scores["judge"] for it in res.items]
    assert all(s.status == "error" and "was retired by the provider" in s.explanation and "'gpt-4.1-nano'" in
               s.explanation for s in scores)
    # an error score is left out of the pass rate under either policy, and a gate fails for an evaluator with no
    # scored rows, saying why
    for policy in ("zero", "exclude"):
        ev = res.summary(policy).evaluators["judge"]
        assert ev.errors == 3 and ev.scored == 0 and ev.pass_rate is None
    gate = res.assert_passing(0.5, raise_on_fail=False)
    assert not gate.passed and "judge: no scored rows" in gate.reasons[0] and "error scores 3" in gate.reasons[0]
    assert res.summary().error_rate == 1.0
    assert len(calls) == 1


def test_a_404_that_does_not_say_retired_stays_the_providers_error():
    judge = Judge("Is the reply polite?", model="gpt-4.1-nanoo", transport=_answering(404, UNKNOWN, []))
    score = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="It shipped.")))["judge"]
    assert score.status == "error" and "judge HTTP 404" in score.explanation and "retired" not in score.explanation
    assert judge.retired is None


# ---- a trial whose task got the retirement answer --------------------------------------------------------------------

class _StatusError(Exception):
    """The shape of ``openai.NotFoundError``: ``status_code``, ``body`` (the error object) and the request."""

    def __init__(self, status_code, body, request=None):
        super().__init__(f"Error code: {status_code} - {body!r}")
        self.status_code = status_code
        self.body = body
        self.request = request


def _trial_error(task):
    res = experiments.run([{"id": "a", "input": "hi"}], task, upload=False, progress=False, trace=False)
    (item,) = res.items
    assert item.status == "failed"
    return item.error


def test_a_task_that_got_the_retirement_answer_fails_naming_the_model():
    def task(row):
        raise _StatusError(404, OPENAI_RETIRED["error"])

    err = _trial_error(task)
    assert err.type == "_StatusError"
    assert err.message.startswith("the model 'gpt-4.1-nano' was retired by the provider (HTTP 404 model_not_found")
    assert "Error code: 404" in err.message  # the provider's own text is kept after it


def test_the_model_comes_from_the_request_when_the_message_does_not_name_it():
    request = httpx.Request("POST", "https://api.example.test/v1/chat/completions",
                            json={"model": "old-model-1", "messages": []})
    response = httpx.Response(410, json={"error": {"message": "This model has been retired."}}, request=request)

    def task(row):
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError("the agent's model call failed") from exc  # a framework wrapping the provider error

    err = _trial_error(task)
    assert err.type == "RuntimeError"
    assert err.message.startswith("the model 'old-model-1' was retired by the provider (HTTP 410")


def test_a_real_openai_not_found_error_is_named(monkeypatch):
    openai = pytest.importorskip("openai")
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions", json={"model": "gpt-4.1-nano"})
    response = httpx.Response(404, json=OPENAI_RETIRED, request=request)
    exc = openai.NotFoundError("Error code: 404", response=response, body=OPENAI_RETIRED["error"])
    found = _provider_errors.from_exception(exc)
    assert found is not None and found.model == "gpt-4.1-nano" and found.code == "model_not_found"


def test_an_ordinary_task_error_is_unchanged():
    def task(row):
        raise ValueError("bad input")

    err = _trial_error(task)
    assert err.type == "ValueError" and err.message == "bad input"


# ---- a malformed judge answer is an error cell, never a pass ----------------------------------------------------------

def test_a_malformed_judge_answer_is_an_error_cell_never_a_pass():
    def handler(request):
        body = json.loads(request.content)
        if body["messages"][0]["content"] == CRITERIA_SYSTEM:
            return httpx.Response(200, json=criteria_answer(False))
        if "Hello" in body["messages"][1]["content"]:  # this row's answer holds no verdict
            return httpx.Response(200, json={"model": "m", "usage": {"prompt_tokens": 5, "completion_tokens": 4},
                                             "choices": [{"message": {"content": json.dumps({"status": "ok"})}}]})
        return httpx.Response(200, json=part_verdict(True))

    judge = Judge("Is the reply a JSON object with a status field?", model="m",
                  transport=httpx.MockTransport(handler))
    rows = [{"id": "good", "input": "x", "answer": "{\"status\": \"ok\"}"}, {"id": "bad", "input": "x", "answer": "Hello"}]
    res = experiments.run(rows, experiments.from_column("answer"), [judge], upload=False, progress=False, trace=False)
    by_id = {it.example_id: it.scores["judge"] for it in res.items}
    assert by_id["good"].status == "assessed" and by_id["good"].passed is True
    bad = by_id["bad"]
    assert bad.status == "error" and bad.passed is None and bad.value is None and bad.explanation
    summary = res.summary().evaluators["judge"]
    assert summary.errors == 1 and summary.n == 2
    assert [it.example_id for it in res.items if it.scores["judge"].passed is True] == ["good"]


def test_no_sdk_doc_offers_the_retired_model_by_name():
    """dataset service decisions after wave 2d: "Docs stop offering nano by name." Only the module that explains the retirement
    may name it, as the retired example."""
    from pathlib import Path

    root = Path(experiments.__file__).resolve().parent
    named = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.suffix in (".py", ".md", ".yaml", ".txt")
                   and "__pycache__" not in p.parts and "gpt-4.1-nano" in p.read_text(encoding="utf-8"))
    assert named == ["_provider_errors.py"], named
