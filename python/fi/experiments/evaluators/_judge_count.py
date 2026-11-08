"""Countable parts of a ``judge()`` CRITERIA are decided by code, not by the model.

LLM judges miscount. Every rate-gate failure of waves 2d-2e was one control: "Flight LX318 is on time and leaves from
gate B12." under "Is the gate in the reply correct, and is the reply a single sentence?" was read as two sentences in
about 1 run in 5 on gpt-4.1-mini. So when the criteria read marks a part as a count (``Count``: its unit and its bound),
the SDK counts the OUTPUT itself and the part's evidence shows the count; the model is never asked to count.

**What is counted** (the OUTPUT as the judge sees it: a string as it is; a dict or a list by its text values, each
counted on its own and summed, its keys, numbers and other values never counted, and the evidence says so; L-SDK2f
Regression coverage: ``{"reply": "Flight LX318 is on time."}`` is 5 words, not the 6 of its JSON text):
- ``words``: whitespace-separated tokens that hold at least one letter or digit ("LX318", "$42.50", "check-in" and
  "don't" are one word each; a lone "-" is none). Chinese and Japanese are written without spaces: each Han or Kana
  character counts as one word, a rough count that never reads a whole reply as one word. Thai, Lao, Khmer and Myanmar
  text is written without spaces too, and the SDK cannot split it into words or sentences: such a count is an error
  score, never a guess.
- ``sentences``: a sentence ends at ``.``, ``!``, ``?`` or ``…`` (with any closing quote or bracket) followed by a space
  and a capital letter or a digit (opening quotes, brackets, "¿" and "¡" before it are skipped), or a letter of a script
  with no capitals, or at the end of the text. "。", "！", "？" (Chinese, Japanese) and "।", "॥" (Hindi and other Indic
  scripts) always end one. A period inside a number ("$42.50"), a title before a name ("Dr. Patel"), "e.g.", "i.e.",
  "vs.", and a month or "No." before a number ("Mar. 3", "No. 5") end nothing. A single capital letter before "." is
  an initial and ends nothing ("J. Smith", "John F. Kennedy", "signed by M. Garcia") only when the word before it is
  missing (the sentence starts there), capitalized, another initial, or one that comes before a name ("by", "with",
  "contact", "call", "ask", "email", "dear", "cc", "attn"), and the word after it is not a common sentence opener ("It",
  "The", "This", "Please", ...). Otherwise it is a label and ends the sentence: "from gate B. Boarding starts at 9.",
  "The correct answer is B. Option C is wrong." and "I will take Plan A. It is cheaper." are 2 sentences each (review
  M1). A dotted capital abbreviation ("U.S.") ends nothing unless a common sentence opener follows it ("from the U.S.
  It arrives Friday."). Known limits, each a rule rather than a guess: a capitalized word, a letter and a word that is
  not an opener ("Take Plan A. Boarding is at 9.") reads as a name with an initial (1 sentence); a sentence that starts
  with a small letter is not split ("sure thing. your order shipped." is 1); a line break ends a sentence unless the
  next line starts with a small letter (a wrapped line), so a hard-wrapped line whose next line starts with a capital
  ("arrives on" / "Thursday.") is 2. A list marker at the start of a line ("1.", "-") is not part of the
  count, and a piece with no letter or digit is not a sentence.
- ``characters``: every character of the text with its leading and trailing spaces removed, spaces and line breaks
  inside it included (Unicode code points, after NFC normalization).
- ``list_items``: lines that start (after any indent) with a bullet (``-``, ``*``, ``•``, ``‣``, ``◦``, ``▪``, ``–``,
  ``—``) or a number or letter marker ("1.", "2)", "(3)", "a.", "b)") followed by a space. Only the items of such a
  list: "at most 3 items" said of things named in prose is not this unit (the read's unit must say list items; the
  aliases "items" / "item" are not read as it, regression coverage).
- ``lines``: lines that are not blank.

**The bound** (``compare``): ``exactly`` / ``at_most`` / ``at_least`` / ``fewer_than`` / ``more_than`` N, or ``between``
N and ``to`` (both included). "a single sentence" is exactly 1; "under 12 words" is fewer than 12.

**A part that asks something besides the count** (``only`` false, e.g. "polite and at most 12 words" left as one part):
the code decides the count and the model judges the rest, told not to count; the part is met only when both hold. A
part that needs the right answer or the INPUT is never count-only, whatever the read says (a count alone needs
neither), so a correctness question can never be skipped.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Optional

UNITS = ("words", "sentences", "characters", "list_items", "lines")
COMPARES = ("exactly", "at_most", "at_least", "fewer_than", "more_than", "between")
# "items" / "item" are NOT list_items: "recommend at most 3 items" is about things named in prose,
# and counting bullet lines for it would pass a prose reply naming 5 (0 list items); such a part stays the model's
_UNIT_ALIASES = {"word": "words", "sentence": "sentences", "character": "characters", "chars": "characters",
                 "char": "characters", "letters_and_spaces": "characters", "list_item": "list_items",
                 "bullets": "list_items", "bullet_points": "list_items", "bullet_point": "list_items",
                 "list_entries": "list_items", "line": "lines"}
_COMPARE_ALIASES = {"=": "exactly", "==": "exactly", "equal": "exactly", "equals": "exactly", "exact": "exactly",
                    "<=": "at_most", "max": "at_most", "maximum": "at_most", "no_more_than": "at_most",
                    ">=": "at_least", "min": "at_least", "minimum": "at_least", "no_fewer_than": "at_least",
                    "<": "fewer_than", "less_than": "fewer_than", "under": "fewer_than", "below": "fewer_than",
                    ">": "more_than", "greater_than": "more_than", "over": "more_than", "above": "more_than",
                    "range": "between"}
_SAID = {"exactly": "exactly {n}", "at_most": "at most {n}", "at_least": "at least {n}", "fewer_than": "fewer than {n}",
         "more_than": "more than {n}", "between": "between {n} and {to}"}


@dataclass(frozen=True)
class Count:
    """A part that counts the OUTPUT's ``unit``, with its bound (``compare`` ``n``, and ``to`` for ``between``)."""

    unit: str
    compare: str
    n: int
    to: Optional[int] = None
    only: bool = False  # the part asks nothing besides this count: decided by code alone, with no model call

    def holds(self, count: int) -> bool:
        return {"exactly": count == self.n, "at_most": count <= self.n, "at_least": count >= self.n,
                "fewer_than": count < self.n, "more_than": count > self.n,
                "between": self.to is not None and self.n <= count <= self.to}[self.compare]

    def asks(self) -> str:
        unit = self.unit.replace("_", " ")
        last = self.to if self.compare == "between" else self.n
        return f"{_SAID[self.compare].format(n=self.n, to=self.to)} {unit[:-1] if last == 1 else unit}"


