"""The frame codec and the state of one exec stream (no I/O).

:class:`StreamState` counts both directions' credit and holds the output that has arrived and has
not been read. Memory is bounded by the contract's output window, not by a cap here: the server may
send at most ``outputWindowBytes`` more than the reader has granted, and the reader grants back
only what the caller consumed. The two stream handles (``_async`` and ``_sync``) own the socket and
the waiting; they call these methods under their own lock."""

from __future__ import annotations

import json
import struct
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Optional, Tuple

from fi._core.sse import SseFrame

from ..channel_errors import ChannelProtocolError
from ..frames import ErrorFrame, ExitFrame, to_frame
from . import constants as c


def encode(kind: int, stream: int, payload: bytes = b"") -> bytes:
    """One frame as one message."""
    if len(payload) > c.MAX_PAYLOAD_BYTES:
        raise ChannelProtocolError(
            f"a frame payload is at most {c.MAX_PAYLOAD_BYTES} bytes, not {len(payload)}"
        )
    return struct.pack(">BI", kind, stream) + bytes(payload)


def decode(message: Any) -> Tuple[int, int, bytes]:
    """``(type, stream, payload)`` of one message; a text message, one shorter than the header or
    one over the size limit is a protocol error."""
    if not isinstance(message, (bytes, bytearray, memoryview)):
        raise ChannelProtocolError("the server sent a text message; the channel carries binary frames")
    data = bytes(message)
    if len(data) < c.HEADER_BYTES:
        raise ChannelProtocolError(f"a frame is at least {c.HEADER_BYTES} bytes, not {len(data)}")
    if len(data) > c.MAX_MESSAGE_BYTES:
        raise ChannelProtocolError(f"a frame is at most {c.MAX_MESSAGE_BYTES} bytes, not {len(data)}")
    kind, stream = struct.unpack(">BI", data[: c.HEADER_BYTES])
    return kind, stream, data[c.HEADER_BYTES:]


def json_object(payload: bytes, what: str) -> dict:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        value = None
    if not isinstance(value, dict):
        raise ChannelProtocolError(f"the server's {what} frame is not a JSON object")
    return value


def credit(payload: bytes) -> int:
    if len(payload) != 4:
        raise ChannelProtocolError("a window frame holds one 4-byte number")
    return struct.unpack(">I", payload)[0]


@dataclass(frozen=True)
class ExecChunk:
    """A piece of output: ``stream`` is ``"stdout"`` or ``"stderr"``, ``data`` the raw bytes."""

    stream: str
    data: bytes


@dataclass(frozen=True)
class StreamError:
    """An ``error`` frame of the stream: the contract's ``code``, ``message`` and ``detail``."""

    code: str
    message: str
    detail: Any = None


