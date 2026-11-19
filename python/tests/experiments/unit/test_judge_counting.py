"""Wave 2f: a countable part of a judge()'s CRITERIA is decided by code, never the model.

No network, no model: an httpx transport answers the criteria read and every verdict request locally, and records
which requests were made, so a test can prove the model was never asked to count.
"""

import asyncio
import json

import httpx
import pytest

from fi.experiments import _judge_checklists
from fi.experiments._dataset import load_local
from fi.experiments._engine_summary import _part_line
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators._judge_count import Count, count_units, decide, parse_count, sentences
from fi.experiments.evaluators._judge_prompt import CRITERIA_SYSTEM, Part, parse_parts, part_request
from fi.experiments.evaluators.judge import Judge
from tests.experiments.unit.judge_helpers import part_verdict, with_criteria

FAKE = "-".join(("judge", "fake", "value"))
ROW = load_local([{"question": "Is flight LX318 on time, and which gate does it leave from?",
                   "expected": "Flight LX318 is on time and leaves from gate B12."}]).rows[0]
ONE_SENTENCE = {"unit": "sentences", "compare": "exactly", "n": 1, "only": True}


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


# ---- the counters ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("text,n", [
    ("Flight LX318 is on time and leaves from gate B12.", 1),  # ch3-gate-right-one-sentence: one sentence, never two
    ("Flight LX318 is on time. It leaves from gate B12.", 2),
    ("Dr. Patel will see you on Monday at 10 am, and please bring your insurance card.", 1),
    ("Your refund of $42.50 for order R808 has been approved. It arrives within 5 business days.", 2),
    ("Thanks for checking! Flight LX318 is on time.", 2),
    ("Is it ready? Yes! It is...", 3),
    ('He said "Hi." Then he left.', 2),
    ("See e.g. Paris, or Rome.", 1),
    ("He moved to the U.S. Navy base.", 1),
    ("We open at 9 a.m. Come early.", 2),
    ("J. Smith called. He left a note.", 2),
    ("Item No. 5 is out. Mar. 3 is the date.", 2),
    ("Version 2.0 is out at example.com today.", 1),
    ("No terminal punctuation here", 1),
    ("first line\nwrapped here.", 1),
    ("Line one\nLine two", 2),
    ("1. Fill your water bottle.\n2. Wear sturdy boots.", 2),
    ("", 0),
    ("!!! ...", 0),
])
def test_sentences_are_counted_by_rule(text, n):
    assert len(sentences(text)) == n


@pytest.mark.parametrize("unit,text,n", [
    ("words", "Your appointment with Dr. Patel is on Monday morning.", 9),
    ("words", "Your appointment with Dr. Patel is on Monday at ten.", 10),
    ("words", "It costs $42.50 - check-in isn't free.", 6),  # a lone "-" is no word
    ("words", "   ", 0),
    ("characters", "Parcel P707 arrives on Thursday.", 32),
    ("characters", "  ab c \n", 4),  # the outer spaces are removed, the inner ones count
    ("characters", "é", 1),  # NFC: an accented letter written as two code points is one character
    ("list_items", "- Water\n- A rain jacket\n- Sturdy boots", 3),
    ("list_items", "Pack these:\n1. Water\n2) A jacket\n(3) Boots\n  * nested\n• dot\na. letter", 6),
    ("list_items", "Water, a jacket and boots.", 0),
    ("list_items", "-5 degrees tonight.", 0),
    ("lines", "Pack water.\n\nWear boots.\n  \nBring a map.", 3),
    ("lines", "", 0),
])
def test_each_unit_is_counted_by_rule(unit, text, n):
    assert count_units(unit, text)[0] == n


@pytest.mark.parametrize("compare,n,to,count,holds", [
    ("exactly", 1, None, 1, True), ("exactly", 1, None, 2, False), ("at_most", 12, None, 12, True),
    ("at_most", 12, None, 13, False), ("at_least", 3, None, 2, False), ("fewer_than", 10, None, 10, False),
    ("fewer_than", 10, None, 9, True), ("more_than", 1, None, 2, True), ("between", 2, 4, 4, True),
    ("between", 2, 4, 5, False),
])
def test_the_bound(compare, n, to, count, holds):
    assert Count("words", compare, n, to).holds(count) is holds


