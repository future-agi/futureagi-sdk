"""Text a receiver, a tenant or a server supplied, made inert for one line of terminal output or an error message.

A response excerpt, an endpoint's name or a server's refusal can carry characters that rewrite what a terminal or a log
viewer shows: ANSI escape sequences (they start with ESC, or the C1 CSI), carriage returns and line separators that
forge extra lines, and the zero-width and bidi characters behind "Trojan Source" spoofing. The API strips most of them
from what it stores; the SDK escapes them again in everything it prints, so the output stays inert whatever the server
sends. HTML and ``javascript:`` text need nothing: a terminal never runs them.
"""

from __future__ import annotations

from typing import Any


def is_live(code: int) -> bool:
    """True for a code point that :func:`inert` escapes."""
    return (
        code < 0x20  # C0 controls: ESC, CR, LF, BEL, backspace, ...
        or 0x7F <= code <= 0x9F  # DEL and the C1 controls (0x9B is CSI)
        or code == 0x061C  # ARABIC LETTER MARK
        or 0x200B <= code <= 0x200F  # zero-width space, joiners, LRM, RLM
        or 0x2028 <= code <= 0x202E  # line and paragraph separators; bidi embeddings and overrides (RLO is 0x202E)
        or 0x2060 <= code <= 0x2069  # word joiner, invisible operators, bidi isolates
        or code == 0xFEFF  # zero-width no-break space
    )


def inert(text: Any, limit: int = 200) -> str:
    """``text`` as one inert line: every :func:`is_live` character written as ``\\uXXXX``, cut to ``limit``
    characters (an ellipsis marks the cut). ``None`` is the empty string."""
    if text is None:
        return ""
    s = str(text)
    out = [f"\\u{ord(ch):04x}" if is_live(ord(ch)) else ch for ch in s[:limit]]
    return "".join(out) + ("…" if len(s) > limit else "")
