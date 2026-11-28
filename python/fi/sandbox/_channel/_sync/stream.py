"""The blocking exec stream handle (``ExecStream``): one command on one WebSocket.

One reader thread feeds :class:`~fi.sandbox._channel.protocol.StreamState` under a condition
variable; the caller's thread reads, writes and waits. Credit goes both ways: ``write`` waits for
the server's stdin credit, and the output credit is granted back only as the caller reads, so a
slow reader stops the command instead of growing memory. Use one thread for ``write`` /
``close_stdin`` and one for reading.
"""

from __future__ import annotations

import socket
import struct
import threading
import time
from typing import Any, Callable, Iterable, Iterator, Optional, Union

from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidStatus
from websockets.sync.client import connect as ws_connect

from ...channel_errors import (
    ChannelClosedError,
    ChannelProtocolError,
    ChannelStreamEndedError,
    channel_closed,
)
from ...errors import CommandFailedError, CommandIncompleteError, stream_failure
from ...frames import ExitFrame
from .. import constants as c
from ..connect import OPERATION, ConnectionPlan, keepalive_options, localhost_dials, next_address_may_answer, proxy_options, refusal, socket_logger, stream_refusal
from ..protocol import ExecChunk, StreamState, encode, exec_payload
from ._redirect import NoRedirectConnect, no_redirect_class  # noqa: F401  (no_redirect_class: the import check)

Stdin = Union[bytes, bytearray, memoryview, Iterable[bytes]]




def _connector(url: str, **options: Any) -> Any:
    """The sync WebSocket connect that does not follow a redirect. websockets 16 does not follow one,
    and has no redirecting class: its plain ``connect`` is used."""
    if NoRedirectConnect is None:
        return ws_connect(url, **options)
    return NoRedirectConnect(url, **options).connect()