def test_the_evidence_shows_the_count_and_the_pieces():
    met, why = decide(Count("sentences", "exactly", 1, only=True), "Flight LX318 is on time and leaves from gate B12.")
    assert met is True
    assert why == ('counted by the SDK, not the model: 1 sentence ("Flight LX318 is on time and leaves from gate B12."); '
                   "the part asks exactly 1 sentence: met.")
    met, why = decide(Count("words", "fewer_than", 10), "one two three four five six seven eight nine ten")
    assert met is False and "10 words" in why and "fewer than 10 words: NOT met" in why


# ---- the read -------------------------------------------------------------------------------------------------------

def _read(*parts):
    return json.dumps({"parts": list(parts)})


def _part(text="Is the reply a single sentence?", count=None, needs_right_answer=False, needs_input=False, **kw):
    return {"part": text, "look_at": "the reply", "needs_right_answer": needs_right_answer, "needs_input": needs_input,
            "required": True, "count": count, **kw}


def test_a_count_is_read_with_its_unit_and_bound():
    (p,) = parse_parts(_read(_part(count=ONE_SENTENCE)))
    assert p.count == Count("sentences", "exactly", 1, None, only=True) and p.counted_only


@pytest.mark.parametrize("raw,want", [
    ({"unit": "Words", "compare": "at most", "n": 12, "only": True}, Count("words", "at_most", 12, only=True)),
    ({"unit": "bullet points", "compare": "<=", "n": 3.0, "only": True}, Count("list_items", "at_most", 3, only=True)),
    ({"unit": "chars", "compare": "under", "n": 60}, Count("characters", "fewer_than", 60)),  # only missing: false
    ({"unit": "lines", "compare": "between", "n": 2, "to": 4, "only": True}, Count("lines", "between", 2, 4, True)),
])
def test_the_reads_spellings_are_normalized(raw, want):
    assert parse_count(raw, asks_more=False, text="t") == want


@pytest.mark.parametrize("raw", [None, False, {"unit": "paragraphs", "compare": "at_most", "n": 2},
                                 {"unit": "words", "compare": "at_most", "n": None},
                                 {"unit": "products", "compare": "at_most", "n": 2}])
def test_no_count_the_sdk_makes_leaves_the_part_to_the_model(raw):
    assert parse_count(raw, asks_more=False, text="t") is None


@pytest.mark.parametrize("raw", [{"unit": "words", "compare": "roughly", "n": 3}, {"unit": "words", "n": 3},
                                 {"unit": "words", "compare": "at_most", "n": -1},
                                 {"unit": "words", "compare": "at_most", "n": 2.5},
                                 {"unit": "words", "compare": "at_most", "n": True},
                                 {"unit": "words", "compare": "between", "n": 4, "to": 2},
                                 {"unit": "words", "compare": "between", "n": 4}, "words"])
def test_a_count_whose_bound_cannot_be_read_is_a_malformed_read_never_a_guess(raw):
    with pytest.raises(ValueError, match="the judge's criteria answer"):
        parse_parts(_read(_part(count=raw)))


@pytest.mark.parametrize("flags", [{"needs_right_answer": True}, {"needs_input": True}])
def test_a_part_that_needs_the_right_answer_or_the_input_is_never_count_only(flags):
    (p,) = parse_parts(_read(_part("Is the gate correct, and is the reply one sentence?", count=ONE_SENTENCE, **flags)))
    assert p.count is not None and not p.counted_only  # the model still judges the rest


def test_the_criteria_read_asks_for_the_count_and_never_to_count():
    assert '"count": null | {"unit"' in CRITERIA_SYSTEM and "Do not count anything yourself" in CRITERIA_SYSTEM


def test_a_count_beside_something_else_tells_the_model_not_to_count():
    (p,) = parse_parts(_read(_part("Is the reply polite, and at most 12 words?",
                                   count={"unit": "words", "compare": "at_most", "n": 12, "only": False})))
    text = part_request(p, input_text="i", output_text="o", expected_text=None)
    assert "COUNT:\nThe SDK counts the OUTPUT's words itself" in text and "Do not count words" in text
    (q,) = parse_parts(_read(_part()))
    assert "COUNT:" not in part_request(q, input_text="i", output_text="o", expected_text=None)


# ---- through Judge --------------------------------------------------------------------------------------------------

GATE_PARTS = [_part("Is the gate in the reply correct?", needs_right_answer=True),
              _part("Is the reply a single sentence?", count=ONE_SENTENCE)]


