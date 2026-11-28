"""Whether a header value holds a key: the value is searched, in any letter case, as written and as it decodes, so that
the key is found in percent, hex and base64 encodings up to three deep (a Basic credential, percent-encoding of any bytes,
hex, base64 at any offset, an encoding of an encoding) without a list of encoded forms. A value longer than
``MAX_SCANNED_LENGTH`` (64 KiB) characters is not scanned and counts as holding a key. Used by
:func:`fi._core.proxy_routing.carries_credentials`."""
from __future__ import annotations

import binascii
import re
import string
from typing import Iterable, Iterator, Union

# How many decodings deep a value is read: base64 of a percent-encoded Basic credential is three.
_DEPTH = 3
# The longest value, in characters, that is scanned; a longer value counts as holding a key. Real header values are far
# shorter, and the scan of a value this long built to be slow to read takes a fraction of a second.
MAX_SCANNED_LENGTH = 64 * 1024
# The opening of a plain-http refusal that rests on the cap alone: it names the cap and what to do.
UNSCANNED_NOTE = (f"A header value longer than {MAX_SCANNED_LENGTH:,} characters (64 KiB; bytes for a bytes value) is not "
                  "scanned for FI_API_KEY, FI_SECRET_KEY or FI_PLATFORM_TOKEN and counts as holding a key; keep each "
                  f"header value to {MAX_SCANNED_LENGTH:,} characters or fewer, or use an https:// address. ")
_PERCENT = re.compile(r"%[0-9A-Fa-f]{2}")
_UNESCAPED = {"%" + high + low: chr(int(high + low, 16)) for high in string.hexdigits for low in string.hexdigits}
_FROM_URL_SAFE = bytes.maketrans(b"-_", b"+/")
# The characters a decoding reads: percent escapes (``+`` also as a space), hex digits and both base64 alphabets.
_ENCODING_CHARS = frozenset(string.ascii_letters + string.digits + "%+/_-")


def _table(members: Iterable[int]) -> bytes:
    """A ``bytes.translate`` table that writes 1 for each byte in ``members`` and 0 for every other byte."""
    chosen = set(members)
    return bytes(byte in chosen for byte in range(256))


_HEX = _table(string.hexdigits.encode())
_BASE64 = ((_table((string.ascii_letters + string.digits + "+/").encode()), False),
           (_table((string.ascii_letters + string.digits + "-_").encode()), True))


def _runs(data: bytes, table: bytes, least: int) -> Iterator[bytes]:
    """The maximal runs of ``data``, at least ``least`` long, of the bytes that ``table`` writes as 1. Found by byte
    search, in time linear in the size of ``data``."""
    marks = data.translate(table)
    wanted = b"\x01" * least
    start = marks.find(wanted)
    while start >= 0:
        end = marks.find(b"\x00", start + least)
        end = len(marks) if end < 0 else end
        yield data[start:end]
        start = marks.find(wanted, end)


def _percent_decoded(text: str) -> str:
    """``urllib.parse.unquote(text, encoding="latin-1")``: each ``%`` escape read as the byte it names."""
    return _PERCENT.sub(lambda escape: _UNESCAPED[escape[0]], text)