def _key(value: Any) -> str:
    return re.sub(r"[\s\-]+", "_", str(value).strip().lower())


def _whole(value: Any, what: str, text: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 \
            or int(value) != value:
        raise ValueError(f"the judge's criteria answer has a count whose {what} is not a whole number: {text[:200]!r}")
    return int(value)


def parse_count(raw: Any, *, asks_more: bool, text: str) -> Optional[Count]:
    """The read's ``count`` for one part, or None when the part is not a count the SDK makes (no count, a unit the SDK
    does not count, or no number: the model judges such a part as before). A count the SDK makes but whose bound it
    cannot read is an error (``ValueError``), never a guess. ``asks_more``: the part needs the right answer or the
    INPUT, so it is never count-only."""
    if raw is None or raw is False:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"the judge's criteria answer has a count that is not an object: {text[:200]!r}")
    unit = _key(raw.get("unit", ""))
    unit = _UNIT_ALIASES.get(unit, unit)
    if unit not in UNITS or raw.get("n") is None:
        return None
    compare = _key(raw.get("compare", ""))
    compare = _COMPARE_ALIASES.get(compare, compare)
    if compare not in COMPARES:
        raise ValueError(f"the judge's criteria answer has a count with an unknown compare {raw.get('compare')!r}: "
                         f"{text[:200]!r}")
    n = _whole(raw.get("n"), "n", text)
    to = _whole(raw.get("to"), "to", text) if compare == "between" else None
    if to is not None and to < n:
        raise ValueError(f"the judge's criteria answer has a count between {n} and {to}: {text[:200]!r}")
    return Count(unit, compare, n, to, only=raw.get("only") is True and not asks_more)


# ---- the counters -------------------------------------------------------------------------------------------------

_TITLES = {"mr", "mrs", "ms", "mx", "dr", "prof", "st", "rev", "hon", "gen", "col", "capt", "lt", "sgt", "mme", "mlle",
           "messrs", "vs", "e.g", "i.e", "cf", "viz", "approx"}
_BEFORE_NUMBER = {"no", "nos", "vol", "fig", "p", "pp", "art", "sec", "ch", "jan", "feb", "mar", "apr", "jun", "jul",
                  "aug", "sep", "sept", "oct", "nov", "dec"}
