"""L-SDK2d review fixes (wave 2d, the checklist judge). No network, no model: an httpx.MockTransport answers.

- M1: a part that asks about correctness on a row with no EXPECTED sees the INPUT. At the recorded revision..the recorded revision the criteria
  read could mark it needs_input=false, and the part was judged on the OUTPUT alone (the reviewer's probe:
  "Is the answer correct?" on "What is 17 * 23?" sent only "391").
- S3: a 429 or 5xx answer is retried (bounded, honouring Retry-After) before it is an error score.
- S4: a run journals its judge's checklist before any row is judged on it; a resume reuses it and reads nothing
  again; a resume with other CRITERIA or another model is refused.
- S5: the metadata's rows_had_expected / expected_shown come from this run's rows, never from an earlier run.
"""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from fi import experiments
from fi.experiments import _judge_checklists
from fi.experiments._dataset import load_local
from fi.experiments._journal import load as load_journal
from fi.experiments.errors import UsageError
from fi.experiments.evaluators import _judge_http
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.judge import CRITERIA_SYSTEM, Judge, Part, part_request, shows_input
from tests.experiments.unit.judge_helpers import criteria_answer, part_verdict

FAKE = "-".join(("judge", "fake", "value"))
CORRECT = [{"part": "Is the answer correct?", "look_at": "the answer", "needs_right_answer": True,
            "needs_input": False, "required": True}]


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


@pytest.fixture
def slept(monkeypatch):
    waits: list = []

    async def fake_sleep(seconds):
        waits.append(seconds)

    monkeypatch.setattr(_judge_http, "_sleep", fake_sleep)
    return waits


def _transport(parts, seen, reads=None, answer=None):
    def handler(request):
        body = json.loads(request.content)
        if body["messages"][0]["content"] == CRITERIA_SYSTEM:
            if reads is not None:
                reads.append(body)
            return httpx.Response(200, json=criteria_answer(True, parts=parts))
        user = body["messages"][1]["content"]
        seen.append(user)
        return answer(user) if answer else httpx.Response(200, json=part_verdict(True))
    return httpx.MockTransport(handler)


def _run(judge, rows, **kw):
    return experiments.run(rows, experiments.from_column("answer"), [judge], upload=False, progress=False,
                           trace=False, **kw)


# ---- M1 -------------------------------------------------------------------------------------------------------------

def test_M1_the_reviewers_probe_a_correctness_part_without_expected_sees_the_input():
    seen = []
    judge = Judge("Is the answer correct?", model="m", transport=_transport(CORRECT, seen))
    row = load_local([{"question": "What is 17 * 23?"}]).rows[0]
    score = asyncio.run(judge.aevaluate(EvalContext(row=row, output="391")))["judge"]
    assert score.status == "assessed" and len(seen) == 1
    assert seen[0] == "PART:\nIs the answer correct?\n\nLOOK AT:\nthe answer\n\nINPUT:\nWhat is 17 * 23?\n\nOUTPUT:\n391"


def test_M1_with_expected_the_same_part_sees_expected_and_not_the_input():
    seen = []
    judge = Judge("Is the answer correct?", model="m", transport=_transport(CORRECT, seen))
    row = load_local([{"question": "What is 17 * 23?", "expected": "391"}]).rows[0]
    asyncio.run(judge.aevaluate(EvalContext(row=row, output="391")))
    assert "INPUT" not in seen[0] and "What is 17 * 23?" not in seen[0] and seen[0].endswith("EXPECTED:\n391")


@pytest.mark.parametrize("needs_right_answer, needs_input, has_expected, shown", [
    (True, False, False, True),    # M1: no reference, so the INPUT
    (True, False, True, False),    # EXPECTED is the reference
    (True, True, True, True),
    (False, False, False, False),  # tone, length, format: the OUTPUT alone, with or without EXPECTED
    (False, False, True, False),
    (False, True, False, True),
])
def test_M1_shows_input(needs_right_answer, needs_input, has_expected, shown):
    part = Part("p", "", needs_right_answer, needs_input, True)
    assert shows_input(part, has_expected) is shown
    text = part_request(part, input_text="THE-INPUT", output_text="o", expected_text="e" if has_expected else None)
    assert ("INPUT:\nTHE-INPUT" in text) is shown


def test_M1_a_run_without_expected_says_its_correctness_part_saw_the_input(capsys):
    judge = Judge("Is the answer correct?", model="m", transport=_transport(CORRECT, []))
    result = experiments.run([{"id": "a", "input": "What is 17 * 23?", "answer": "391"}],
                             experiments.from_column("answer"), [judge], upload=False, trace=False)
    meta = result.metadata["judge_criteria"]["judge"]
    assert (meta["rows_had_expected"], meta["rows_without_expected"], meta["expected_shown"]) == (False, True, False)
    assert "1. Is the answer correct? [OUTPUT, INPUT (the rows have no EXPECTED)]" in capsys.readouterr().err


