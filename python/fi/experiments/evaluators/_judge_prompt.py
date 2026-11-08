"""``judge()``'s two prompts and the parsing of their answers (wave 2d: the criteria read's parts are the checklist).

1. **The criteria read** (``CRITERIA_SYSTEM``), once per judge: the CRITERIA split into the separate things they ask
   (parts). For each part: what to look at, whether checking it needs the right answer (EXPECTED), whether it needs
   the INPUT, and whether the CRITERIA make it required.
2. **One verdict per part** (``SYSTEM``): each part is judged on its own, in its own request, against only what it
   needs: the OUTPUT always; the INPUT when the part needs it, and for a part that asks about correctness on a row
   with no EXPECTED (``shows_input``); EXPECTED only when the part asks about correctness. The SDK, not the model,
   combines them: the score is the share of parts met, and the verdict passes exactly when every required part is met
   (``combine``).
3. **A part that counts** (words, sentences, characters, list items, lines; wave 2f) is marked by the read with its unit
   and bound (``count``), and the SDK counts it (``_judge_count``): a count-only part makes no verdict request, and a
   part with a count beside something else is sent with a COUNT note telling the model not to count.

Why (e2e evaluation regression B15/B16, waves 2c-2d): asked for one verdict over the whole CRITERIA with the INPUT in view, the
default judge failed "Order E505 has shipped." under "Is the reply a single sentence?" because the INPUT also asked
for a tracking number, a requirement the CRITERIA never state.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Optional, Sequence

from fi.experiments.evaluators._judge_count import Count, parse_count

CRITERIA_SYSTEM = (
    "You read the CRITERIA that an evaluator will apply to an OUTPUT. Split them into parts: the separate things they "
    "ask, each in the CRITERIA's own words (a CRITERIA that asks one thing is one part). Never add a part the CRITERIA "
    "do not ask for, such as answering all of the INPUT, being complete, or being helpful. For each part, first say "
    "what must be looked at to check it, then whether checking it needs the right answer to compare with. "
    "needs_right_answer is true only when the part asks whether the OUTPUT's answer or facts are right or correct. "
    "It is false when reading the OUTPUT alone is enough: its tone or politeness, its length, its format, structure, "
    "fields or keys, its language, whether it mentions or states something (whatever the value), and whether it "
    "reveals or keeps something private. needs_input is true only when checking the part needs the INPUT: whether the "
    "OUTPUT answers the INPUT's question or questions, or is about what the INPUT asks; it is false when the OUTPUT "
    "alone is enough. required is false only when the CRITERIA say the part is optional or only preferred (for example "
    "\"ideally\" or \"if possible\"); otherwise it is true. count is for a part that asks how many words, sentences, "
    "characters, list items or lines the whole OUTPUT has, with a number (its length in words or characters, or its "
    "number of sentences, list items or lines): the unit (\"words\", \"sentences\", \"characters\", \"list_items\" or "
    "\"lines\"), compare (\"exactly\", \"at_most\", \"at_least\", \"fewer_than\", \"more_than\" or \"between\"), n "
    "(the number in the CRITERIA), to (the upper number, only for between) and only (true when the part asks nothing "
    "but that count, false when it also asks something else, such as tone or correctness). \"A single sentence\" or "
    "\"one sentence\" is exactly 1 sentence; \"under 12 words\" is fewer_than 12; \"no more than 3 list items\" "
    "is at_most 3 list_items (list_items are only the items of a bulleted or numbered list, never things named in a "
    "sentence). "
    "Make a count its own part: \"Is the gate correct, and is the reply a single sentence?\" is two parts, and the "
    "sentence part's count has only true. Do not count anything yourself; the count is made by code. count is null for "
    "every other part, including a length with no number (\"short\", \"brief\"). Reply with one JSON object only: "
    '{"parts": [{"part": "<from the CRITERIA>", "look_at": "<what to check in the OUTPUT>", "needs_right_answer": '
    '<true|false>, "needs_input": <true|false>, "required": <true|false>, "count": null | {"unit": "<unit>", '
    '"compare": "<compare>", "n": <number>, "to": <number or null>, "only": <true|false>}}]}.'
)
SYSTEM = (
    "You are an evaluator. You judge ONE PART of an evaluator's CRITERIA: decide whether the OUTPUT meets the PART, "
    "and nothing else. Any other parts are judged separately. Never add a requirement the PART does not state, such as "
    "answering all of the INPUT, being complete, or being helpful. LOOK AT says what to check. The INPUT is given only "
    "when the PART needs it. When an EXPECTED answer is given, it is a reference for the facts, not for the wording. "
    "Work in this order: (1) list each fact in EXPECTED that the PART cares about (a status, number, amount, name, "
    "date, place, or a yes/no answer), in EXPECTED's words. Facts come from EXPECTED only: the INPUT, a question, and "
    "the PART are never facts; "
    "(2) for each fact, copy the words of the OUTPUT that state it (empty if none), then compare their meaning with "
    "the fact: \"same\" when they mean the same thing in any words, \"different\" when they contradict it (another "
    "value, the opposite answer, or a negation), \"missing\" when the OUTPUT does not state it. Synonyms, paraphrase, "
    "word order, tense, grammar, and extra information that does not contradict the fact never make a fact "
    "different; "
    "(3) with EXPECTED, the PART is met exactly when every fact is \"same\" and the OUTPUT meets the rest of the PART. "
    "Without an EXPECTED answer, judge the OUTPUT against the PART alone and leave facts empty. "
    "Reply with one JSON object only, the facts first and the verdict last: "
    '{"facts": [{"fact": "<from EXPECTED>", "output_words": "<from OUTPUT>", "output": "same" | "different" | '
    '"missing"}], "reason": "<one or two sentences: what the PART asks and whether the OUTPUT meets it>", '
    '"met": <true|false>}.'
)


@dataclass(frozen=True)
class Part:
    """One thing the CRITERIA ask, as the criteria read split it."""

    part: str
    look_at: str
    needs_right_answer: bool
    needs_input: bool
    required: bool
    count: Optional[Count] = None  # a count the SDK makes itself (wave 2f, ``_judge_count``); None: the model judges

    def as_dict(self) -> dict[str, Any]:
        """The part as the journal, the run's metadata and the criteria span keep it; ``count`` only when it has one
        (a part with no count reads as before wave 2f)."""
        out = asdict(self)
        if out["count"] is None:
            del out["count"]
        return out

    @property
    def counted_only(self) -> bool:
        """Decided by code alone: the part is a count and asks nothing else, so no model call is made for it."""
        return self.count is not None and self.count.only


def _json_object(text: str, what: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"the judge did not return JSON for {what}: {text[:200]!r}")
    data = json.loads(match.group())
    if not isinstance(data, dict):
        raise ValueError(f"the judge's answer for {what} is not a JSON object: {text[:200]!r}")
    return data


def parse_parts(text: str) -> tuple[Part, ...]:
    """The criteria read's parts. Every part needs its text and true/false for ``needs_right_answer``; a missing
    ``needs_input`` is true (the INPUT is shown) and a missing ``required`` is true (fail closed). When no part is
    required, every part is: the CRITERIA as a whole must then be met. A part's ``count`` is read by
    ``_judge_count.parse_count`` (a missing ``only`` is false, so the model still judges the rest of the part)."""
    raw = _json_object(text, "its criteria").get("parts")
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"the judge's criteria answer has no parts: {text[:200]!r}")
    parts = []
    for p in raw:
        if not (isinstance(p, dict) and isinstance(p.get("part"), str) and p["part"].strip()
                and isinstance(p.get("needs_right_answer"), bool)):
            raise ValueError(f"the judge's criteria answer has a part without its text or needs_right_answer: "
                             f"{text[:200]!r}")
        flags = {k: p.get(k, True) for k in ("needs_input", "required")}
        if not all(isinstance(v, bool) for v in flags.values()):
            raise ValueError(f"the judge's criteria answer has a needs_input or required that is not true/false: "
                             f"{text[:200]!r}")
        count = parse_count(p.get("count"), asks_more=p["needs_right_answer"] or flags["needs_input"], text=text)
        parts.append(Part(p["part"].strip(), str(p.get("look_at") or "").strip(), p["needs_right_answer"], **flags,
                          count=count))
    if not any(p.required for p in parts):
        parts = [Part(p.part, p.look_at, p.needs_right_answer, p.needs_input, True, p.count) for p in parts]
    return tuple(parts)


def parse_asks_correctness(text: str) -> bool:
    """True when any part of the CRITERIA needs the right answer to check (the criteria read, ``CRITERIA_SYSTEM``)."""
    return any(p.needs_right_answer for p in parse_parts(text))


def parse_part_verdict(text: str) -> tuple[bool, str]:
    """``(met, reason)`` from one part's verdict. No true/false ``met`` is an error, never a made-up verdict."""
    data = _json_object(text, "a part of its criteria")
    met = data.get("met")
    if not isinstance(met, bool):
        raise ValueError(f"the judge's answer for a part has no true/false met: {text[:200]!r}")
    return met, str(data.get("reason", ""))


