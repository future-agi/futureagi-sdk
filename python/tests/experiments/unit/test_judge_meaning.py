"""Replay recorded model exchanges to test paraphrase judgments and how the judge applies criteria.

``fixtures/f8_paraphrase_recorded.json`` holds real model exchanges collected by the end-to-end evaluation.
``fixtures/make_f8_paraphrase_recorded.py`` builds it from the evaluation record:
- ``records``: the F8 guard model (``provenance.model``) on every paraphrase pair: answers with EXPECTED's meaning in
  other words (must pass) and answers in near-identical words with another meaning (a negation, a changed amount or
  number, the opposite answer, swapped roles; must fail), from the 6 development pairs and three held-out sets;
- ``control_records``: every control run in ``provenance.control_runs`` on the criteria controls: ``default`` is
  ``judge(criteria)`` with no ``model=`` (the default judge model), the others name their model. EXPECTED present, the
  CRITERIA about tone, length, privacy, format or language (both directions), so the verdict must not depend on EXPECTED; also
  CONTROL_HELD_OUT_2 and CONTROL_HELD_OUT_3, where the OUTPUT does not fully answer the INPUT (and, in set 3, two-part
  CRITERIA), so the judge must add no requirement the CRITERIA do not state;
- ``criteria_reads``: each run's single read of each criterion, which produces a checklist of parts.
The evaluation checks each seeded control over six seeds and records seed 1. For the lock's judge, it records the
single unseeded run. The fixture keeps the misses from the recorded run. The controls include CONTROL_HELD_OUT_4
(rows with no expected), CONTROL_HELD_OUT_5 (countable criteria) and CONTROL_HELD_OUT_6 (held-out sentence counting
cases). The criteria reader's prompt includes a "list items" example.
Each record stores an exchange in ``parts`` for every part that requires model judgment. The SDK evaluates count-only
parts locally. These tests verify that requests match the recordings byte for byte and that recorded answers replay
to the recorded verdicts. A prompt change requires recording the affected exchanges again with the real model.
The replay itself calls neither the network nor a model.
"""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from fi.experiments._dataset import DatasetSpec, load_local
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.judge import (CRITERIA_SYSTEM, DEFAULT_JUDGE_MODEL, SYSTEM, Judge, parse_part_verdict,
                                             parse_parts, shows_input)

FX = json.loads((Path(__file__).parent / "fixtures" / "f8_paraphrase_recorded.json").read_text(encoding="utf-8"))
RECORDS = FX["records"]
CONTROLS = FX["control_records"]
READS = FX["criteria_reads"]
CRITERIA = FX["provenance"]["criteria"]
MISSES = FX["provenance"]["control_misses_by_model"]
F8_MISSES = FX["provenance"]["f8_misses_by_model"][FX["provenance"]["model"]]
FAKE = "-".join(("judge", "fake", "value"))  # placeholder for the mocked endpoint


def _malformed(rec: dict) -> bool:
    """A recorded part answer holds no verdict (no JSON with a true/false met)."""
    for x in rec["parts"]:
        try:
            parse_part_verdict(x["response"]["choices"][0]["message"]["content"])
        except Exception:
            return True
    return False


def test_the_recording_is_kept_as_the_row_recorded_it():
    """The fixture preserves the evaluation's verdict. The rate gate spans six seeds for seeded runs, so a miss in
    the recorded run does not necessarily fail the gate. The lock's judge has one unseeded run."""
    prov = FX["provenance"]
    failed = set(prov["failed_checks"])
    assert prov["status"] == ("RED" if failed else "GREEN")
    assert failed <= {f"B{n}" for n in range(1, 25)} | {"P3"}
    runs = prov["control_runs"]
    assert set(MISSES) == set(runs) and {"default", "gpt-4.1-mini"} <= set(runs) and "gpt-4.1-nano" not in runs
    assert prov["recorded_seed"]["default"] == "1" and prov["recorded_seed"]["gpt-4.1-mini"] == "1"
    ids = [r["id"] for r in RECORDS]
    assert len(ids) == len(set(ids)) == 36
    assert sum(r["must_pass"] for r in RECORDS) == 18  # 18 must pass, 18 must fail
    assert {r["model"] for r in RECORDS} == {prov["model"]}
    assert {r["run"] for r in CONTROLS} == set(runs)
    per_run = {run: [r for r in CONTROLS if r["run"] == run] for run in runs}
    # CONTROL 9, CONTROL_HELD_OUT 8, _2 8, _3 14, _4 15 (no expected), _5 24 (countable), _6 19 (sentences)
    assert all(len(rs) == 97 and sum(r["must_pass"] for r in rs) == 47 for rs in per_run.values())
    assert {x["model"] for r in per_run["default"] for x in r["parts"]} == {DEFAULT_JUDGE_MODEL}
    for prefix, n in (("ch3-", 14), ("rf-", 15), ("ch5-", 24), ("ch6-", 19)):
        assert sum(r["id"].startswith(prefix) for r in per_run["default"]) == n
    assert all(r["expected"] is None for r in per_run["default"] if r["id"].startswith("rf-"))