# ---- S3 -------------------------------------------------------------------------------------------------------------

def _flaky(statuses, headers=None):
    """Answers each part request with the next status of ``statuses`` (then 200), counting the requests."""
    count = {"n": 0}

    def answer(user):
        count["n"] += 1
        if count["n"] <= len(statuses):
            return httpx.Response(statuses[count["n"] - 1], json={"error": {"message": "busy"}}, headers=headers or {})
        return httpx.Response(200, json=part_verdict(True))
    return answer, count


def _one_row(judge):
    row = load_local([{"q": "x", "expected": "y"}]).rows[0]
    ec = EvalContext(row=row, output="o")
    return asyncio.run(judge.aevaluate(ec))["judge"], ec


def test_S3_a_429_is_retried_after_what_retry_after_asks(slept):
    answer, count = _flaky([429], headers={"Retry-After": "2"})
    score, ec = _one_row(Judge("c", model="m", transport=_transport(CORRECT, [], answer=answer)))
    assert score.status == "assessed" and score.passed is True and count["n"] == 2 and slept == [2.0]
    assert len(ec.usage) == 2  # the read and the one answer that came back; the 429 carried no usage


def test_S3_a_5xx_without_retry_after_backs_off_1_2_4(slept):
    answer, count = _flaky([503, 502, 500])
    score, _ = _one_row(Judge("c", model="m", transport=_transport(CORRECT, [], answer=answer)))
    assert score.status == "assessed" and count["n"] == 4 and slept == [1.0, 2.0, 4.0]


def test_S3_retries_are_bounded_then_an_error_score_names_them(slept):
    answer, count = _flaky([429] * 9, headers={"retry-after-ms": "250"})
    score, _ = _one_row(Judge("c", model="m", transport=_transport(CORRECT, [], answer=answer)))
    assert count["n"] == 1 + _judge_http.MAX_RETRIES and slept == [0.25] * _judge_http.MAX_RETRIES
    assert score.status == "error" and "judge HTTP 429 (after 3 retries)" in score.explanation


def test_S3_a_4xx_other_than_429_is_never_retried(slept):
    answer, count = _flaky([400])
    score, _ = _one_row(Judge("c", model="m", transport=_transport(CORRECT, [], answer=answer)))
    assert count["n"] == 1 and slept == [] and score.status == "error" and "judge HTTP 400:" in score.explanation


def test_S3_the_criteria_read_is_retried_too(slept):
    calls = {"read": 0}

    def handler(request):
        if json.loads(request.content)["messages"][0]["content"] == CRITERIA_SYSTEM:
            calls["read"] += 1
            if calls["read"] == 1:
                return httpx.Response(429, json={})
            return httpx.Response(200, json=criteria_answer(True, parts=CORRECT))
        return httpx.Response(200, json=part_verdict(True))

    score, _ = _one_row(Judge("c", model="m", transport=httpx.MockTransport(handler)))
    assert score.status == "assessed" and calls["read"] == 2 and slept == [1.0]


@pytest.mark.parametrize("headers, attempt, want", [
    ({"retry-after-ms": "1500"}, 1, 1.5),
    ({"retry-after": "7"}, 1, 7.0),
    ({"retry-after": "3600"}, 1, _judge_http.RETRY_WAIT_CAP_S),  # capped
    ({"retry-after": "-5"}, 1, 0.0),
    ({"retry-after": "Wed, 21 Oct 2015 07:28:00 GMT"}, 2, 0.0),  # a date in the past: no wait
    ({"retry-after": "soon"}, 3, 4.0),  # unreadable: the backoff
    ({}, 2, 2.0),
])
def test_S3_retry_wait(headers, attempt, want):
    assert _judge_http.retry_wait(httpx.Response(429, headers=headers), attempt) == want


# ---- S4 -------------------------------------------------------------------------------------------------------------

ROWS = [{"id": f"r{i}", "input": f"q{i}", "expected": "x", "answer": "x"} for i in range(3)]


def _drop_last_item(journal_dir: str) -> None:
    """Make a finished run look stopped before its last row (that row's item line goes)."""
    path = Path(journal_dir) / "journal.jsonl"
    lines = path.read_text().splitlines()
    last = max(i for i, ln in enumerate(lines) if json.loads(ln).get("type") == "item")
    path.write_text("\n".join(ln for i, ln in enumerate(lines) if i != last) + "\n")