def shows_input(part: Part, has_expected: bool) -> bool:
    """Whether a part's request shows the INPUT: when the part needs it, and always for a part that asks about
    correctness on a row with no EXPECTED. With no reference answer, whether an answer is right can
    only be judged against what it answers, and the criteria read marks such a part needs_input=false when its words do
    not mention the INPUT (the real reads of "Is the gate in the reply correct" did). Before this, "Is the answer
    correct?" on a row with no EXPECTED was judged on the OUTPUT alone: a verdict with no basis."""
    return part.needs_input or (part.needs_right_answer and not has_expected)


def part_request(part: Part, *, input_text: str, output_text: str, expected_text: Optional[str]) -> str:
    """The user message for one part: the PART, what to look at, the INPUT when ``shows_input`` says so, the OUTPUT,
    and EXPECTED only when the part asks about correctness and the row has one."""
    blocks = [f"PART:\n{part.part}"]
    if part.look_at:
        blocks.append(f"LOOK AT:\n{part.look_at}")
    if shows_input(part, expected_text is not None):
        blocks.append(f"INPUT:\n{input_text}")
    blocks.append(f"OUTPUT:\n{output_text}")
    if part.needs_right_answer and expected_text is not None:
        blocks.append(f"EXPECTED:\n{expected_text}")
    if part.count is not None:  # a count beside something else: the SDK counts, the model judges the rest
        unit = part.count.unit.replace("_", " ")
        blocks.append(f"COUNT:\nThe SDK counts the OUTPUT's {unit} itself and checks that the PART's number of {unit} "
                      f"holds. Do not count {unit}: judge only the rest of the PART, as if its number of {unit} is "
                      "right.")
    return "\n\n".join(blocks)


def combine(parts: Sequence[Part], verdicts: Sequence[tuple[bool, str]]) -> tuple[float, bool, str]:
    """``(score, passed, explanation)``: the score is the share of parts met; the verdict passes exactly when every
    required part is met. A one-part CRITERIA keeps the model's reason as the explanation."""
    met = [m for m, _ in verdicts]
    score = sum(met) / len(parts)
    passed = all(m for p, m in zip(parts, met) if p.required)
    if len(parts) == 1:
        return score, passed, verdicts[0][1]
    lines = [f"{n}. {p.part}{'' if p.required else ' (optional)'}: {'met' if m else 'NOT met'}. {reason}".strip()
             for n, (p, (m, reason)) in enumerate(zip(parts, verdicts), 1)]
    return score, passed, " ".join(lines)