class ExecStream:
    """One running command: write its standard input, read its standard output and error, wait for
    its exit record.

    ``stdout`` and ``stderr`` share the stream's output credit, so read both (or iterate: chunks
    come in arrival order). ``wait()`` drops output that was not read, so read first. Closing the
    stream (``close()`` or leaving ``with``) closes the socket, and the server then stops the
    command. Nothing is retried: another stream is another command."""

    def __init__(self, ws: Any, state: StreamState, plan: ConnectionPlan, scrub: Callable[[str], str]) -> None:
        self._ws, self._state, self._plan, self._scrub = ws, state, plan, scrub
        self._cond = threading.Condition()
        self._reader: Optional[threading.Thread] = None
        self._feeder: Optional[threading.Thread] = None
        self._local_close = False
        self._feed_error: Optional[BaseException] = None

    # -- opening ------------------------------------------------------------------------------

    @classmethod
    def open(
        cls,
        plan: ConnectionPlan,
        argv: list,
        *,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout_seconds: Optional[int] = None,
        stdin: Optional[Stdin] = None,
        scrub: Callable[[str], str] = lambda text: text,
    ) -> "ExecStream":
        """Connect, wait for ``hello``, send ``exec`` and wait for ``started`` (or the server's
        refusal, raised as the sandbox error for it)."""
        ws = cls._connect(plan, scrub)
        state = StreamState()
        stream = cls(ws, state, plan, scrub)
        try:
            stream._handshake(argv, cwd, env, timeout_seconds)
        except BaseException:
            stream._shut()
            raise
        stream._reader = threading.Thread(target=stream._read_loop, name="fi-sandbox-channel", daemon=True)
        stream._reader.start()
        if stdin is not None:
            stream._feeder = threading.Thread(target=stream._feed, args=(stdin,), name="fi-sandbox-stdin", daemon=True)
            stream._feeder.start()
        return stream

    @staticmethod
    def _connect(plan: ConnectionPlan, scrub: Callable[[str], str]) -> Any:
        # A failure is built inside the handler and raised after it, so the error carries no context:
        # the library's frames hold the offered protocols, which include the token.
        failure: Optional[BaseException] = None
        dials = localhost_dials(plan.url, asynchronous=False)
        try:
            for index, dial in enumerate(dials):
                try:
                    connection = _connector(
                        plan.url,
                        subprotocols=plan.protocols,
                        origin=plan.origin,
                        compression=None,
                        max_size=c.MAX_MESSAGE_BYTES,
                        open_timeout=c.OPEN_TIMEOUT_SECONDS,
                        close_timeout=c.CLOSE_TIMEOUT_SECONDS,
                        logger=socket_logger(),
                        **keepalive_options(ws_connect),
                        **proxy_options(ws_connect, plan.url),
                        **dial,
                    )
                    # The handle owns the socket's life (close() ends it), so it enters the connection
                    # once here: websockets 17 warns about a connection that was not entered, and
                    # entering returns the same connection in 16 and 17.
                    return connection.__enter__()
                except OSError as error:
                    if index + 1 < len(dials) and next_address_may_answer(error):
                        continue
                    raise
        except InvalidStatus as error:
            response = error.response
            failure = refusal(response.status_code, response.body, response.headers, scrub)
        except InvalidHandshake as error:
            failure = ChannelProtocolError(
                f"the channel handshake failed ({type(error).__name__}); the server did not answer "
                f"the {c.SUBPROTOCOL} protocol"
            )
        except (TimeoutError, socket.timeout) as error:
            failure = stream_failure(OPERATION, error)
        except OSError as error:
            failure = stream_failure(OPERATION, error)
        raise failure

    def _recv(self, timeout: Optional[float] = None) -> Any:
        return self._ws.recv(timeout=timeout)

    def _handshake(self, argv: list, cwd: Any, env: Any, timeout_seconds: Any) -> None:
        state = self._state
        try:
            state.feed(self._recv(c.OPEN_TIMEOUT_SECONDS))
            if not state.hello:
                raise ChannelProtocolError("the server did not start the channel with a hello frame")
            self._ws.send(encode(c.EXEC, state.stream_id, exec_payload(argv, cwd, env, timeout_seconds)))
            while not state.started:
                state.feed(self._recv(c.OPEN_TIMEOUT_SECONDS))
                if state.error is not None and not state.started:
                    raise stream_refusal(state.error, scrub=self._scrub)
                if state.exit is not None:
                    return  # refused with an exit record (it did not start)
        except ConnectionClosed as error:
            raise self._closed_error(error) from None
        except TimeoutError as error:
            raise stream_failure(OPERATION, error) from None

    # -- the reader ---------------------------------------------------------------------------

    def _closed_error(self, error: ConnectionClosed) -> BaseException:
        frame = error.rcvd
        if frame is not None and (frame.code in c.CLOSE_REASONS or frame.code >= 4000):
            return channel_closed(frame.code, frame.reason or "", self._scrub)
        if frame is not None and frame.code in (1000, 1001, 1005):
            return CommandIncompleteError(
                f"{OPERATION}: the channel closed before the exit record; whether the command "
                "finished is unknown",
                exec_id=self._state.exec_id,
                operation=OPERATION,
            )
        if frame is not None:
            return channel_closed(frame.code, frame.reason or "", self._scrub)
        return stream_failure(OPERATION, error)

    def _end(self, error: BaseException) -> None:
        with self._cond:
            if self._state.closed is None and self._state.exit is None:
                self._state.closed = error
            self._cond.notify_all()

    def _read_loop(self) -> None:
        try:
            while True:
                message = self._recv()
                with self._cond:
                    self._state.feed(message)
                    done = self._state.exit is not None
                    self._cond.notify_all()
                if done:
                    break
        except ConnectionClosed as error:
            if not self._local_close:
                self._end(self._closed_error(error))
            else:
                self._end(ChannelStreamEndedError("the stream was closed"))
        except ChannelProtocolError as error:
            self._end(error)
        except Exception as error:  # a broken transport, not a bug to hide: reads report it
            self._end(stream_failure(OPERATION, error))
        finally:
            self._shut()

    def _shut(self) -> None:
        try:
            self._ws.close()
        except Exception:
            pass

    # -- failures a caller sees ---------------------------------------------------------------

    def _ended(self) -> BaseException:
        """The error for a stream that ended without an exit record."""
        state = self._state
        error = state.closed
        if isinstance(error, ChannelStreamEndedError):
            return error
        if state.error is not None and not isinstance(error, ChannelClosedError):
            failed = CommandFailedError(
                f"{OPERATION}: {state.error.code}: {state.error.message}; whether the command "
                "finished is unknown",
                exec_id=state.exec_id,
                operation=OPERATION,
            )
            failed.code, failed.detail = state.error.code, state.error.detail
            return failed
        return error if error is not None else ChannelStreamEndedError("the stream has ended")

    # -- reading ------------------------------------------------------------------------------

    @property
    def exec_id(self) -> Optional[str]:
        """The id the exec routes (``commands.cancel``, ``processes``) use; set once started."""
        return self._state.exec_id

    @property
    def exit(self) -> Optional[ExitFrame]:
        """The exit record once it arrived, else ``None``."""
        return self._state.exit

    @property
    def buffered_bytes(self) -> int:
        """Output that arrived and has not been read: at most the server's output window."""
        return self._state.buffered

    def _grant(self, n: int) -> None:
        if n:
            self._send(encode(c.WINDOW_TO_SERVER, self._state.stream_id, struct.pack(">I", n)), quiet=True)

    def _send(self, message: bytes, *, quiet: bool = False) -> None:
        try:
            self._ws.send(message)
        except ConnectionClosed as error:
            self._end(self._closed_error(error))
            if not quiet:
                raise self._ended() from None

    def _take(self, stream: Optional[str], size: int, timeout: Optional[float]) -> Optional[ExecChunk]:
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._cond:
            while True:
                chunk = self._state.consume(stream, size)
                if chunk is not None:
                    grant = self._state.grant_due()
                    break
                if self._state.finished:
                    if self._state.exit is None:
                        raise self._ended()
                    return None
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError("no output within the timeout")
                self._cond.wait(remaining)
        self._grant(grant)
        return chunk

    def read_stdout(self, size: int = -1, timeout: Optional[float] = None) -> bytes:
        """The next standard output, at most ``size`` bytes (any amount when ``size`` is not
        positive); waits for some. ``b""`` once the stream ended and no stdout is left. A close
        before the exit record raises its typed error."""
        chunk = self._take("stdout", size, timeout)
        return b"" if chunk is None else chunk.data

    def read_stderr(self, size: int = -1, timeout: Optional[float] = None) -> bytes:
        """The next standard error: as :meth:`read_stdout`."""
        chunk = self._take("stderr", size, timeout)
        return b"" if chunk is None else chunk.data

    def read_output(self, timeout: Optional[float] = None) -> Optional[ExecChunk]:
        """The next chunk of either stream in arrival order, or ``None`` at the end."""
        return self._take(None, -1, timeout)

    def __iter__(self) -> Iterator[ExecChunk]:
        while (chunk := self.read_output()) is not None:
            yield chunk

    # -- writing ------------------------------------------------------------------------------

    def write(self, data: Union[bytes, bytearray, memoryview]) -> None:
        """Send standard input, in frames of at most 64 KiB and only as far as the server's stdin
        credit allows: it waits while the command is not taking input."""
        view = memoryview(bytes(data))
        while len(view):
            with self._cond:
                while True:
                    state = self._state
                    if state.closed is not None and state.exit is None:
                        raise self._ended()
                    if state.exit is not None or state.stdin_closed:
                        raise ChannelStreamEndedError(
                            "cannot write: the command has ended or its standard input is closed"
                        )
                    n = state.stdin_allowance(len(view))
                    if n:
                        state.spend_stdin(n)
                        break
                    self._cond.wait()
            self._send(encode(c.STDIN, self._state.stream_id, bytes(view[:n])))
            view = view[n:]

    def close_stdin(self) -> None:
        """Half-close: send end of input and continue receiving output while the command runs."""
        with self._cond:
            if self._state.stdin_closed or self._state.finished:
                return
            self._state.stdin_closed = True
        self._send(encode(c.STDIN_EOF, self._state.stream_id))

    def _feed(self, source: Stdin) -> None:
        try:
            parts = [bytes(source)] if isinstance(source, (bytes, bytearray, memoryview)) else source
            for part in parts:
                self.write(part)
            self.close_stdin()
        except ChannelClosedError:
            pass  # the reader reports the close
        except ChannelStreamEndedError:
            pass
        except BaseException as error:  # a source that failed: stop the command, report it from wait()
            self._feed_error = error
            self.cancel()

    # -- ending -------------------------------------------------------------------------------

    def cancel(self) -> None:
        """Stop the command (TERM, then KILL after the server's grace); ``wait()`` then returns
        the exit record with ``cancelled`` set."""
        if not self._state.finished:
            self._send(encode(c.CANCEL, self._state.stream_id), quiet=True)

    def wait(self, timeout: Optional[float] = None) -> ExitFrame:
        """Wait for the exit record and return it. Output that was not read is dropped (it is
        counted as consumed so the command can finish). A close before the record raises its typed
        error (``ChannelClosedError`` and its subclasses)."""
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            with self._cond:
                self._state.drop_output()
                grant = self._state.grant_due(force=True)
                if self._state.exit is not None:
                    return self._state.exit
                if self._feed_error is not None:
                    raise self._feed_error
                if self._state.closed is not None:
                    raise self._ended()
                if not grant:
                    remaining = None if deadline is None else deadline - time.monotonic()
                    if remaining is not None and remaining <= 0:
                        raise TimeoutError("the command did not end within the timeout")
                    self._cond.wait(remaining)
            self._grant(grant)

    def close(self) -> None:
        """Close the socket; a command running is stopped by the server."""
        self._local_close = True
        self._shut()
        if self._reader is not None and self._reader is not threading.current_thread():
            self._reader.join(c.CLOSE_TIMEOUT_SECONDS + 1)
        with self._cond:
            if self._state.closed is None and self._state.exit is None:
                self._state.closed = ChannelStreamEndedError("the stream was closed")
            self._cond.notify_all()

    def __enter__(self) -> "ExecStream":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


__all__ = ["ExecStream", "ExecChunk"]
