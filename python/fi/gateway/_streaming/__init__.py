"""Streaming: SSE parsing, chunk streams, the accumulator and the StreamManager.

``fi.gateway._streaming`` provides the exports of the 1.0 streaming module
(``agentcc._streaming``).
"""

from __future__ import annotations

from fi.gateway._streaming._accumulator import ChunkAccumulator, stream_chunk_builder
from fi.gateway._streaming._manager import (
    AsyncStreamManager,
    StreamEvent,
    StreamManager,
)
from fi.gateway._streaming._responses import AsyncResponseStream, ResponseStream
from fi.gateway._streaming._sse import AsyncSSEParser, SSEEvent, SSEParser
from fi.gateway._streaming._stream import AsyncStream, MockStream, Stream

# Keep the released public class identities stable across the internal split.
for _stream_type in (Stream, AsyncStream, StreamManager, AsyncStreamManager):
    _stream_type.__module__ = __name__
del _stream_type

__all__ = [
    "AsyncSSEParser",
    "AsyncStream",
    "AsyncResponseStream",
    "AsyncStreamManager",
    "ChunkAccumulator",
    "MockStream",
    "ResponseStream",
    "SSEEvent",
    "SSEParser",
    "Stream",
    "StreamEvent",
    "StreamManager",
    "stream_chunk_builder",
]
