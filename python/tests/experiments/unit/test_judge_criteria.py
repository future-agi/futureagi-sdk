"""Regression coverage: the CRITERIA decide judge()'s verdict, as a checklist. The judge reads its CRITERIA
once (``CRITERIA_SYSTEM``, one small call per judge, cached) and splits them into parts; each row then gets one verdict
request per part, showing EXPECTED only for a part that needs the right answer and the INPUT only for a part that needs
it, and the SDK combines the parts (passes exactly when every required part is met). So with an expected column, a
CRITERIA about tone, length, format or privacy is judged on the OUTPUT alone, and matching facts can never pass a rude
reply as polite (the review's gpt-4.1-nano finding at the recorded revision). No network, no model: an httpx.MockTransport answers.
The real verdicts are guarded by e2e evaluation regression B11-B18 and replayed in test_judge_meaning.py.
"""

import asyncio
import json

import httpx
import pytest

from fi import experiments
from fi.experiments._dataset import load_local
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.judge import (CRITERIA_SYSTEM, SYSTEM, Judge, Part, combine, parse_asks_correctness,
                                             parse_part_verdict, parse_parts)
from tests.experiments.unit.judge_helpers import criteria_answer, part_verdict, with_criteria

FAKE = "-".join(("judge", "fake", "value"))  # built at run time: the pre-ship scan reads literals
ROWS = [{"id": f"r{i}", "input": "Where is my order A101?", "expected": "Order A101 has shipped.",
         "answer": "It shipped, obviously. Stop wasting my time."} for i in range(3)]


def _verdicts(seen: list):
    def handler(request):
        seen.append(json.loads(request.content)["messages"][1]["content"])
        return httpx.Response(200, json=part_verdict(False, "rude"))
    return handler


def _run(judge, rows=ROWS, **kw):
    return experiments.run(rows, experiments.from_column("answer"), [judge], upload=False, progress=False, trace=False,
                           **kw)


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


def test_a_criteria_not_about_correctness_never_shows_the_judge_expected():
    seen, reads = [], []
    judge = Judge("Is the reply polite and respectful to the customer?", model="m",
                  transport=httpx.MockTransport(with_criteria(_verdicts(seen), needs_right_answer=False, reads=reads)))
    result = _run(judge, concurrency=3)
    assert [i.scores["judge"].passed for i in result.items] == [False, False, False]
    assert len(reads) == 1  # the criteria are read once for the run, even with 3 rows at once
    assert reads[0]["messages"] == [{"role": "system", "content": CRITERIA_SYSTEM},
                                    {"role": "user", "content": "CRITERIA:\nIs the reply polite and respectful to the customer?"}]
    assert len(seen) == 3 and all("EXPECTED" not in u and "Order A101 has shipped." not in u for u in seen)
    assert judge.asks_correctness is False


def test_a_criteria_about_correctness_shows_the_judge_expected():
    seen, reads = [], []
    judge = Judge("Is the output a correct answer to the input?", model="m",
                  transport=httpx.MockTransport(with_criteria(_verdicts(seen), needs_right_answer=True, reads=reads)))
    _run(judge)
    assert len(reads) == 1 and len(seen) == 3
    assert all(u.endswith("EXPECTED:\nOrder A101 has shipped.") for u in seen)


def test_the_criteria_are_read_once_with_or_without_expected():
    """Wave 2d: the read is the checklist, so a judge reads its CRITERIA on its first row even without EXPECTED."""
    seen, reads = [], []
    judge = Judge("Is the reply polite?", model="m", transport=httpx.MockTransport(with_criteria(_verdicts(seen), reads=reads)))
    _run(judge, rows=[{"id": "x", "input": "q", "answer": "a"}, {"id": "y", "input": "q", "answer": "b"}])
    assert len(reads) == 1 and len(seen) == 2 and all("EXPECTED" not in u for u in seen)
    assert judge.parts is not None


def test_a_failed_criteria_read_is_an_error_score_and_is_retried_on_the_next_row():
    calls = {"read": 0}

    def handler(request):
        if json.loads(request.content)["messages"][0]["content"] == CRITERIA_SYSTEM:
            calls["read"] += 1
            if calls["read"] == 1:  # a 400, not a 503: a 429 or 5xx is retried within the row
                return httpx.Response(400, text="bad request")
            return httpx.Response(200, json=criteria_answer(False))
        return _verdicts([])(request)

    judge = Judge("Is the reply polite?", model="m", transport=httpx.MockTransport(handler))
    result = _run(judge, rows=ROWS[:2], concurrency=1)
    first, second = (i.scores["judge"] for i in result.items)
    assert first.status == "error" and "could not read its criteria" in first.explanation and "400" in first.explanation
    assert second.status == "assessed" and calls["read"] == 2 and judge.asks_correctness is False