def _judge(parts, met=True, seen=None):
    seen = [] if seen is None else seen

    def handler(request):
        seen.append(json.loads(request.content)["messages"][1]["content"])
        return httpx.Response(200, json=part_verdict(met, reason="the gate B12 matches"))

    return Judge("Is the gate in the reply correct, and is the reply a single sentence?", model="gpt-4.1-mini",
                 transport=httpx.MockTransport(with_criteria(handler, parts=parts))), seen


@pytest.mark.parametrize("answer,passed", [("Flight LX318 is on time and leaves from gate B12.", True),
                                           ("Flight LX318 is on time. It leaves from gate B12.", False)])
def test_the_ch3_class_the_sentence_count_is_never_the_models(answer, passed):
    judge, seen = _judge(GATE_PARTS)
    score = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output=answer)))["judge"]
    assert score.status == "assessed" and score.passed is passed
    assert len(seen) == 1 and seen[0].startswith("PART:\nIs the gate in the reply correct?")  # one call: the gate
    assert "counted by the SDK, not the model:" in score.explanation
    assert ("1 sentence" if passed else "2 sentences") in score.explanation


def test_a_count_only_row_makes_no_call_and_its_span_says_so(monkeypatch):
    pytest.importorskip("opentelemetry.sdk")  # absent on Python 3.14 until TA-1
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    mem = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(mem))
    tracer = provider.get_tracer("t")

    def start_span(name, attrs):
        return tracer.start_span(name, attributes=attrs)

    judge, seen = _judge([_part(count=ONE_SENTENCE)], met=False)
    ec = EvalContext(row=ROW, output="Order E505 has shipped.", start_span=start_span)
    score = asyncio.run(judge.aevaluate(ec))["judge"]
    assert score.passed is True and seen == []  # the model's met=False is never asked for
    (span,) = [s for s in mem.get_finished_spans() if s.name == "experiment.judge"]
    a = dict(span.attributes)
    assert a["fi.experiment.judge.parts_counted"] == 1 and a["fi.experiment.judge.parts_asked"] == 0
    assert "gen_ai.usage.input_tokens" not in a and a["gen_ai.evaluation.score.label"] == "pass"


def test_a_count_beside_tone_needs_both():
    parts = [_part("Is the reply polite, and at most 5 words?",
                   count={"unit": "words", "compare": "at_most", "n": 5, "only": False})]
    judge, seen = _judge(parts, met=True)
    long_polite = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="Thank you so much, it is on time.")))
    assert long_polite["judge"].passed is False and len(seen) == 1 and "COUNT:" in seen[0]
    rude_judge, _ = _judge(parts, met=False)
    rude_short = asyncio.run(rude_judge.aevaluate(EvalContext(row=ROW, output="On time. Go away.")))
    assert rude_short["judge"].passed is False
    ok = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="Thanks, it is on time.")))["judge"]
    assert ok.passed is True and "The rest of the part: the gate B12 matches" in ok.explanation


def test_every_character_is_counted_past_the_prompt_cut():
    judge, _ = _judge([_part("Is the reply at most 20000 characters?",
                             count={"unit": "characters", "compare": "at_most", "n": 20000, "only": True})])
    score = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="x" * 20001)))["judge"]
    assert score.passed is False and "20001 characters" in score.explanation


def test_a_journaled_checklist_keeps_its_counts_on_resume():
    (p,) = parse_parts(_read(_part(count=ONE_SENTENCE)))
    journaled = {"judge": {"criteria_sha256": _judge_checklists.criteria_sha256("c"), "model": "gpt-4.1-mini",
                           "parts": [p.as_dict()]}}
    judge = Judge("c", model="gpt-4.1-mini")
    _judge_checklists.restore("run-1", journaled, [judge])
    assert judge.parts == (p,) and judge.parts[0].counted_only
    older = {"judge": dict(journaled["judge"], parts=[{k: v for k, v in p.as_dict().items() if k != "count"}])}
    judge2 = Judge("c", model="gpt-4.1-mini")
    _judge_checklists.restore("run-1", older, [judge2])  # an older SDK's journal: its run keeps its own checklist
    assert judge2.parts[0].count is None


def test_the_closing_lines_say_which_parts_the_sdk_counted():
    only = Part("Is the reply a single sentence?", "", False, False, True, Count("sentences", "exactly", 1, only=True))
    beside = Part("Polite and at most 5 words?", "", False, False, True, Count("words", "at_most", 5))
    assert _part_line(1, only.as_dict(), True, False).endswith("[counted by the SDK: exactly 1 sentence; no model call]")
    assert "[OUTPUT only; its count (at most 5 words) made by the SDK]" in _part_line(2, beside.as_dict(), True, False)
