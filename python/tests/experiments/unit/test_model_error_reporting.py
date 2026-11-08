"""L-SDK2e review fixes (no network, no model: an httpx transport answers locally).

- M1: a retirement word counts only when it is about a model. A provider also deprecates parameters and endpoints
  (OpenAI's 400 "The 'functions' parameter is deprecated"), and such an answer stays the provider's own error: the
  judge says "judge HTTP 400" and keeps calling, a trial's message is unchanged.
- S1: the run's closing lines say each evaluator's distinct error once, a retirement first ("judge: 3 errors: the
  model 'gpt-4.1-nano' was retired by the provider ..."), and the same for the trials' errors.
- S2: under concurrency one retirement answer is the only call to the retired model; the judge keys it by endpoint
  and model, so a reused judge whose OPENAI_BASE_URL changed calls the new endpoint.
"""

import asyncio
import json

import httpx
import pytest

from fi import experiments
from fi.experiments import _provider_errors
from fi.experiments._dataset import load_local
from fi.experiments._engine_summary import SHOWN_ERRORS, print_summary
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.judge import CRITERIA_SYSTEM, Judge
from fi.experiments.results import EvalScore, ExperimentResult, TrialError, TrialResult
from tests.experiments.unit.judge_helpers import criteria_answer, part_verdict

FAKE = "-".join(("judge", "fake", "value"))
OPENAI_RETIRED = {"error": {"message": "The model `gpt-4.1-nano` has been deprecated, learn more here: "
                                       "https://platform.openai.com/docs/deprecations",
                            "type": "invalid_request_error", "param": None, "code": "model_not_found"}}
# the review's probe answers (cache/l-sdk2e-review/probe/probe_retired.py): deprecations of a parameter or an endpoint
PARAMETER = (400, {"error": {"message": "The 'functions' parameter is deprecated. Please use 'tools' instead.",
                             "type": "invalid_request_error", "param": "functions", "code": None}})
ENDPOINT_PARAMETER = (400, {"error": {"message": "'max_tokens' is deprecated for this endpoint; use "
                                                 "'max_completion_tokens'", "type": "invalid_request_error",
                                      "param": "max_tokens", "code": "unsupported_parameter"}})
ENDPOINT = (404, {"error": {"message": "The endpoint /v1/engines is deprecated and no longer available",
                            "type": "invalid_request_error"}})
NOT_ABOUT_A_MODEL = [PARAMETER, ENDPOINT_PARAMETER, ENDPOINT]
ROW = load_local([{"question": "where is my order?"}]).rows[0]


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


# ---- M1 -------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("status,body", NOT_ABOUT_A_MODEL)
@pytest.mark.parametrize("model", [None, "gpt-4.1-mini", "m"])  # "m": a short id is not any word's letter
def test_a_parameter_or_endpoint_deprecation_is_not_a_retirement(status, body, model):
    assert _provider_errors.retirement(status, body, model=model) is None


@pytest.mark.parametrize("status,body", NOT_ABOUT_A_MODEL)
def test_the_judge_keeps_a_parameter_or_endpoint_deprecation_as_the_providers_error(status, body):
    calls: list = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json=body)

    judge = Judge("Is the reply polite?", model="gpt-4.1-mini", transport=httpx.MockTransport(handler))
    first = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="It shipped.")))["judge"]
    assert first.status == "error" and f"judge HTTP {status}" in first.explanation
    assert "retired" not in first.explanation and judge.retired is None
    asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="It shipped.")))
    assert len(calls) == 2  # not marked retired: the next row calls again


def test_a_trials_parameter_deprecation_message_is_unchanged():
    status, body = PARAMETER

    class StatusError(Exception):
        def __init__(self):
            super().__init__(f"Error code: {status} - {body['error']!r}")
            self.status_code, self.body = status, body["error"]

    def task(row):
        raise StatusError()

    res = experiments.run([{"id": "a", "input": "hi"}], task, upload=False, progress=False, trace=False)
    assert res.items[0].error.message.startswith("Error code: 400")
    assert "retired" not in res.items[0].error.message


