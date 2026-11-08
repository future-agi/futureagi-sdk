"""L-SDK2f review fixes (SDK the recorded revision..the recorded version): the counts judge() makes by code. No network, no model.

- M1: the sentence counter gave confident wrong counts on common text, and the reason said "counted by the SDK, not
  the model". A single capital letter before "." was always an initial ("...from gate B. Boarding starts at 9." was 1
  sentence: the ch3 class itself), "¿" and "¡" were no openers, and "。", "！", "？", "।" ended nothing. Each probe row of
  the review is a test here, and real initials stay initials ("J. Smith called.", "John F. Kennedy spoke.").
- S1: a dict OUTPUT was counted on its JSON text ({"reply": "Flight LX318 is on time."} was 6 words, its key one of
  them); it is now counted by its text values, and the evidence says so.
- S2: the unit aliases "items" / "item" no longer mean list items; the read's example says "list items".
- S4: Chinese and Japanese count each Han or Kana character as a word; Thai, Lao, Khmer and Myanmar are an error score.
- S5: two counter rules pinned as documented: a wrapped line whose next line starts with a capital is 2 sentences, and
  a sentence that starts with a small letter is not split.
- S9: the retirement sentence has one pair of parentheses after the provider's host.
"""

import asyncio
import json

import httpx
import pytest

from fi.experiments import _provider_errors
from fi.experiments._dataset import load_local
from fi.experiments.evaluators import _judge_count
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators._judge_count import Count, count_units, decide, parse_count, sentences, texts_of
from fi.experiments.evaluators._judge_prompt import CRITERIA_SYSTEM
from fi.experiments.evaluators.judge import Judge
from tests.experiments.unit.judge_helpers import part_verdict, with_criteria

FAKE = "-".join(("judge", "fake", "value"))
ROW = load_local([{"question": "Which gate does my flight leave from?",
                   "expected": "Your flight leaves from gate B."}]).rows[0]
ONE_SENTENCE = {"unit": "sentences", "compare": "exactly", "n": 1, "only": True}


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


# ---- M1: the review's probe rows (cache/l-sdk2f-review/probe/probe_count.out) ---------------------------------------

@pytest.mark.parametrize("text", [
    "Your flight leaves from gate B. Boarding starts at 9.",  # the ch3 class: a label letter after a lowercase word
    "The correct answer is B. Option C is wrong.",
    "I will take Plan A. It is cheaper.",  # after a capitalized word, but "It" starts a sentence, never a name
    "Hola. ¿Cómo estás?",
    "Gracias. ¡Buen viaje!",
    "你好。我很好。",
    "आप कैसे हैं। मैं ठीक हूँ।",  # Hindi with the danda
    "मैं ठीक हूँ॥ धन्यवाद॥",  # the double danda
    "注文を受け付けました！ありがとうございます？",  # full-width ! and ?
])
def test_each_probe_row_is_two_sentences(text):
    assert len(sentences(text)) == 2, sentences(text)


@pytest.mark.parametrize("text", [
    "J. Smith called.",  # at the start
    "John F. Kennedy spoke.",  # after a capitalized word
    "J. R. R. Tolkien wrote it.",  # after another initial
    "Your parcel was signed for by M. Garcia at the front desk.",  # after a word that comes before a name
    "Please contact J. Smith for the refund.",
    '"J. Smith called," she said.',  # after an opening quote
    "Agent Maria L. Chen will call you back.",
    "Dr. Patel will see you on Monday.",
    "The U.S. Postal Service delivers it.",  # "U.S." before a word that is not a sentence opener
    "Flight LX318 is on time and leaves from gate B12.",
])
def test_initials_titles_and_abbreviations_end_nothing(text):
    assert len(sentences(text)) == 1, sentences(text)