# full stops of scripts with no capitals and often no space after them: they always end a sentence
_ALWAYS_ENDS = "。！？｡।॥"
_CLOSERS = "\"'”’)]»」』）》】〕"
_END = re.compile(r"[.!?…。！？｡।॥]+[" + re.escape(_CLOSERS) + r"]*")
_OPENERS = "\"'“‘([«¿¡「『（《【〔"
# words that start a sentence and are never a surname: after one, "B." or "U.S." ends its sentence ("Plan A. It ...")
_OPENER_WORDS = {
    "a", "an", "the", "this", "that", "these", "those", "it", "it's", "its", "i", "i'm", "i'll", "i've", "we", "we're",
    "we'll", "you", "you're", "you'll", "he", "she", "they", "they're", "there", "there's", "here", "here's", "my",
    "your", "our", "their", "his", "her", "and", "but", "or", "so", "then", "also", "however", "please", "thanks",
    "thank", "yes", "no", "not", "if", "when", "while", "each", "every", "all", "both", "some", "any", "most", "many",
    "none", "either", "neither", "note", "next", "finally", "first", "second", "otherwise", "sure", "okay", "ok",
    "well", "great", "what", "which", "who", "how", "why", "where", "is", "are", "was", "were", "do", "does", "did",
    "can", "should", "would", "could", "let", "let's", "just", "only", "after", "before", "once", "for", "in", "on",
    "at", "to", "with", "as", "because", "since", "unfortunately", "hello", "hi", "sorry", "now", "today",
    "tomorrow", "yesterday", "again", "still", "remember", "make", "check", "see", "use", "go", "choose", "pick",
    "take", "bring", "keep", "try", "visit", "wait"}
# words that come before a name, so a capital letter after one is an initial ("signed by M. Garcia")
_NAME_BEFORE = {"by", "with", "contact", "call", "ask", "email", "dear", "cc", "attn"}
_MARKER = r"^\s*(?:[-*•‣◦▪–—]|\(?\d{1,3}[.)]|\(\d{1,3}\)|[a-z][.)]|\(?[A-Za-z]\))\s+"
_BULLET = re.compile(_MARKER + r"\S")
_LEADING_MARKER = re.compile(_MARKER)
# Thai, Lao, Khmer, Myanmar: no spaces between words, and splitting needs a dictionary
_UNSPLIT_SCRIPTS = re.compile("[\u0e00-\u0eff\u1000-\u109f\u1780-\u17ff\u19e0-\u19ff\ua9e0-\ua9ff\uaa60-\uaa7f]")
# Han and Kana: each character counts as a word
_HAN_KANA = re.compile("[\u3040-\u30ff\u31f0-\u31ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f"
                       "\U00020000-\U0002ebef\U00030000-\U0003134f]")


def _starts_sentence(text: str) -> bool:
    """Whether ``text`` (what follows a terminator and its space) starts with a capital, a digit, or a letter of a
    script with no capitals, after any opening quotes, brackets, "¿" or "¡"."""
    head = text.lstrip(_OPENERS) or text
    first = head[0]
    return first.isdigit() or (first.isalpha() and not first.islower())


def _first_word(text: str) -> str:
    found = re.match(r"[^\W\d_]+(?:['’][^\W\d_]+)?", text.lstrip(_OPENERS))
    return found.group().lower().replace("’", "'") if found else ""


def _is_initial(word: "re.Match[str]", line: str, nxt: str) -> bool:
    """A single capital letter before ".": an initial (ends nothing) or a label that ends its sentence."""
    if _first_word(nxt) in _OPENER_WORDS:
        return False  # "Plan A. It is cheaper.": no name starts with "It"
    if word.group(1)[:1] in _OPENERS:
        return True  # an opening quote or bracket starts a sentence there: '"J. Smith called."'
    before = re.search(r"(\S+)\s+$", line[:word.start(1)])
    if before is None:
        return True  # the sentence starts with it: "J. Smith called."
    prev = before.group(1).lstrip(_OPENERS)
    return (prev == "" or prev[-1:] in ".!?…" or prev[:1].isupper() or prev.lower().rstrip(",:;") in _NAME_BEFORE
            or bool(re.fullmatch(r"[^\W\d_]\.", prev)))  # after a capitalized word ("John F."), another initial


def _ends_here(line: str, match: "re.Match[str]") -> bool:
    """Whether the terminator ``match`` in ``line`` ends a sentence."""
    rest = line[match.end():]
    if rest.strip() == "":
        return True
    if any(c in _ALWAYS_ENDS for c in match.group()):  # "你好。我很好。", "नमस्ते। आप कैसे हैं?"
        return True
    if not rest[:1].isspace():  # "42.50", "example.com", "v2.0": no space after it
        return False
    nxt = rest.lstrip()
    if not _starts_sentence(nxt):
        return False
    if match.group().rstrip(_CLOSERS) == ".":
        word = re.search(r"(\S+)\.$", line[:match.start() + 1])
        raw = word.group(1).lstrip(_OPENERS) if word else ""
        token = raw.lower()
        if token in _TITLES or (token in _BEFORE_NUMBER and nxt[:1].isdigit()):
            return False
        if word and re.fullmatch(r"[^\W\d_]", raw) and raw.isupper():
            return not _is_initial(word, line, nxt)  # "J. Smith" ends nothing; "from gate B. Boarding" ends
        if re.fullmatch(r"(?:[a-z]\.)+[a-z]", token) and raw[:1].isupper():
            return _first_word(nxt) in _OPENER_WORDS  # "the U.S. Navy" ends nothing; "from the U.S. It arrives" ends
    return True