@pytest.mark.parametrize("status,body,model,named", [
    (404, OPENAI_RETIRED, None, "gpt-4.1-nano"),                                   # the message names it
    (404, {"error": {"message": "gpt-old-1 has been retired."}}, "gpt-old-1", "gpt-old-1"),  # names the request's
    (410, {"error": {"message": "This model has been retired."}}, None, None),     # "this model" is the subject
    (400, {"error": {"code": "model_decommissioned", "message": "decommissioned"}}, "g", "g"),  # a retirement code
    (400, {"error": {"code": "model_not_found", "message": "The model `x-1` has been deprecated"}}, None, "x-1"),
])
def test_a_retirement_about_a_model_is_still_found(status, body, model, named):
    found = _provider_errors.retirement(status, body, model=model)
    assert found is not None and found.model == named


def test_a_404_whose_word_names_another_thing_but_the_requested_model_is_elsewhere_is_not_a_retirement():
    body = {"error": {"message": "The endpoint /v1/engines is deprecated; use /v1/chat/completions"}}
    assert _provider_errors.retirement(404, body, model="engines") is None  # "/v1/engines" is a path, not the id


# ---- S2 -------------------------------------------------------------------------------------------------------------

class _Slow(httpx.AsyncBaseTransport):
    """Answers every request after a delay, counting the calls (the review's probe transport)."""

    def __init__(self, status, body, delay=0.2):
        self.calls, self.status, self.body, self.delay = 0, status, body, delay

    async def handle_async_request(self, request):
        self.calls += 1
        await asyncio.sleep(self.delay)
        return httpx.Response(self.status, json=self.body)


def test_under_concurrency_one_retirement_answer_is_the_only_call():
    slow = _Slow(404, OPENAI_RETIRED)
    judge = Judge("Is the reply polite?", model="gpt-4.1-nano", transport=slow)
    rows = [{"id": str(i), "input": "hi", "answer": "Hello!"} for i in range(8)]
    res = experiments.run(rows, experiments.from_column("answer"), [judge], upload=False, progress=False,
                          trace=False, concurrency=8)
    assert slow.calls == 1
    assert all("the model 'gpt-4.1-nano' was retired by the provider" in it.scores["judge"].explanation
               for it in res.items)


def test_a_part_call_answered_retired_stops_every_later_rows_calls():
    """The checklist was read (the model served it), then a part call is answered retired: no row calls again."""
    seen = {"parts": 0}

    class Transport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            body = json.loads(request.content)
            if body["messages"][0]["content"] == CRITERIA_SYSTEM:
                return httpx.Response(200, json=criteria_answer(False))
            seen["parts"] += 1
            await asyncio.sleep(0.1)
            return httpx.Response(404, json=OPENAI_RETIRED)

    judge = Judge("Is the reply polite?", model="gpt-4.1-nano", transport=Transport())

    async def go():
        first = await judge.aevaluate(EvalContext(row=ROW, output="a"))  # reads the checklist, then the part: retired
        later = await asyncio.gather(*(judge.aevaluate(EvalContext(row=ROW, output="b")) for _ in range(5)))
        return first, later

    first, later = asyncio.run(go())
    assert seen["parts"] == 1 and "was retired by the provider" in first["judge"].explanation
    assert all("was retired by the provider" in s["judge"].explanation for s in later)


def test_the_retirement_is_kept_per_endpoint(monkeypatch):
    hosts: list = []

    def handler(request):
        hosts.append(request.url.host)
        if request.url.host == "old.example.test":
            return httpx.Response(404, json=OPENAI_RETIRED)
        body = json.loads(request.content)
        if body["messages"][0]["content"] == CRITERIA_SYSTEM:
            return httpx.Response(200, json=criteria_answer(False))
        return httpx.Response(200, json=part_verdict(True))

    monkeypatch.setenv("OPENAI_BASE_URL", "https://old.example.test/v1")
    judge = Judge("Is the reply polite?", model="gpt-4.1-nano", transport=httpx.MockTransport(handler))
    first = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="Hello!")))["judge"]
    assert "was retired by the provider at old.example.test (HTTP" in first.explanation and judge.retired is not None
    monkeypatch.setenv("OPENAI_BASE_URL", "https://new.example.test/v1")
    assert judge.retired is None  # another endpoint: not known retired there
    second = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="Hello!")))["judge"]
    assert second.status == "assessed" and second.passed is True
    assert hosts[0] == "old.example.test" and set(hosts[1:]) == {"new.example.test"}
    monkeypatch.setenv("OPENAI_BASE_URL", "https://old.example.test/v1")
    assert judge.retired is not None  # back on the old endpoint: still known retired, no call
    asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="Hello!")))
    assert hosts.count("old.example.test") == 1


