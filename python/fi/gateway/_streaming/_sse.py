"""Server-Sent Events: one parsed event, and the sync and async byte-stream parsers."""

from __future__ import annotations

import codecs as _codecs
import contextlib
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass


@dataclass
class SSEEvent:
    """One parsed Server-Sent Event."""

    data: str | None = None
    event: str | None = None
    id: str | None = None
    retry: int | None = None


class _EventBuilder:
    """Collects the field lines of one event; both parsers feed it line by line."""

    def __init__(self) -> None:
        self._reset()

    def _reset(self) -> None:
        self.data: list[str] = []
        self.event: str | None = None
        self.id: str | None = None
        self.retry: int | None = None

    def _take(self) -> SSEEvent:
        evt = SSEEvent(
            data="\n".join(self.data), event=self.event, id=self.id, retry=self.retry
        )
        self._reset()
        return evt

    def feed(self, line: str) -> SSEEvent | None:
        """Take one line; return the finished event at an event boundary (an empty line)."""
        if not line:
            return self._take() if self.data else None
        if line.startswith(":"):
            return None  # comment
        if line.startswith("data: "):
            self.data.append(line[6:])
        elif line.startswith("data:"):
            self.data.append(line[5:])
        elif line.startswith("event: "):
            self.event = line[7:]
        elif line.startswith("event:"):
            self.event = line[6:]
        elif line.startswith("id: "):
            self.id = line[4:]
        elif line.startswith("id:"):
            self.id = line[3:]
        elif line.startswith("retry: "):
            with contextlib.suppress(ValueError):
                self.retry = int(line[7:])
        return None

    def flush(self) -> SSEEvent | None:
        """The event still open when the body ends, if it has data."""
        return self._take() if self.data else None


class _Lines:
    """Decode UTF-8 and CR/LF across arbitrary network chunk boundaries."""

    def __init__(self) -> None:
        self.decoder = _codecs.getincrementaldecoder("utf-8")("replace")
        self.pending = ""

    def feed(self, chunk: bytes, *, final: bool = False) -> list[str]:
        self.pending += self.decoder.decode(chunk, final=final)
        lines = []
        start, index = 0, 0
        while index < len(self.pending):
            char = self.pending[index]
            if char not in "\r\n":
                index += 1
                continue
            if char == "\r" and index + 1 == len(self.pending) and not final:
                break
            lines.append(self.pending[start:index])
            index += 1
            if char == "\r" and self.pending[index:index + 1] == "\n":
                index += 1
            start = index
        self.pending = self.pending[start:]
        if final and self.pending:
            lines.append(self.pending)
            self.pending = ""
        return lines


class SSEParser:
    """Parse a byte iterator into SSE events."""

    def __init__(self, byte_stream: Iterator[bytes]) -> None:
        self._byte_stream = byte_stream

    def __iter__(self) -> Iterator[SSEEvent]:
        builder = _EventBuilder()
        lines = _Lines()
        for raw_chunk in self._byte_stream:
            for line in lines.feed(raw_chunk):
                evt = builder.feed(line)
                if evt is not None:
                    yield evt
                    if evt.data == "[DONE]":
                        return
        for line in lines.feed(b"", final=True):
            evt = builder.feed(line)
            if evt is not None:
                yield evt
                if evt.data == "[DONE]":
                    return
        evt = builder.flush()
        if evt is not None:
            yield evt


class AsyncSSEParser:
    """Parse an async byte iterator into SSE events."""

    def __init__(self, byte_stream: AsyncIterator[bytes]) -> None:
        self._byte_stream = byte_stream

    async def __aiter__(self) -> AsyncIterator[SSEEvent]:
        builder = _EventBuilder()
        lines = _Lines()
        async for raw_chunk in self._byte_stream:
            for line in lines.feed(raw_chunk):
                evt = builder.feed(line)
                if evt is not None:
                    yield evt
                    if evt.data == "[DONE]":
                        return
        for line in lines.feed(b"", final=True):
            evt = builder.feed(line)
            if evt is not None:
                yield evt
                if evt.data == "[DONE]":
                    return
        evt = builder.flush()
        if evt is not None:
            yield evt