def sentences(text: str) -> list[str]:
    lines = [_LEADING_MARKER.sub("", ln).strip() for ln in text.splitlines()]  # "1. Pack water." is one sentence
    joined: list[str] = []
    for ln in lines:
        if not ln:
            joined.append("")
        elif joined and joined[-1] and ln[:1].islower() and not _END.search(joined[-1][-1:]):
            joined[-1] += " " + ln  # a wrapped line continues its sentence
        else:
            joined.append(ln)
    out: list[str] = []
    for ln in joined:
        start = 0
        for m in _END.finditer(ln):
            if _ends_here(ln, m):
                out.append(ln[start:m.end()].strip())
                start = m.end()
        out.append(ln[start:].strip())
    return [s for s in out if any(ch.isalnum() for ch in s)]


def _unsplit(unit: str, text: str) -> None:
    found = _UNSPLIT_SCRIPTS.search(text)
    if found:
        script = unicodedata.name(found.group(), "").split(" ")[0].title() or "this script"
        raise ValueError(f"the SDK cannot count {unit} in {script} text (Thai, Lao, Khmer and Myanmar are written "
                         "without spaces between words): this count is an error, never a guess")


def _words(text: str) -> int:
    _unsplit("words", text)
    n = 0
    for token in text.split():
        n += sum(1 for ch in token if _HAN_KANA.match(ch) and unicodedata.category(ch) == "Lo")
        n += sum(1 for piece in _HAN_KANA.sub(" ", token).split() if any(ch.isalnum() for ch in piece))
    return n


def count_units(unit: str, text: str) -> tuple[int, list[str]]:
    """``(the count, the pieces counted)``: the pieces are kept for sentences, list items and lines (the evidence)."""
    if unit == "words":
        return _words(text), []
    if unit == "characters":
        return len(unicodedata.normalize("NFC", text.strip())), []
    if unit == "sentences":
        _unsplit("sentences", text)
        found = sentences(text)
    elif unit == "list_items":
        found = [ln.strip() for ln in text.splitlines() if _BULLET.match(ln)]
    elif unit == "lines":
        found = [ln.strip() for ln in text.splitlines() if ln.strip()]
    else:  # parse_count admits only UNITS
        raise ValueError(f"the SDK does not count {unit!r}")
    return len(found), found


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [t for v in value.values() for t in _string_values(v)]
    if isinstance(value, (list, tuple)):
        return [t for v in value for t in _string_values(v)]
    return []  # a number, a bool, None: not text


def texts_of(output: Any) -> Optional[list[str]]:
    """The OUTPUT's text the SDK counts: None for a string (counted as it is); for a dict or a list, its string values
    in order (nested ones too), never its keys, numbers or other values; for None, no text; anything else, its JSON
    text as one value."""
    if isinstance(output, str):
        return None
    if output is None:
        return []
    if isinstance(output, (dict, list, tuple)):
        return _string_values(output)
    return [json.dumps(output, ensure_ascii=False, default=repr)]


def _quote(piece: str, cut: int = 80) -> str:
    return '"' + (piece if len(piece) <= cut else piece[:cut] + "…") + '"'


def decide(count: Count, output: Any) -> tuple[bool, str]:
    """``(met, evidence)``: the count made by code and whether the part's bound holds. ``output`` is the row's OUTPUT:
    a string is counted as it is, a dict or a list by its text values (``texts_of``), and the evidence says which."""
    values = texts_of(output)
    n, pieces = 0, []
    for text in ([output] if values is None else values):
        got, found = count_units(count.unit, text)
        n, pieces = n + got, pieces + found
    unit = count.unit.replace("_", " ")
    if n == 1 and unit.endswith("s"):
        unit = unit[:-1]
    shown = ""
    if pieces:
        shown = " (" + "; ".join(_quote(p) for p in pieces[:10]) + ("; …" if len(pieces) > 10 else "") + ")"
    over = ""
    if isinstance(output, (dict, list, tuple)):
        what = "text value" if len(values or []) == 1 else "text values"
        over = (f", over the OUTPUT's {len(values or [])} {what}, each counted on its own (its keys and other values "
                "are not counted)")
    met = count.holds(n)
    return met, (f"counted by the SDK, not the model{over}: {n} {unit}{shown}; the part asks {count.asks()}: "
                 f"{'met' if met else 'NOT met'}.")
