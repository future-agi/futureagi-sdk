"""Dropped everywhere (the same set in the TypeScript client, src/platform/resources/unsafe-text.ts, checked
against tests/fixtures/unsafe-text/dropped.json over every code point): every control character (Cc), every format
character (Cf), every surrogate code point (Cs, a lone one is what a Python str can hold), every
Default_Ignorable_Code_Point (the Hangul fillers, the variation selectors, the combining grapheme joiner, the
unassigned ignorable ranges and more), the line and paragraph separators (U+2028, U+2029), the braille blank
(U+2800) and the musical symbol null notehead (U+1D159). The table is written out, so the set does not depend on the
Unicode data of the interpreter: it includes the characters older data lacks (U+0890, U+0891 and the Egyptian
hieroglyph format controls U+13439-U+1343F).

Dropped only where it splits a token (the same file): every space separator (Zs: U+0020, U+00A0, U+1680,
U+2000-U+200A, U+202F, U+205F, U+3000), which stays in text that carries no token.
"""

from __future__ import annotations

from bisect import bisect_right
from typing import Sequence, Tuple

#: Inclusive code point ranges dropped everywhere.
DROPPED_RANGES: Tuple[Tuple[int, int], ...] = (
    (0x0000, 0x001F), (0x007F, 0x009F), (0x00AD, 0x00AD), (0x034F, 0x034F), (0x0600, 0x0605), (0x061C, 0x061C),
    (0x06DD, 0x06DD), (0x070F, 0x070F), (0x0890, 0x0891), (0x08E2, 0x08E2), (0x115F, 0x1160), (0x17B4, 0x17B5),
    (0x180B, 0x180F), (0x200B, 0x200F), (0x2028, 0x202E), (0x2060, 0x206F), (0x2800, 0x2800), (0x3164, 0x3164),
    (0xD800, 0xDFFF), (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0), (0xFFF0, 0xFFFB),
    (0x110BD, 0x110BD), (0x110CD, 0x110CD), (0x13430, 0x1343F), (0x1BCA0, 0x1BCA3), (0x1D159, 0x1D159),
    (0x1D173, 0x1D17A), (0xE0000, 0xE0FFF),
)

#: Inclusive code point ranges dropped only where they split a token.
TOKEN_RUN_RANGES: Tuple[Tuple[int, int], ...] = (
    (0x0020, 0x0020), (0x00A0, 0x00A0), (0x1680, 0x1680), (0x2000, 0x200A), (0x202F, 0x202F), (0x205F, 0x205F),
    (0x3000, 0x3000),
)

_DROPPED_STARTS = tuple(lo for lo, _ in DROPPED_RANGES)
_TOKEN_RUN_STARTS = tuple(lo for lo, _ in TOKEN_RUN_RANGES)


def _inside(code: int, starts: Sequence[int], ranges: Sequence[Tuple[int, int]]) -> bool:
    index = bisect_right(starts, code) - 1
    return index >= 0 and code <= ranges[index][1]


def is_dropped(code: int) -> bool:
    return _inside(code, _DROPPED_STARTS, DROPPED_RANGES)


def is_token_run(code: int) -> bool:
    return _inside(code, _TOKEN_RUN_STARTS, TOKEN_RUN_RANGES)
