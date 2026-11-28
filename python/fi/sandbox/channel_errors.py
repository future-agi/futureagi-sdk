"""The exec-channel errors (``commands.exec_stream``), exported from ``fi.sandbox`` and also
reachable as ``fi.sandbox.errors.<Name>``.

``ChannelClosedError`` is raised when the server closes the socket before the command's ``exit``
record, with one subclass per close code (4401 ``ChannelAccessRevokedError``, 4404
``ChannelSandboxGoneError``, 4409 ``ChannelEmergencyStopError``, 4410
``ChannelSandboxHibernatedError``, 4411 ``ChannelSandboxFrozenError``, 1001
``ChannelServerStoppingError``). ``ChannelProtocolError`` is a frame or handshake that breaks the
protocol; ``ChannelStreamEndedError`` is a write to a stream that has ended."""

from __future__ import annotations

from typing import Any, Callable, Optional

from ._unsafe_text import is_dropped, is_token_run
from .errors import SandboxAPIError, SandboxError


class CommandStreamError(SandboxError):
    """Base of the exec-channel errors that are not HTTP answers."""

    _error_code = "CHANNEL_ERROR"


class ChannelClosedError(CommandStreamError):
    """The server closed the channel socket before the command's ``exit`` record. ``close_code`` is
    the WebSocket close code, ``reason`` the contract's stable reason for it (``sandbox_hibernated``)
    and ``server_reason`` the text the server sent with it. A subclass says which: the command was
    stopped, and whether it finished is unknown."""

    close_code: Optional[int] = None
    reason: Optional[str] = None
    server_reason: str = ""
    _error_code = "CHANNEL_CLOSED"


class ChannelAccessRevokedError(ChannelClosedError):
    """4401 ``access_revoked``: the member left the workspace or lost the role, or an
    ``access.revoked`` event named them."""

    _error_code = "CHANNEL_ACCESS_REVOKED"


class ChannelSandboxGoneError(ChannelClosedError):
    """4404 ``sandbox_gone``: the sandbox was destroyed or is not the workspace's."""

    _error_code = "CHANNEL_SANDBOX_GONE"


class ChannelEmergencyStopError(ChannelClosedError):
    """4409 ``emergency_stop``: the workspace's sandboxes are emergency-stopped, paused or halted."""

    _error_code = "CHANNEL_EMERGENCY_STOP"


class ChannelSandboxHibernatedError(ChannelClosedError):
    """4410 ``sandbox_hibernated``: the sandbox hibernated while the socket was open. Open a new
    stream: an exec resumes it as usual."""

    _error_code = "CHANNEL_SANDBOX_HIBERNATED"


class ChannelSandboxFrozenError(ChannelClosedError):
    """4411 ``sandbox_frozen``: the sandbox was frozen (``lifecycle.frozen``)."""

    _error_code = "CHANNEL_SANDBOX_FROZEN"


class ChannelServerStoppingError(ChannelClosedError):
    """1001 ``server_stopping``: the server is shutting down. Try again shortly."""

    _error_code = "CHANNEL_SERVER_STOPPING"


class ChannelProtocolError(CommandStreamError):
    """A frame or a handshake broke the channel protocol (a message too short or too large, a text
    message, a missing ``hello``, a subprotocol the server did not answer)."""

    _error_code = "CHANNEL_PROTOCOL_ERROR"


class ChannelStreamEndedError(CommandStreamError):
    """A write to a stream whose command has ended or whose standard input is closed."""

    _error_code = "CHANNEL_STREAM_ENDED"


#: The class and the plain words for each close code (the words follow the contract's table).
_CLOSES = {
    4401: (ChannelAccessRevokedError, "access revoked: the member left the workspace, lost the role, "
           "or had access to this sandbox revoked"),
    4404: (ChannelSandboxGoneError, "sandbox gone: the sandbox was deleted or is no longer in this "
           "workspace"),
    4409: (ChannelEmergencyStopError, "emergency stop: the workspace's sandboxes were stopped "
           "(emergency stop, paused or halted)"),
    4410: (ChannelSandboxHibernatedError, "sandbox hibernated: the sandbox hibernated while the "
           "command ran; a new command resumes it"),
    4411: (ChannelSandboxFrozenError, "sandbox frozen: the sandbox was frozen"),
    1001: (ChannelServerStoppingError, "server stopping: the server is shutting down; try again "
           "shortly"),
}


SERVER_TEXT_CAP = 200


def is_unsafe_text_char(ch: str) -> bool:
    """Whether a character is dropped from server text everywhere: every control character (Cc), every
    format character (Cf: the bidirectional marks, overrides and isolates, the zero-width and invisible
    characters, the soft hyphen and the tag characters), every surrogate code point (a lone one, which no
    text encoding carries), every Default_Ignorable_Code_Point (the Hangul fillers, the variation
    selectors, the combining grapheme joiner and the unassigned ignorable ranges), the line and paragraph
    separators (U+2028, U+2029), the braille blank (U+2800) and the musical symbol null notehead
    (U+1D159). The set is a written-out table (``_unsafe_text``), not the interpreter's Unicode data, so
    it is the same on every Python and is the TypeScript client's; a shared fixture checks both."""
    return is_dropped(ord(ch))