class StreamState:
    """One exec stream's frames in, its credit and its buffered output. Not thread-safe: the
    handle that owns it serializes calls."""

    def __init__(self, stream_id: int = c.EXEC_STREAM_ID) -> None:
        self.stream_id = stream_id
        self.hello: dict = {}
        self.started = False
        self.exec_id: Optional[str] = None
        self.exit: Optional[ExitFrame] = None
        self.error: Optional[StreamError] = None
        #: The error that ended the stream before its ``exit`` record (a close, a broken socket).
        self.closed: Optional[BaseException] = None
        #: How many stdin bytes the server will take (the client's credit).
        self.stdin_credit = c.STDIN_WINDOW_BYTES
        self.stdin_closed = False
        self.chunks: Deque[ExecChunk] = deque()
        self.buffered = 0
        self._consumed = 0  # consumed bytes pending a credit grant

    @property
    def finished(self) -> bool:
        return self.exit is not None or self.closed is not None

    # -- frames in ----------------------------------------------------------------------------

    def feed(self, message: Any) -> None:
        kind, stream, payload = decode(message)
        if kind == c.HELLO and stream == 0:
            self.hello = json_object(payload, "hello")
            window = self.hello.get("stdinWindowBytes")
            if isinstance(window, int) and not self.started:
                self.stdin_credit = window
            return
        if stream != self.stream_id:
            return  # a stream this client did not open
        if kind == c.STARTED:
            info = json_object(payload, "started")
            self.started = True
            self.exec_id = info["execId"] if isinstance(info.get("execId"), str) else None
            window = info.get("stdinWindowBytes")
            if isinstance(window, int):
                self.stdin_credit = window
        elif kind in (c.STDOUT, c.STDERR):
            if payload and self.exit is None:
                self.chunks.append(ExecChunk("stdout" if kind == c.STDOUT else "stderr", payload))
                self.buffered += len(payload)
        elif kind == c.WINDOW_TO_CLIENT:
            self.stdin_credit += credit(payload)
        elif kind == c.EXIT:
            self.exit = self._exit(payload)
        elif kind == c.ERROR:
            body = json_object(payload, "error")
            message = body.get("message")
            self.error = StreamError(
                str(body.get("code") or "internal"),
                message if isinstance(message, str) else "the server refused the stream",
                body.get("detail"),
            )

    @staticmethod
    def _exit(payload: bytes) -> ExitFrame:
        json_object(payload, "exit")
        frame = to_frame(SseFrame(event="exit", data=payload.decode("utf-8"), id=None, last_event_id=""))
        if not isinstance(frame, ExitFrame):
            raise ChannelProtocolError("the server's exit frame has no usable exit record")
        return frame

    def error_frame(self) -> Optional[ErrorFrame]:
        """The stream's ``error`` frame as the typed frame (``None`` when it had none)."""
        if self.error is None:
            return None
        raw = {"event": "error", "id": None, "data": {"code": self.error.code,
                                                       "message": self.error.message,
                                                       "detail": self.error.detail}}
        return ErrorFrame(None, self.error.message, raw)

    # -- output out ---------------------------------------------------------------------------

    def consume(self, stream: Optional[str] = None, size: int = -1) -> Optional[ExecChunk]:
        """The next buffered chunk (of ``stream`` when named; at most ``size`` bytes when ``size``
        is positive), or ``None``. What it returns counts as consumed."""
        for index, chunk in enumerate(self.chunks):
            if stream is not None and chunk.stream != stream:
                continue
            if 0 < size < len(chunk.data):
                head, tail = chunk.data[:size], chunk.data[size:]
                self.chunks[index] = ExecChunk(chunk.stream, tail)
                chunk = ExecChunk(chunk.stream, head)
            else:
                del self.chunks[index]
            self.buffered -= len(chunk.data)
            self._consumed += len(chunk.data)
            return chunk
        return None

    def drop_output(self) -> None:
        """Count every buffered byte as consumed and forget it."""
        self._consumed += self.buffered
        self.chunks.clear()
        self.buffered = 0

    def grant_due(self, *, force: bool = False) -> int:
        """Bytes of output credit to grant the server at this point: what was consumed, once it is a step or
        nothing is left buffered (or when ``force``). Zero once the stream has an exit record."""
        if self.exit is not None:
            self._consumed = 0
            return 0
        due = self._consumed
        if due and (force or due >= c.GRANT_STEP_BYTES or not self.chunks):
            self._consumed = 0
            return due
        return 0

    # -- stdin --------------------------------------------------------------------------------

    def stdin_allowance(self, wanted: int) -> int:
        """How many of ``wanted`` stdin bytes may be sent at this point (at most one payload, at most the
        credit); the caller sends that many and calls :meth:`spend_stdin`."""
        return max(0, min(wanted, c.MAX_PAYLOAD_BYTES, self.stdin_credit))

    def spend_stdin(self, sent: int) -> None:
        self.stdin_credit -= sent


def exec_payload(argv: list, cwd: Optional[str], env: Optional[dict], timeout_seconds: Optional[int]) -> bytes:
    body: dict = {"argv": argv}
    if cwd is not None:
        body["cwd"] = cwd
    if env is not None:
        body["env"] = env
    if timeout_seconds is not None:
        body["timeoutSeconds"] = timeout_seconds
    return json.dumps(body, ensure_ascii=False).encode("utf-8")