def test_the_countable_controls_were_counted_by_code_in_the_recording():
    """Every recorded criteria read for CONTROL_HELD_OUT_5 or _6 identifies a count of sentences, words, characters,
    list items or lines. A part marked count-only has no model exchange."""
    for r in CONTROLS:
        if not r["id"].startswith(("ch5-", "ch6-")):
            continue
        parts = parse_parts(READS[r["run"]][r["criteria"]]["response"]["choices"][0]["message"]["content"])
        assert any(p.count is not None for p in parts), (r["run"], r["criteria"], parts)
        assert len(r["parts"]) == sum(not p.counted_only for p in parts)


def test_the_prompts_are_the_ones_the_real_models_were_recorded_with():
    assert {x["system"] for r in RECORDS + CONTROLS for x in r["parts"]} == {SYSTEM}
    assert {x["system"] for reads in READS.values() for x in reads.values()} == {CRITERIA_SYSTEM}


def test_the_controls_showed_expected_only_to_a_part_that_asks_about_correctness():
    """A recorded request shows EXPECTED if it is available and the part needs the right answer. It shows INPUT if
    the checklist requests it or if the part asks about correctness without an EXPECTED value."""
    for r in CONTROLS:
        parts = parse_parts(READS[r["run"]][r["criteria"]]["response"]["choices"][0]["message"]["content"])
        asked = [p for p in parts if not p.counted_only]  # count-only parts have no model exchange
        assert len(asked) == len(r["parts"])
        has_expected = r["expected"] is not None
        for part, x in zip(asked, r["parts"]):
            assert ("\n\nEXPECTED:\n" in x["user"]) is (part.needs_right_answer and has_expected), (r["run"], r["id"])
            assert ("\n\nINPUT:\n" in x["user"]) is shows_input(part, has_expected), (r["run"], r["id"], part)


def _replay(rec: dict, criteria: str, monkeypatch) -> tuple:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    run = rec.get("run", rec["model"])  # F8 records carry the guard model only
    read = READS[run][criteria]
    by_user = {x["user"]: x for x in rec["parts"]}
    sent: list = []
    models: list = []  # the model each request names

    def handler(request):
        body = json.loads(request.content)
        sent.append(body["messages"])
        models.append(body["model"])
        if body["messages"][0]["content"] == CRITERIA_SYSTEM:
            x = read
        else:
            x = by_user[body["messages"][1]["content"]]  # a KeyError means the SDK built a request absent from the recordings
        return httpx.Response(x["status"], json=x["response"])

    transport = httpx.MockTransport(handler)
    judge = (Judge(criteria, transport=transport) if run == "default"
             else Judge(criteria, model=rec["model"], transport=transport))
    # Reproduce the evaluation row with experiments.from_column("answer") over {id, input, expected, answer}.
    raw = {"id": rec["id"], "input": rec["input"], "answer": rec["output"]}
    if rec["expected"] is not None:  # CONTROL_HELD_OUT_4's rows have no expected column
        raw["expected"] = rec["expected"]
    row = load_local(DatasetSpec([raw], exclude_expected="answer")).rows[0]
    ec = EvalContext(row=row, output=rec["output"], output_column="answer")
    score = asyncio.run(judge.aevaluate(ec))["judge"]
    assert sent[0] == [{"role": "system", "content": read["system"]}, {"role": "user", "content": read["user"]}]
    want = sorted(json.dumps([{"role": "system", "content": x["system"]}, {"role": "user", "content": x["user"]}])
                  for x in rec["parts"])
    assert sorted(json.dumps(m) for m in sent[1:]) == want  # one request per part, each exactly as recorded
    assert set(models) == {rec["model"]}  # the default run sends DEFAULT_JUDGE_MODEL
    return score


@pytest.mark.parametrize("rec", RECORDS, ids=[r["id"] for r in RECORDS])
def test_recorded_verdicts_same_meaning_passes_different_meaning_fails(rec, monkeypatch):
    """Each F8 pair replays to its recorded verdict: right, except a miss of the recorded run (the rate gate allows a
    miss in 6 seeded runs; none is expected, and every one is listed in the provenance)."""
    score = _replay(rec, CRITERIA, monkeypatch)
    missed = rec["id"] in F8_MISSES
    assert score.status == "assessed" and score.passed is (rec["must_pass"] is not missed), score


@pytest.mark.parametrize("rec", CONTROLS, ids=[f"{r['run']}-{r['id']}" for r in CONTROLS])
def test_recorded_controls_the_criteria_decide_never_expected(rec, monkeypatch):
    """Each control replays to its recorded verdict: right, except a miss the row recorded for that run; a recorded
    answer without a verdict replays to an error score."""
    score = _replay(rec, rec["criteria"], monkeypatch)
    if _malformed(rec):
        assert score.status == "error" and score.passed is None and rec["id"] in MISSES[rec["run"]], score
        return
    missed = rec["id"] in MISSES[rec["run"]]
    assert score.status == "assessed" and score.passed is (rec["must_pass"] is not missed), score