# ---- S1 -------------------------------------------------------------------------------------------------------------

def test_the_closing_lines_name_the_retired_judge_model_once(capsys):
    judge = Judge("Is the reply polite?", model="gpt-4.1-nano",
                  transport=httpx.MockTransport(lambda r: httpx.Response(404, json=OPENAI_RETIRED)))
    rows = [{"id": str(i), "input": "hi", "answer": "Hello!"} for i in range(3)]
    experiments.run(rows, experiments.from_column("answer"), [judge], upload=False, progress=True, trace=False)
    err = capsys.readouterr().err
    summary = err[err.index("Done     "):]
    lines = [ln for ln in summary.splitlines() if ln.startswith("  judge: ")]
    assert len(lines) == 1, lines
    assert lines[0].startswith("  judge: 3 errors: the model 'gpt-4.1-nano' was retired by the provider "
                               "at api.openai.com (HTTP 404 model_not_found")
    assert lines[0].endswith("a retired model can still be listed by the provider's /models call.")


def test_the_closing_lines_name_the_retired_model_of_the_trials(capsys):
    class StatusError(Exception):
        def __init__(self):
            super().__init__("Error code: 404")
            self.status_code, self.body = 404, OPENAI_RETIRED["error"]

    def task(row):
        raise StatusError()

    experiments.run([{"id": "a", "input": "hi"}, {"id": "b", "input": "ho"}], task, upload=False, progress=True,
                    trace=False)
    err = capsys.readouterr().err
    summary = err[err.index("Done     "):].splitlines()
    assert "  2 × StatusError" in summary
    said = [ln for ln in summary if ln.startswith("  StatusError: ")]
    assert len(said) == 1 and said[0].startswith(
        "  StatusError: 2 errors: the model 'gpt-4.1-nano' was retired by the provider (HTTP 404 model_not_found")


def _result(scores, errors=()):
    items = [TrialResult(example_id=str(i), number=i, trial=0, status="completed", scores={"judge": sc})
             for i, sc in enumerate(scores)]
    items += [TrialResult(example_id=f"e{i}", number=100 + i, trial=0, status="failed", error=err)
              for i, err in enumerate(errors)]
    return ExperimentResult(run_id="r", name="n", status="completed", items=items, journal_dir="j")


def test_each_distinct_error_is_said_once_with_its_count_and_the_rest_counted():
    texts = ["ValueError: a"] * 3 + ["ValueError: b"] * 2 + ["RuntimeError: c", "RuntimeError: d", "KeyError: e"]
    lines: list = []
    print_summary(lines.append, _result([EvalScore(status="error", explanation=t) for t in texts]
                                        + [EvalScore(1.0, passed=True)]))
    said = [ln for ln in lines if ln.startswith("  judge: ")]
    assert said[:SHOWN_ERRORS] == ["  judge: 3 errors: ValueError: a", "  judge: 2 errors: ValueError: b",
                                   "  judge: 1 error: KeyError: e"]
    assert said[SHOWN_ERRORS:] == ["  judge: 2 other distinct errors (each row's own is in its score or error)"]
    assert len(said) == SHOWN_ERRORS + 1


def test_a_run_with_no_errors_prints_no_error_lines_and_a_trial_error_says_its_message():
    lines: list = []
    print_summary(lines.append, _result([EvalScore(1.0, passed=True)],
                                        [TrialError(type="ValueError", message="bad input\nmore")]))
    assert not [ln for ln in lines if ln.startswith("  judge: ")]
    assert "  1 × ValueError" in lines and "  ValueError: 1 error: bad input" in lines


def test_the_printed_error_texts_go_through_the_runs_redactor():
    lines: list = []
    secret = "-".join(("not", "a", "real", "key", "123"))
    print_summary(lines.append, _result([EvalScore(status="error", explanation=f"judge HTTP 401: bad key {secret}")]),
                  redact=lambda text: text.replace(secret, "[REDACTED]"))
    assert "  judge: 1 error: judge HTTP 401: bad key [REDACTED]" in lines
    assert not any(secret in ln for ln in lines)
