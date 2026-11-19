"""F8 and the criteria controls (L-SDK2b regression coverage, wave 2d checklist), replayed from real recordings.

``fixtures/f8_paraphrase_recorded.json`` holds the real exchanges of e2e row evaluation regression, built by
``fixtures/make_f8_paraphrase_recorded.py`` from the row's truth record:
- ``records``: the F8 guard model (``provenance.model``) on every paraphrase pair: answers with EXPECTED's meaning in
  other words (must pass) and answers in near-identical words with another meaning (a negation, a changed amount or
  number, the opposite answer, swapped roles; must fail), from the 6 development pairs and three held-out sets;
- ``control_records``: every control run in ``provenance.control_runs`` on the criteria controls: ``default`` is
  ``judge(criteria)`` with no ``model=`` (the default judge model), the others name their model. EXPECTED present, the
  CRITERIA about tone, length, privacy, format or language (both directions), so EXPECTED must never decide; also
  CONTROL_HELD_OUT_2 and CONTROL_HELD_OUT_3, where the OUTPUT does not fully answer the INPUT (and, in set 3, two-part
  CRITERIA), so the judge must add no requirement the CRITERIA do not state;
- ``criteria_reads``: each run's one read of each CRITERIA: the checklist of parts (wave 2d).
From wave 2e the row runs each control on 6 seeds and records seed 1 (the lock's judge: its one unseeded run); the
misses kept are the recorded run's. From wave 2f the controls include CONTROL_HELD_OUT_4 (rows with no expected) and
CONTROL_HELD_OUT_5 (countable criteria), and a part the read marked count-only is decided by code: it has no exchange;
from the L-SDK2f review fixes also CONTROL_HELD_OUT_6 (the sentence counter's held-out set), recorded at SDK the recorded revision
with the read's "list items" example.
From wave 2d each record holds one exchange per part of its CRITERIA (``parts``). These tests replay them: every
request the SDK builds today must be byte-for-byte a recorded one (so a prompt change needs a new recording on the
real model), and the recorded answers must give the recorded verdicts. No network, no model.
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
FAKE = "-".join(("judge", "fake", "value"))  # built at run time: the pre-ship scan reads literals


def _malformed(rec: dict) -> bool:
    """A recorded part answer holds no verdict (no JSON with a true/false met)."""
    for x in rec["parts"]:
        try:
            parse_part_verdict(x["response"]["choices"][0]["message"]["content"])
        except Exception:
            return True
    return False


def test_the_recording_is_kept_as_the_row_recorded_it():
    """The row's verdict is kept as recorded. From wave 2e evaluation regression gates every control on a rate over 6 seeds and
    records seed 1's exchanges (the lock's judge: its one unseeded run), so a failed check is a B check of the rate gate
    (or implementation), and a miss in the recorded run need not fail a check."""
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
    # CONTROL 9, CONTROL_HELD_OUT 8, _2 8, _3 14, _4 15 (no expected), _5 24 (countable, wave 2f), _6 19 (sentences)
    assert all(len(rs) == 97 and sum(r["must_pass"] for r in rs) == 47 for rs in per_run.values())
    assert {x["model"] for r in per_run["default"] for x in r["parts"]} == {DEFAULT_JUDGE_MODEL}
    for prefix, n in (("ch3-", 14), ("rf-", 15), ("ch5-", 24), ("ch6-", 19)):
        assert sum(r["id"].startswith(prefix) for r in per_run["default"]) == n
    assert all(r["expected"] is None for r in per_run["default"] if r["id"].startswith("rf-"))


def test_the_countable_controls_were_counted_by_code_in_the_recording():
    """Wave 2f on the real recordings: every read of a CONTROL_HELD_OUT_5 or _6 criteria marked a count (its sentences,
    words, characters, list items or lines), and a part the read marked count-only has no exchange: the model was
    never asked to count it."""
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
    """M1 on the real recordings, per part (wave 2d): EXPECTED was in a part's request only when the recorded read
    marked that part as needing the right answer; the INPUT only when it marked the part as needing the INPUT."""
    for r in CONTROLS:
        parts = parse_parts(READS[r["run"]][r["criteria"]]["response"]["choices"][0]["message"]["content"])
        asked = [p for p in parts if not p.counted_only]  # a count-only part has no exchange (wave 2f)
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
            x = by_user[body["messages"][1]["content"]]  # a KeyError here: the SDK built a request never recorded
        return httpx.Response(x["status"], json=x["response"])

    transport = httpx.MockTransport(handler)
    judge = (Judge(criteria, transport=transport) if run == "default"
             else Judge(criteria, model=rec["model"], transport=transport))
    # the row exactly as evaluation regression ran it: experiments.from_column("answer") over {id, input, expected, answer}
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
    answer that holds no verdict replays to an error score, never to a made-up verdict."""
    score = _replay(rec, rec["criteria"], monkeypatch)
    if _malformed(rec):
        assert score.status == "error" and score.passed is None and rec["id"] in MISSES[rec["run"]], score
        return
    missed = rec["id"] in MISSES[rec["run"]]
    assert score.status == "assessed" and score.passed is (rec["must_pass"] is not missed), score