@pytest.mark.parametrize("text,n", [
    ("It shipped. J. Smith signed for it.", 2),  # a letter right after a full stop starts a sentence: an initial
    ("Board at gates A and B. Bring your pass.", 2),  # "and" does not come before a name here
    ("Your gate changed to B. Boarding starts at 9.", 2),
    ("Your order ships from the U.S. It arrives Friday.", 2),  # "U.S." before a sentence opener ends it
    ("He moved to the U.S. Navy base.", 1),
    ("Vitamin C. Take it daily.", 2),  # "Take" is an opener
    ("Take Plan A. Boarding is at 9.", 1),  # the documented limit: a capitalized word, a letter, a non-opener
    ('He said "Hi." Then he left.', 2),
    ("「你好。」他说。", 2),
])
def test_the_rules_around_a_capital_letter_before_a_full_stop(text, n):
    assert len(sentences(text)) == n, sentences(text)


def test_the_ch3_probe_through_judge_fails_a_two_sentence_reply():
    """The review's first probe row, as the ch3 control asks it: the gate is right, but the reply is two sentences."""
    parts = [{"part": "Is the gate in the reply correct?", "look_at": "the gate", "needs_right_answer": True,
              "needs_input": False, "required": True, "count": None},
             {"part": "is the reply a single sentence?", "look_at": "the reply", "needs_right_answer": False,
              "needs_input": False, "required": True, "count": ONE_SENTENCE}]
    seen = []

    def handler(request):
        seen.append(json.loads(request.content)["messages"][1]["content"])
        return httpx.Response(200, json=part_verdict(True, reason="gate B matches"))

    judge = Judge("Is the gate in the reply correct, and is the reply a single sentence?", model="gpt-4.1-mini",
                  transport=httpx.MockTransport(with_criteria(handler, parts=parts)))
    two = "Your flight leaves from gate B. Boarding starts at 9."
    score = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output=two)))["judge"]
    assert score.status == "assessed" and score.passed is False and len(seen) == 1
    assert ('2 sentences ("Your flight leaves from gate B."; "Boarding starts at 9."); the part asks exactly 1 '
            "sentence: NOT met") in score.explanation
    one = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="Your flight leaves from gate B at 9.")))["judge"]
    assert one.passed is True


# ---- S1: a dict or list OUTPUT is counted by its text values ---------------------------------------------------------

def test_a_dict_output_is_counted_on_its_text_values_not_its_json():
    out = {"reply": "Flight LX318 is on time."}
    met, why = decide(Count("words", "at_most", 5), out)
    assert met is True and why.startswith("counted by the SDK, not the model, over the OUTPUT's 1 text value, each "
                                          "counted on its own (its keys and other values are not counted): 5 words;")
    met, why = decide(Count("characters", "at_most", 24), out)
    assert met is True and "): 24 characters;" in why  # its JSON text is 37
    assert len(json.dumps(out)) == 37


def test_nested_values_are_counted_and_numbers_and_keys_are_not():
    out = {"reply": "It shipped. It arrives Friday.", "meta": {"eta_days": 3, "notes": ["Signed by M. Garcia."]},
           "ok": True}
    assert texts_of(out) == ["It shipped. It arrives Friday.", "Signed by M. Garcia."]
    met, why = decide(Count("sentences", "exactly", 3), out)
    assert met is True and "over the OUTPUT's 2 text values" in why
    assert decide(Count("words", "exactly", 0), {"n": 5})[0] is True  # no text values: nothing to count
    assert texts_of("plain") is None and texts_of(None) == [] and texts_of(42) == ["42"]


def test_a_dict_output_through_judge_meets_the_count():
    parts = [{"part": "Is the reply at most 5 words?", "look_at": "the reply", "needs_right_answer": False,
              "needs_input": False, "required": True,
              "count": {"unit": "words", "compare": "at_most", "n": 5, "only": True}}]
    judge = Judge("Is the reply at most 5 words?", model="gpt-4.1-mini",
                  transport=httpx.MockTransport(with_criteria(lambda r: httpx.Response(500), parts=parts)))
    score = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output={"reply": "Flight LX318 is on time."})))["judge"]
    assert score.status == "assessed" and score.passed is True and "1 text value" in score.explanation


# ---- S2: "items" is not list items -----------------------------------------------------------------------------------