def is_token_split_char(ch: str) -> bool:
    """Whether a character is a space separator (Zs: U+0020, U+00A0, U+1680, U+2000-U+200A, U+202F,
    U+205F, U+3000). Text keeps these, except inside a span that ``scrub`` rewrites once the space
    separators are taken out."""
    return is_token_run(ord(ch))


def _common_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _next_span(rest: str, scrub: Callable[[str], str]) -> Optional[tuple[int, int, str]]:
    """The first span of ``rest`` that ``scrub`` rewrites, as ``(start, end, rewrite)``, or ``None``.

    The span ends at the shortest prefix ``scrub`` already rewrites, moved on to the end of the match when
    ``scrub`` matches more than that prefix holds; it starts where the rewrite first differs from the text."""
    whole = scrub(rest)
    if whole == rest:
        return None
    low, high = 1, len(rest)  # smallest prefix length that scrub rewrites
    while low < high:
        mid = (low + high) // 2
        if scrub(rest[:mid]) != rest[:mid]:
            high = mid
        else:
            low = mid + 1
    for end in range(low, len(rest) + 1):
        head = scrub(rest[:end])
        if head + scrub(rest[end:]) != whole:
            continue
        start = _common_prefix(rest, head)
        if start >= end:
            return None
        return start, end, head[start:]
    return None


def _scrub_across_spaces(value: str, scrub: Callable[[str], str]) -> str:
    """``scrub(value)``, also finding what a space separator splits. ``scrub`` is run on the text with its
    space separators taken out; each span it rewrites there is replaced in ``value`` by the rewritten text,
    and the space separators inside that span are gone. Every space separator outside those spans stays,
    including the ones between two spans."""
    positions = [i for i, ch in enumerate(value) if not is_token_split_char(ch)]
    if len(positions) == len(value):
        return scrub(value)
    packed = "".join(value[i] for i in positions)
    pieces: list[str] = []
    cursor = base = 0
    while base < len(packed):
        found = _next_span(packed[base:], scrub)
        if found is None:
            break
        start, end, rewrite = found
        first, last = positions[base + start], positions[base + end - 1] + 1
        pieces += [value[cursor:first], rewrite]
        cursor = last
        base += end
    if not pieces:
        return scrub(value)
    pieces.append(value[cursor:])
    return scrub("".join(pieces))


def clean_server_text(text: Any, scrub: Optional[Callable[[str], str]] = None, cap: int = SERVER_TEXT_CAP) -> str:
    """Text a server sent, made safe to show. The unsafe characters (see :func:`is_unsafe_text_char`)
    are dropped first, then the text is scrubbed with ``scrub``. A span that ``scrub`` rewrites only
    once the space separators are taken out is replaced as a whole, and the space separators inside
    it are dropped; the ones outside it are kept. Last the text is cut to ``cap`` characters (code
    points)."""
    value = text if isinstance(text, str) else str(text)
    value = "".join(ch for ch in value if not is_unsafe_text_char(ch))
    if scrub is not None:
        value = _scrub_across_spaces(value, scrub)
    return value[:cap]


def channel_closed(code: int, server_reason: str = "", scrub: Optional[Callable[[str], str]] = None) -> ChannelClosedError:
    """The typed error for a close code: its subclass when the contract names the code, else
    :class:`ChannelClosedError`. Whether the command finished is unknown, and the message says so."""
    from ._channel.constants import CLOSE_REASONS

    server_reason = clean_server_text(server_reason, scrub)

    cls, words = _CLOSES.get(code, (ChannelClosedError, f"the server closed the channel (code {code})"))
    out = cls(f"{words}; the command was stopped and whether it finished is unknown",
              operation="sandboxes.commands.execStream")
    out.close_code, out.reason = code, CLOSE_REASONS.get(code, server_reason or None)
    out.server_reason = server_reason
    out.code = out.reason
    return out


def reworded(error: SandboxAPIError, text: str) -> SandboxAPIError:
    """``error`` again (same class, status, code, detail and ids) with ``text`` as its message."""
    return type(error)(
        error.status_code,
        error.payload,
        detail=error.detail,
        retry_after=error.retry_after,
        request_id=error.request_id,
        code=error.code,
        message=text,
        operation=error.operation,
        upstream_request_id=error.upstream_request_id,
        receipt_id=error.receipt_id,
    )


__all__ = [
    "CommandStreamError",
    "ChannelClosedError",
    "ChannelAccessRevokedError",
    "ChannelSandboxGoneError",
    "ChannelEmergencyStopError",
    "ChannelSandboxHibernatedError",
    "ChannelSandboxFrozenError",
    "ChannelServerStoppingError",
    "ChannelProtocolError",
    "ChannelStreamEndedError",
    "channel_closed",
    "clean_server_text",
    "is_unsafe_text_char",
    "reworded",
]