def test_S4_a_run_journals_its_checklist_without_the_criteria_text():
    judge = Judge("Is the answer right? secret-word", model="m", transport=_transport(CORRECT, []))
    result = _run(judge, ROWS)
    lines = [json.loads(ln) for ln in (Path(result.journal_dir) / "journal.jsonl").read_text().splitlines()]
    marks = [ln for ln in lines if ln["type"] == "judge_checklist"]
    assert len(marks) == 1 and marks[0]["judge"] == "judge" and marks[0]["model"] == "m"
    assert marks[0]["parts"] == CORRECT
    assert marks[0]["criteria_sha256"] == _judge_checklists.criteria_sha256("Is the answer right? secret-word")
    assert "secret-word" not in json.dumps(lines)
    first_item = next(i for i, ln in enumerate(lines) if ln["type"] == "item")
    assert lines.index(marks[0]) < first_item  # journaled before any row's result
    assert load_journal(result.run_id).checklists["judge"]["parts"] == CORRECT


def test_S4_a_resume_judges_the_rest_on_the_journaled_checklist_and_reads_nothing_again():
    first = _run(Judge("Is the answer correct?", model="m", transport=_transport(CORRECT, [])), ROWS)
    _drop_last_item(first.journal_dir)
    other = [{**CORRECT[0], "part": "a different read of the same criteria"}]
    seen, reads = [], []
    again = _run(Judge("Is the answer correct?", model="m", transport=_transport(other, seen, reads)), ROWS,
                 resume=first.run_id)
    assert reads == [] and len(seen) == 1 and seen[0].startswith("PART:\nIs the answer correct?\n")
    assert [i.status for i in again.items] == ["completed"] * 3
    assert again.metadata["judge_criteria"]["judge"]["parts"] == CORRECT
    marks = [ln for ln in (Path(again.journal_dir) / "journal.jsonl").read_text().splitlines()
             if json.loads(ln)["type"] == "judge_checklist"]
    assert len(marks) == 1  # the resume journaled no second checklist


@pytest.mark.parametrize("criteria, model, said", [
    ("Is the answer right?", "m", "its CRITERIA differ"),
    ("Is the answer correct?", "other", "its model is 'other', the run's was 'm'"),
])
def test_S4_a_resume_with_another_judge_is_refused_before_any_request(criteria, model, said):
    first = _run(Judge("Is the answer correct?", model="m", transport=_transport(CORRECT, [])), ROWS)
    _drop_last_item(first.journal_dir)
    seen, reads = [], []
    with pytest.raises(UsageError) as info:
        _run(Judge(criteria, model=model, transport=_transport(CORRECT, seen, reads)), ROWS, resume=first.run_id)
    msg = str(info.value)
    assert said in msg and "start a new run instead" in msg and "nothing was sent" in msg
    assert seen == [] and reads == []


def test_S4_a_resume_of_a_run_stopped_before_its_first_read_reads_and_journals_it():
    first = _run(Judge("Is the answer correct?", model="m", transport=_transport(CORRECT, [])), ROWS)
    path = Path(first.journal_dir) / "journal.jsonl"
    path.write_text("".join(ln + "\n" for ln in path.read_text().splitlines()
                            if json.loads(ln)["type"] not in ("item", "judge_checklist")))
    reads = []
    again = _run(Judge("Is the answer correct?", model="m", transport=_transport(CORRECT, [], reads)), ROWS,
                 resume=first.run_id)
    assert len(reads) == 1 and [i.status for i in again.items] == ["completed"] * 3
    assert load_journal(first.run_id).checklists["judge"]["parts"] == CORRECT


def test_S4_a_judge_reused_for_a_second_run_journals_its_checklist_in_that_run_too():
    reads = []
    judge = Judge("Is the answer correct?", model="m", transport=_transport(CORRECT, [], reads))
    _run(judge, ROWS[:1])
    second = _run(judge, ROWS[1:])
    assert len(reads) == 1  # read once per judge
    assert load_journal(second.run_id).checklists["judge"]["parts"] == CORRECT


# ---- S5 -------------------------------------------------------------------------------------------------------------

def test_S5_a_second_run_of_one_judge_reports_its_own_rows():
    """The reviewer's probe: one judge reused for a run with no expected column reported rows_had_expected=true."""
    judge = Judge("Is the answer correct?", model="m", transport=_transport(CORRECT, []))
    _run(judge, [{"id": "a", "input": "q", "answer": "x", "expected": "x"}])
    second = _run(judge, [{"id": "b", "input": "q", "answer": "y"}])
    meta = second.metadata["judge_criteria"]["judge"]
    assert (meta["rows_had_expected"], meta["expected_shown"], meta["rows_without_expected"]) == (False, False, True)