@pytest.mark.parametrize("unit", ["items", "item", "Items"])
def test_items_is_not_read_as_list_items(unit):
    assert parse_count({"unit": unit, "compare": "at_most", "n": 3, "only": True}, asks_more=False, text="t") is None


def test_the_reads_example_says_list_items():
    assert '\\"no more than 3 items\\"' not in json.dumps(CRITERIA_SYSTEM)
    assert '"no more than 3 list items" is at_most 3 list_items' in CRITERIA_SYSTEM
    assert "list_items are only the items of a bulleted or numbered list" in CRITERIA_SYSTEM
    assert parse_count({"unit": "list items", "compare": "at_most", "n": 3}, asks_more=False, text="t") == \
        Count("list_items", "at_most", 3)


# ---- S4: text written without spaces ---------------------------------------------------------------------------------

@pytest.mark.parametrize("text,n", [
    ("你好世界", 4),  # four Han characters
    ("您的包裹已经发出。", 8),  # the full stop is no word
    ("我在Tokyo工作", 5),  # 4 Han characters and one Latin word
    ("コーヒーを飲む", 5),  # Kana and Han; the long-vowel mark "ー" is no word
    ("check-in isn't free", 3),
])
def test_han_and_kana_characters_count_as_words(text, n):
    assert count_units("words", text)[0] == n


@pytest.mark.parametrize("text,script", [("สวัสดีครับ ยินดีต้อนรับ", "Thai"), ("ສະບາຍດີ", "Lao"),
                                         ("សួស្តី", "Khmer"), ("မင်္ဂလာပါ", "Myanmar")])
def test_words_or_sentences_in_unsplit_scripts_are_an_error_never_a_guess(text, script):
    for unit in ("words", "sentences"):
        with pytest.raises(ValueError, match=f"cannot count {unit} in {script} text"):
            count_units(unit, text)
    assert count_units("characters", text)[0] == len(text)  # characters need no word boundaries


def test_a_thai_reply_is_an_error_score_through_judge():
    parts = [{"part": "Is the reply under 10 words?", "look_at": "the reply", "needs_right_answer": False,
              "needs_input": False, "required": True,
              "count": {"unit": "words", "compare": "fewer_than", "n": 10, "only": True}}]
    judge = Judge("Is the reply under 10 words?", model="gpt-4.1-mini",
                  transport=httpx.MockTransport(with_criteria(lambda r: httpx.Response(500), parts=parts)))
    score = asyncio.run(judge.aevaluate(EvalContext(row=ROW, output="สวัสดีครับ ยินดีต้อนรับ")))["judge"]
    assert score.status == "error" and score.passed is None and "cannot count words in Thai text" in score.explanation


# ---- S5: two documented counter rules --------------------------------------------------------------------------------

def test_a_wrapped_line_whose_next_line_starts_with_a_capital_is_two_sentences():
    assert sentences("Your parcel arrives on\nThursday.") == ["Your parcel arrives on", "Thursday."]
    assert len(sentences("Your parcel arrives on\nthursday.")) == 1  # a small letter: the line was wrapped
    assert "a hard-wrapped line whose" in _judge_count.__doc__ and '"Thursday.") is 2' in _judge_count.__doc__


def test_a_sentence_that_starts_with_a_small_letter_is_not_split():
    assert len(sentences("sure thing. your order shipped.")) == 1
    assert '("sure thing. your order shipped." is 1)' in " ".join(_judge_count.__doc__.split())


# ---- S9: one pair of parentheses -------------------------------------------------------------------------------------

def test_the_retirement_sentence_has_one_pair_of_parentheses():
    found = _provider_errors.Retirement(404, "model_not_found", "The model `x` has been deprecated", "x")
    text = _provider_errors.describe(found, "api.openai.com")
    assert text.startswith("the model 'x' was retired by the provider at api.openai.com (HTTP 404 model_not_found: ")
    assert ") (" not in text
    assert _provider_errors.sentence_in(f"ModelRetiredError: {text}") == text
