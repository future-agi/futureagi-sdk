"""Streaming: SSE parsing, chunk streams, the accumulator and the StreamManager.

The 1.0 module path (``agentcc._streaming``) is kept as this package, so every name it
exported imports from ``fi.gateway._streaming`` as before.
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
