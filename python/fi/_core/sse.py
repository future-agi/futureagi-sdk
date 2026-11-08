"""Server-sent events (the parser is ported from the Omega runtime): an incremental
parser that follows the WHATWG ``text/event-stream`` rules, and frame iteration over a live httpx
response (sync and async).

The parser yields the same frames whatever way the bytes are split: CR, LF and CRLF line ends, a CR
at the end of one chunk and its LF at the start of the next, multi-byte UTF-8 characters split across
chunks, a leading BOM. A frame's ``id`` is set only when its own block had an ``id:`` line, because
the live delta frames omit ``id:`` so that ``Last-Event-ID`` stays on the durable sequence.

Reading a stream: :func:`iter_frames` / :func:`aiter_frames` yield frames and close the response
when the consumer stops. No data within the idle timeout (the response's read timeout) raises
``APITimeoutError``; a dropped connection raises ``APIConnectionError``. Python's standard library
and httpx only: no new dependency.
"""

from __future__ import annotations

import codecs
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Iterator

import httpx

from fi.errors import APIConnectionError, APITimeoutError


@dataclass(frozen=True)
class SseFrame:
    """One dispatched event."""

    #: The event type (``message`` when the block named none).
    event: str
    #: The data lines joined by ``\\n``.
    data: str
    #: The ``id:`` of this block, when it had one.
    id: str | None
    #: The stream's last event id at dispatch (persists across blocks, per the spec).
    last_event_id: str
    #: A ``retry:`` value in this block, in ms.
    retry: int | None = None


class SseParser:
    """An incremental parser over bytes. ``push`` returns the frames completed by a chunk."""

    def __init__(self) -> None:
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._buffer = ""
        self._pending_cr = False
        self._saw_first = False
        self._data: list[str] = []
        self._has_data = False
        self._event = ""
        self._block_id: str | None = None
        self._retry: int | None = None
        self._last_id = ""
        #: Comment lines seen (keepalives).
        self.comments = 0

    def push(self, chunk: bytes) -> list[SseFrame]:
        """Feed bytes; returns the frames they complete."""
        return self._push_text(self._decoder.decode(chunk))

    def end(self) -> list[SseFrame]:
        """End of stream: flush the decoder; an incomplete final block is discarded, per the spec."""
        frames = self._push_text(self._decoder.decode(b"", final=True))
        self._buffer = ""
        self._reset_block()
        return frames

    def _push_text(self, text: str) -> list[SseFrame]:
        if not text:
            return []
        if not self._saw_first:
            self._saw_first = True
            if text.startswith("﻿"):
                text = text[1:]
        if self._pending_cr and text.startswith("\n"):
            text = text[1:]
        self._pending_cr = False
        frames: list[SseFrame] = []
        buffer = self._buffer + text
        start = 0
        i = 0
        while i < len(buffer):
            ch = buffer[i]
            if ch != "\n" and ch != "\r":
                i += 1
                continue
            line = buffer[start:i]
            if ch == "\r":
                if i + 1 < len(buffer):
                    if buffer[i + 1] == "\n":
                        i += 1
                else:
                    self._pending_cr = True
            i += 1
            start = i
            frame = self._line(line)
            if frame is not None:
                frames.append(frame)
        self._buffer = buffer[start:]
        return frames

    def _reset_block(self) -> None:
        self._data = []
        self._has_data = False
        self._event = ""
        self._block_id = None
        self._retry = None

    def _line(self, line: str) -> SseFrame | None:
        if line == "":
            return self._dispatch()
        if line.startswith(":"):
            self.comments += 1
            return None
        field, colon, value = line.partition(":")
        if colon and value.startswith(" "):
            value = value[1:]
        if field == "event":
            self._event = value
        elif field == "data":
            self._data.append(value)
            self._has_data = True
        elif field == "id":
            if "\0" not in value:
                self._block_id = value
                self._last_id = value
        elif field == "retry" and value.isdigit() and value.isascii():
            self._retry = int(value)
        return None

    def _dispatch(self) -> SseFrame | None:
        if not self._has_data:
            self._reset_block()
            return None
        frame = SseFrame(self._event or "message", "\n".join(self._data), self._block_id, self._last_id, self._retry)
        self._reset_block()
        return frame


def decode_frame(frame: SseFrame, known: tuple[str, ...]) -> dict[str, Any]:
    """Decode one frame: its JSON object with ``type`` set, or an unknown event. Never raises.

    An unknown event is ``{"type": "unknown", "eventType": <type>, "raw": <data>}``: a newer server's
    event type never breaks an older SDK's iterator.
    """
    try:
        raw: Any = json.loads(frame.data)
    except ValueError:
        raw = frame.data
    kind = frame.event
    if kind == "message" and isinstance(raw, dict):
        kind = str(raw.get("type", "message"))
    if kind not in known or not isinstance(raw, dict):
        return {"type": "unknown", "eventType": kind, "raw": raw}
    return {**raw, "type": kind}


def _idle(operation: str) -> APITimeoutError:
    err = APITimeoutError(f"{operation}: no data within the stream's idle timeout")
    err.kind, err.possibly_applied, err.operation = "timeout", True, operation
    return err


def _lost(operation: str, error: BaseException) -> APIConnectionError:
    err = APIConnectionError(f"{operation}: the stream's connection was lost ({type(error).__name__})")
    err.kind, err.possibly_applied, err.operation = "connection", True, operation
    return err


def iter_frames(response: httpx.Response, *, operation: str) -> Iterator[SseFrame]:
    """SSE frames from a live response (sync); closes it when the consumer stops."""
    parser = SseParser()
    try:
        for chunk in response.iter_bytes():  # decoded (a gateway may gzip the stream)
            yield from parser.push(chunk)
        yield from parser.end()
    except httpx.ReadTimeout:
        raise _idle(operation) from None
    except httpx.HTTPError as error:
        raise _lost(operation, error) from None
    finally:
        response.close()


async def aiter_frames(response: httpx.Response, *, operation: str) -> AsyncIterator[SseFrame]:
    """SSE frames from a live response (async); closes it when the consumer stops."""
    parser = SseParser()
    try:
        async for chunk in response.aiter_bytes():
            for frame in parser.push(chunk):
                yield frame
        for frame in parser.end():
            yield frame
    except httpx.ReadTimeout:
        raise _idle(operation) from None
    except httpx.HTTPError as error:
        raise _lost(operation, error) from None
    finally:
        await response.aclose()