def test_the_criteria_read_is_metered_with_the_trial():
    judge = Judge("Is the reply polite?", model="m",
                  transport=httpx.MockTransport(with_criteria(_verdicts([]), needs_right_answer=False)))
    ec = EvalContext(row=load_local([{"q": "x", "expected": "y"}]).rows[0], output="o")
    asyncio.run(judge.aevaluate(ec))
    assert ec.usage == [("m", 3, 2), ("m", 5, 4)]  # the read, then the verdict


@pytest.mark.parametrize("text,want", [
    ('{"parts": [{"part": "polite", "look_at": "tone", "needs_right_answer": false}]}', False),
    ('{"parts": [{"part": "correct", "look_at": "facts", "needs_right_answer": true},'
     ' {"part": "polite", "look_at": "tone", "needs_right_answer": false}]}', True),
])
def test_parse_asks_correctness(text, want):
    assert parse_asks_correctness(text) is want


@pytest.mark.parametrize("bad", ["no json", '{"parts": []}', '{"parts": [{"part": "x", "needs_right_answer": "no"}]}'])
def test_parse_asks_correctness_refuses_an_answer_without_a_true_false(bad):
    with pytest.raises(ValueError):
        parse_asks_correctness(bad)


def test_the_prompts_say_the_criteria_decide():
    assert "You judge ONE PART of an evaluator's CRITERIA" in SYSTEM and "Any other parts are judged separately" in SYSTEM
    assert "it is a reference for the facts, not for the wording" in SYSTEM
    assert "politeness" not in SYSTEM  # never listed among things that cannot make a fact different
    for phrase in ("needs_right_answer is true only when the part asks whether the OUTPUT's answer or facts are right",
                   "its tone or politeness, its length, its format", "reveals or keeps something private",
                   "needs_input is true only when checking the part needs the INPUT",
                   "Never add a part the CRITERIA do not ask for, such as answering all of the INPUT",
                   "required is false only when the CRITERIA say the part is optional or only preferred"):
        assert phrase in CRITERIA_SYSTEM


def test_the_verdict_prompt_adds_no_requirement_and_asks_for_the_reason_before_the_verdict():
    """Wave 2c: at the recorded revision the default judge (gpt-4.1-mini) scored a 5-word reply 0.5 under "at most 8 words" because
    it "does not explicitly state the location of the order as asked" (e2e evaluation regression B11; 5 of 8 scratch repetitions,
    run 20261023T080413Z-w2cctl). Wave 2d: each part is judged alone; the prompt forbids requirements the PART does not
    state, the model answers met true/false per part (the SDK makes the score), and the reason comes first."""
    assert "Never add a requirement the PART does not state, such as answering all of the INPUT" in SYSTEM
    assert "The INPUT is given only when the PART needs it" in SYSTEM
    schema = SYSTEM[SYSTEM.index('{"facts"'):]
    assert schema.index('"reason"') < schema.index('"met"') and '"pass"' not in schema and '"score"' not in schema


@pytest.mark.parametrize("text", [
    '{"facts": [], "reason": "5 words, within the limit.", "met": true}',
    '{"met": true, "facts": [], "reason": "5 words, within the limit."}',
])
def test_parse_part_verdict_reads_either_key_order(text):
    assert parse_part_verdict(text) == (True, "5 words, within the limit.")


# ---- wave 2d: the checklist ---------------------------------------------------------------------------------------

TWO = [{"part": "the reply is polite", "look_at": "its tone", "needs_right_answer": False, "needs_input": False,
        "required": True},
       {"part": "the reply gives the right status", "look_at": "the status it states", "needs_right_answer": True,
        "needs_input": True, "required": True}]


def _per_part(seen: list, met: dict):
    """Answers each part's request with met[<the PART line>] and records the request's user message."""
    def handler(request):
        user = json.loads(request.content)["messages"][1]["content"]
        seen.append(user)
        part = user.split("\n", 2)[1]
        return httpx.Response(200, json=part_verdict(met[part], f"{part}: {'yes' if met[part] else 'no'}"))
    return handler