def _decodings(text: str, shortest: int) -> Iterator[Union[str, bytes]]:
    """What ``text`` decodes to: percent-decoded when it holds a ``%`` escape (with and without ``+`` read as a space),
    and the bytes of each hex or base64 run (standard and URL-safe alphabets, padded or not) decoded from each start
    offset of its alphabet's groups. A run too short to decode to ``shortest`` characters is skipped."""
    if "%" in text and _PERCENT.search(text):
        yield _percent_decoded(text)
        if "+" in text:
            yield _percent_decoded(text.replace("+", " "))
    # A character beyond Latin-1 is in no alphabet; it is read as "?", which keeps each run where it is.
    data = text.encode("latin-1", "replace")
    for token in _runs(data, _HEX, 2 * shortest):
        for start in (0, 1):
            piece = token[start:]
            yield binascii.a2b_hex(piece[: len(piece) // 2 * 2])
    for table, url_safe in _BASE64:
        for token in _runs(data, table, -(-4 * shortest // 3)):
            token = token.translate(_FROM_URL_SAFE) if url_safe else token
            for start in range(4):
                piece = token[start:]
                piece = piece[: len(piece) - (len(piece) % 4 == 1)]
                yield binascii.a2b_base64(piece + b"=" * (-len(piece) % 4))


def _kept(decoded: Union[str, bytes], table: bytes, shortest: int) -> Iterator[str]:
    """The parts of ``decoded`` read further, one character per byte (Latin-1): its runs, at least ``shortest`` long, of
    the bytes ``table`` keeps. A text with a character beyond Latin-1 is read whole."""
    if isinstance(decoded, str):
        try:
            decoded = decoded.encode("latin-1")
        except UnicodeEncodeError:
            yield decoded
            return
    for run in _runs(decoded, table, shortest):
        yield run.decode("latin-1")


def holds_key(text: str, keys: Iterable[str]) -> bool:
    """Whether ``text`` holds one of ``keys`` in any letter case, as written (a space also as ``+``) or in what it decodes
    to, read up to ``_DEPTH`` decodings deep (see :func:`_decodings`). Deterministic; no key means ``False``. A ``text``
    longer than :data:`MAX_SCANNED_LENGTH` characters is not read and counts as holding a key.

    What a value decodes to is read in its runs of characters that are in a key (any letter case) or that a decoding
    reads, each at least as long as the shortest key: a key, and each encoding a key can be read from, lies inside one
    such run, and the bytes between the runs (most of what random data decodes to) are not decoded again. The time taken
    is then linear in the size of ``text``, and bounded by the cap."""
    forms = (form for key in keys for form in (key, key.encode("utf-8", "surrogateescape").decode("latin-1")))
    needles = {written.lower() for form in forms for written in (form, form.replace(" ", "+"))}
    if not needles:
        return False
    if len(text) > MAX_SCANNED_LENGTH:
        return True
    shortest = min(len(needle) for needle in needles)
    letters = set("".join(needles))
    kept = _table(byte for byte in range(256) if chr(byte) in _ENCODING_CHARS or chr(byte).lower() in letters)
    # Each text is kept with the fewest decodings that reached it, so a text reached again in fewer is read again.
    seen, pending = {text: 0}, [(text, 0)]
    while pending:
        current, depth = pending.pop()
        lowered = current.lower()
        if any(needle in lowered for needle in needles):
            return True
        if depth == _DEPTH:
            continue
        for decoded in _decodings(current, shortest):
            for run in _kept(decoded, kept, shortest):
                if seen.get(run, _DEPTH + 1) > depth + 1:
                    seen[run] = depth + 1
                    pending.append((run, depth + 1))
    return False


class CredentialJudgement:
    """What :func:`fi._core.proxy_routing.judge_credentials` found in a request's headers. ``carried`` is the answer of
    :func:`fi._core.proxy_routing.carries_credentials`. :meth:`only_unscanned` says whether they carry a key only
    because a value is longer than :data:`MAX_SCANNED_LENGTH`; it is asked for a refusal's message, and reads only the
    values the first pass left unread."""

    def __init__(self, carried: bool, keys: tuple[str, ...] = (), unread: tuple[str, ...] = (),
                 over_cap: bool = False) -> None:
        self.carried = carried
        self._keys, self._unread, self._over_cap = keys, unread, over_cap

    def only_unscanned(self) -> bool:
        """Whether a value over the cap is the only reason the headers carry a key: no credential header, and no value
        up to the cap holds a key. ``False`` for headers that cannot be read."""
        if not self._over_cap:
            return False
        try:
            return not any(holds_key(text, list(self._keys)) for text in self._unread)
        except Exception:
            return False


def unscanned_note(headers: object) -> str:
    """:data:`UNSCANNED_NOTE` when ``headers`` carry a key (:func:`fi._core.proxy_routing.carries_credentials`) only
    because a value is longer than :data:`MAX_SCANNED_LENGTH`: no credential header, and no value up to that length holds
    ``FI_API_KEY``, ``FI_SECRET_KEY`` or ``FI_PLATFORM_TOKEN``. Else ``""``, and ``""`` for headers that cannot be read.
    A judgement that has read the headers asks its :class:`CredentialJudgement` instead."""
    from fi._core.proxy_routing import judge_credentials

    judgement = judge_credentials(headers)
    return UNSCANNED_NOTE if judgement.carried and judgement.only_unscanned() else ""
