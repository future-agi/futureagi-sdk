"""The exact set of characters the exec channel's server-text scrub drops, shared with the TypeScript client.

tests/fixtures/unsafe-text/dropped.json lists, as ranges over every code point, what is dropped everywhere (controls,
format characters, lone surrogates, every Default_Ignorable_Code_Point, the braille blank, the null notehead) and
what is dropped only where it splits a token (the space separators). The TypeScript suite checks the same file.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest
from fi.sandbox import channel_errors
from fi.sandbox.channel_errors import clean_server_text

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "unsafe-text" / "dropped.json"
TOKEN = "sct_ABCDEF123456"


def _expand(ranges):
    out = set()
    for lo, hi in ranges:
        out.update(range(int(lo, 16), int(hi, 16) + 1))
    return out


DOC = json.loads(FIXTURE.read_text(encoding="utf-8"))
DROPPED = _expand(DOC["dropped"])
TOKEN_RUN = _expand(DOC["token_run"])

#: Blank or ignorable characters outside the Cc and Cf categories.
NEW_HIDING = [0x2800, 0x1D159, 0x3164, 0x115F, 0x1160, 0xFFA0, 0x2065, 0xE0000, 0x180B, 0x180F, 0x17B4, 0x00A0, 0x3000,
              0x2003, 0x202F, 0x205F, 0x1680, 0x2009, 0x0020]


def _scrub(text: str) -> str:
    return text.replace(TOKEN, "[token]")


@pytest.mark.parametrize("code", NEW_HIDING, ids=lambda c: f"U+{c:04X}")
def test_a_token_split_by_an_invisible_or_space_character_is_scrubbed(code):
    split = TOKEN[:6] + chr(code) + TOKEN[6:]
    out = clean_server_text(f"see {split} now", _scrub)
    assert TOKEN not in out and TOKEN[:6] not in out and "[token]" in out


def test_a_token_split_by_several_characters_at_once_is_scrubbed():
    split = "".join(ch + chr(c) for ch, c in zip(TOKEN, [0x2800, 0x3000, 0x1D159, 0x00A0, 0x3164] * 4))
    assert "[token]" in clean_server_text(split, _scrub)


def test_ordinary_spaces_and_space_separators_outside_a_token_stay():
    assert clean_server_text("two  words and　more", _scrub) == "two  words and　more"
    assert clean_server_text(f"see {TOKEN} now", _scrub) == "see [token] now"


def test_the_drop_predicate_matches_the_shared_table_over_every_code_point():
    wrong = [c for c in range(0x110000)
             if channel_errors.is_unsafe_text_char(chr(c)) != (c in DROPPED)]
    assert wrong == []


def test_the_token_run_predicate_matches_the_shared_table_over_every_code_point():
    wrong = [c for c in range(0x110000)
             if channel_errors.is_token_split_char(chr(c)) != (c in TOKEN_RUN)]
    assert wrong == []


def test_the_table_covers_what_this_interpreters_unicode_data_calls_unsafe():
    gap = [c for c in range(0x110000)
           if unicodedata.category(chr(c)) in ("Cc", "Cf", "Cs") and c not in DROPPED]
    assert gap == []
    assert [c for c in range(0x110000) if unicodedata.category(chr(c)) == "Zs" and c not in TOKEN_RUN] == []


def test_the_cap_counts_code_points():
    text = "a" * 199 + "\U0001F600" + "b"
    out = clean_server_text(text)
    assert out == "a" * 199 + "\U0001F600" and len(out) == 200