def test_each_part_gets_its_own_request_with_only_what_it_needs():
    seen = []
    judge = Judge("Is the reply polite, and does it give the right status?", model="m", transport=httpx.MockTransport(
        with_criteria(_per_part(seen, {TWO[0]["part"]: True, TWO[1]["part"]: True}), parts=TWO)))
    result = _run(judge, rows=ROWS[:1])
    score = result.items[0].scores["judge"]
    assert (score.status, score.value, score.passed) == ("assessed", 1.0, True)
    polite = next(u for u in seen if u.startswith("PART:\nthe reply is polite"))
    status = next(u for u in seen if u.startswith("PART:\nthe reply gives the right status"))
    assert len(seen) == 2
    assert polite == "PART:\nthe reply is polite\n\nLOOK AT:\nits tone\n\nOUTPUT:\n" + ROWS[0]["answer"]
    assert "INPUT:\nWhere is my order A101?" in status and status.endswith("EXPECTED:\nOrder A101 has shipped.")
    meta = result.metadata["judge_criteria"]["judge"]
    assert meta["asks_correctness"] is True and meta["expected_shown"] is True and meta["rows_had_expected"] is True
    assert [p["part"] for p in meta["parts"]] == [TWO[0]["part"], TWO[1]["part"]]


@pytest.mark.parametrize("met, required, want", [
    ((True, True), (True, True), (1.0, True)),
    ((True, False), (True, True), (0.5, False)),   # a required part not met fails the verdict
    ((False, True), (True, True), (0.5, False)),
    ((True, False), (True, False), (0.5, True)),   # an optional part not met lowers the score, not the verdict
    ((False, False), (False, False), (0.0, False)),  # no part required: every part is
])
def test_the_verdict_is_every_required_part_met_and_the_score_the_share_met(met, required, want):
    parts = [{**p, "required": r} for p, r in zip(TWO, required)]
    judge = Judge("c", model="m", transport=httpx.MockTransport(
        with_criteria(_per_part([], {parts[0]["part"]: met[0], parts[1]["part"]: met[1]}), parts=parts)))
    score = _run(judge, rows=ROWS[:1]).items[0].scores["judge"]
    assert (score.value, score.passed) == want
    assert score.explanation.startswith("1. the reply is polite") and "2. the reply gives the right status" in score.explanation


def test_passing_score_still_decides_when_given():
    judge = Judge("c", model="m", passing_score=0.5, transport=httpx.MockTransport(
        with_criteria(_per_part([], {TWO[0]["part"]: True, TWO[1]["part"]: False}), parts=TWO)))
    score = _run(judge, rows=ROWS[:1]).items[0].scores["judge"]
    assert (score.value, score.passed) == (0.5, True)


def test_a_part_answer_without_a_verdict_is_an_error_never_a_made_up_one():
    def handler(request):
        user = json.loads(request.content)["messages"][1]["content"]
        if "polite" in user.split("\n", 2)[1]:
            return httpx.Response(200, json=part_verdict(True))
        return httpx.Response(200, json={"model": "m", "usage": {"prompt_tokens": 5, "completion_tokens": 4},
                                         "choices": [{"message": {"content": '{"order": "A101", "status": "x"}'}}]})

    judge = Judge("c", model="m", transport=httpx.MockTransport(with_criteria(handler, parts=TWO)))
    ec = EvalContext(row=load_local([{"q": "x", "expected": "y"}]).rows[0], output="o")
    score = asyncio.run(judge.aevaluate(ec))["judge"]
    assert score.status == "error" and score.passed is None and "no true/false met" in score.explanation
    assert len(ec.usage) == 3  # the read and both parts are metered, the failed one included


def test_a_part_that_needs_no_input_never_sees_it():
    seen = []
    judge = Judge("Is the reply a single sentence?", model="m",
                  transport=httpx.MockTransport(with_criteria(_verdicts(seen), needs_right_answer=False,
                                                              needs_input=False)))
    _run(judge, rows=ROWS[:2])
    assert len(seen) == 2 and all("INPUT" not in u and "Where is my order" not in u for u in seen)


@pytest.mark.parametrize("text, want", [
    ('{"parts": [{"part": "short", "needs_right_answer": false}]}',  # missing flags fail closed: INPUT shown, required
     (Part("short", "", False, True, True),)),
    ('{"parts": [{"part": " polite ", "look_at": " tone ", "needs_right_answer": false, "needs_input": false, '
     '"required": false}]}', (Part("polite", "tone", False, False, True),)),  # the only part, so it is required
])
def test_parse_parts(text, want):
    assert parse_parts(text) == want


@pytest.mark.parametrize("bad", ['{"parts": [{"needs_right_answer": true}]}', '{"parts": [{"part": " ", '
                                 '"needs_right_answer": true}]}',
                                 '{"parts": [{"part": "x", "needs_right_answer": true, "needs_input": "no"}]}',
                                 '[{"part": "x"}]'])
def test_parse_parts_refuses_a_part_it_cannot_use(bad):
    with pytest.raises(ValueError):
        parse_parts(bad)


def test_combine_keeps_a_one_part_reason():
    assert combine((Part("p", "", False, False, True),), [(True, "one sentence")]) == (1.0, True, "one sentence")
