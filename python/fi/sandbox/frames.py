"""Typed frames of a command's output stream (the contract's ``OmegaExecFrame``).

The server sends ``started`` first, then any number of ``stdout`` / ``stderr``, then exactly one
``exit`` (or ``error`` when it failed after starting). On the wire each frame is one SSE block::

    event: stdout
    id: 2
    data: {"data": "hello\\n"}

``frame.raw`` keeps the frame as the contract types it (``{"event", "id", "data"}``). An event type
this SDK does not know becomes an :class:`UnknownFrame`, never an error, so a newer server cannot
break an older SDK. The stream is not resumable: the stream *is* the command.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Union

from fi._core.sse import SseFrame

#: The frame types this SDK knows, when the operation table does not say (it normally does).
KNOWN_EVENTS = ("started", "stdout", "stderr", "exit", "error")


@dataclass(frozen=True)
class StartedFrame:
    """The command started; ``exec_id`` is what ``commands.cancel`` takes."""

    id: Optional[str]
    exec_id: str
    sandbox_id: str
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    event: str = field(default="started", init=False)


@dataclass(frozen=True)
class StdoutFrame:
    """Standard output, as the command wrote it (UTF-8). Concatenate in order."""

    id: Optional[str]
    data: str
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    event: str = field(default="stdout", init=False)


@dataclass(frozen=True)
class StderrFrame:
    """Standard error, as the command wrote it (UTF-8). Concatenate in order."""

    id: Optional[str]
    data: str
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    event: str = field(default="stderr", init=False)


@dataclass(frozen=True)
class ExitFrame:
    """The command ended. ``exit_code`` is None when a signal ended it or it never started."""

    id: Optional[str]
    exit_code: Optional[int]
    timed_out: bool = False
    cancelled: bool = False
    truncated: bool = False
    duration_ms: Optional[int] = None
    stdout_bytes: Optional[int] = None
    stderr_bytes: Optional[int] = None
    signal: Optional[str] = None
    error: Optional[str] = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    event: str = field(default="exit", init=False)


@dataclass(frozen=True)
class ErrorFrame:
    """The server failed after the command started."""

    id: Optional[str]
    message: str
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    event: str = field(default="error", init=False)


@dataclass(frozen=True)
class UnknownFrame:
    """An event type this SDK does not know (or a known one with an unreadable body), kept as sent."""

    event: str
    id: Optional[str]
    data: Any
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


ExecFrame = Union[
    StartedFrame, StdoutFrame, StderrFrame, ExitFrame, ErrorFrame, UnknownFrame
]


def _int(value: Any) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def to_frame(sse: SseFrame, known: tuple[str, ...] = KNOWN_EVENTS) -> ExecFrame:
    """One SSE block as a typed frame. Never raises.

    Also accepts a server that puts the whole frame (``{"event", "id", "data"}``) in ``data:``
    under the default ``message`` event."""
    try:
        data: Any = json.loads(sse.data)
    except ValueError:
        data = sse.data
    kind, ident = sse.event, sse.id
    whole = isinstance(data, dict) and isinstance(data.get("event"), str)
    if kind == "message" and whole and "data" in data:
        kind = data["event"]
        ident = data["id"] if isinstance(data.get("id"), str) else ident
        data = data["data"]
    raw = {"event": kind, "id": ident, "data": data}
    if kind not in known or not isinstance(data, dict):
        return UnknownFrame(kind, ident, data, raw)
    if kind == "started" and isinstance(data.get("execId"), str):
        return StartedFrame(ident, data["execId"], str(data.get("sandboxId", "")), raw)
    if kind in ("stdout", "stderr") and isinstance(data.get("data"), str):
        cls = StdoutFrame if kind == "stdout" else StderrFrame
        return cls(ident, data["data"], raw)
    if kind == "exit":
        return ExitFrame(
            ident,
            _int(data.get("exitCode")),
            timed_out=data.get("timedOut") is True,
            cancelled=data.get("cancelled") is True,
            truncated=data.get("truncated") is True,
            duration_ms=_int(data.get("durationMs")),
            stdout_bytes=_int(data.get("stdoutBytes")),
            stderr_bytes=_int(data.get("stderrBytes")),
            signal=data.get("signal") if isinstance(data.get("signal"), str) else None,
            error=data.get("error") if isinstance(data.get("error"), str) else None,
            raw=raw,
        )
    if kind == "error":
        message = data.get("message")
        text = message if isinstance(message, str) else "the command failed"
        return ErrorFrame(ident, text, raw)
    return UnknownFrame(kind, ident, data, raw)


__all__ = [
    "ExecFrame",
    "StartedFrame",
    "StdoutFrame",
    "StderrFrame",
    "ExitFrame",
    "ErrorFrame",
    "UnknownFrame",
    "KNOWN_EVENTS",
    "to_frame",
]
