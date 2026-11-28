"""The asyncio exec stream handle (``AsyncExecStream``): one command on one WebSocket.

One reader task feeds :class:`~fi.sandbox._channel.protocol.StreamState`; the caller's coroutines
read, write and wait on a condition. Credit goes both ways: ``write`` waits for the server's stdin
credit, and the output credit is granted back only as the caller reads, so a slow reader stops the
command instead of growing memory. Use one task for ``write`` / ``close_stdin`` and one for
reading."""

from __future__ import annotations

import asyncio
import struct
from typing import Any, AsyncIterator, Callable, Iterable, Optional, Union

from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidStatus

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

Stdin = Union[bytes, bytearray, memoryview, Iterable[bytes], AsyncIterator[bytes]]


class _NoRedirect(ws_connect):
    """The WebSocket connect that answers a 3xx to the upgrade as the refusal it is: the library
    would otherwise follow it and send the offered protocols, token included, to the new address."""

    def process_redirect(self, exc: Exception) -> Exception:
        return exc


class AsyncExecStream:
    """One running command (async): write its standard input, read its standard output and error,
    wait for its exit record.

    ``stdout`` and ``stderr`` share the stream's output credit, so read both (or iterate: chunks
    come in arrival order). ``wait()`` drops output that was not read, so read first. Closing the
    stream (``await close()`` or leaving ``async with``) closes the socket, and the server then
    stops the command. Nothing is retried: another stream is another command."""

    def __init__(self, ws: Any, state: StreamState, plan: ConnectionPlan, scrub: Callable[[str], str]) -> None:
        self._ws, self._state, self._plan, self._scrub = ws, state, plan, scrub
        self._cond = asyncio.Condition()
        self._reader: Optional["asyncio.Task[None]"] = None
        self._feeder: Optional["asyncio.Task[None]"] = None
        self._local_close = False
        self._feed_error: Optional[BaseException] = None

    # -- opening ------------------------------------------------------------------------------

    @classmethod
    async def open(
        cls,
        plan: ConnectionPlan,
        argv: list,
        *,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout_seconds: Optional[int] = None,
        stdin: Optional[Stdin] = None,
        scrub: Callable[[str], str] = lambda text: text,
    ) -> "AsyncExecStream":
        """Connect, wait for ``hello``, send ``exec`` and wait for ``started`` (or the server's
        refusal, raised as the sandbox error for it)."""
        ws = await cls._connect(plan, scrub)
        state = StreamState()
        stream = cls(ws, state, plan, scrub)
        try:
            await stream._handshake(argv, cwd, env, timeout_seconds)
        except BaseException:
            await stream._shut()
            raise
        stream._reader = asyncio.ensure_future(stream._read_loop())
        if stdin is not None:
            stream._feeder = asyncio.ensure_future(stream._feed(stdin))
        return stream

    @staticmethod
    async def _connect(plan: ConnectionPlan, scrub: Callable[[str], str]) -> Any:
        # A failure is built inside the handler and raised after it, so the error carries no context:
        # the library's frames hold the offered protocols, which include the token.
        failure: Optional[BaseException] = None
        dials = localhost_dials(plan.url, asynchronous=True)
        try:
            for index, dial in enumerate(dials):
                try:
                    return await _NoRedirect(
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
        except (TimeoutError, asyncio.TimeoutError, OSError) as error:
            failure = stream_failure(OPERATION, error)
        raise failure

    async def _recv(self, timeout: Optional[float] = None) -> Any:
        if timeout is None:
            return await self._ws.recv()
        return await asyncio.wait_for(self._ws.recv(), timeout)

    async def _handshake(self, argv: list, cwd: Any, env: Any, timeout_seconds: Any) -> None:
        state = self._state
        try:
            state.feed(await self._recv(c.OPEN_TIMEOUT_SECONDS))
            if not state.hello:
                raise ChannelProtocolError("the server did not start the channel with a hello frame")
            await self._ws.send(encode(c.EXEC, state.stream_id, exec_payload(argv, cwd, env, timeout_seconds)))
            while not state.started:
                state.feed(await self._recv(c.OPEN_TIMEOUT_SECONDS))
                if state.error is not None and not state.started:
                    raise stream_refusal(state.error, scrub=self._scrub)
                if state.exit is not None:
                    return  # refused with an exit record (it did not start)
        except ConnectionClosed as error:
            raise self._closed_error(error) from None
        except (TimeoutError, asyncio.TimeoutError) as error:
            raise stream_failure(OPERATION, error) from None

    # -- the reader ---------------------------------------------------------------------------

    def _closed_error(self, error: ConnectionClosed) -> BaseException:
        frame = error.rcvd
        if frame is not None and (frame.code in c.CLOSE_REASONS or frame.code >= 4000):
            return channel_closed(frame.code, frame.reason or "", self._scrub)
        if frame is not None and frame.code in (1000, 1005):
            return CommandIncompleteError(
                f"{OPERATION}: the channel closed before the exit record; whether the command "
                "finished is unknown",
                exec_id=self._state.exec_id,
                operation=OPERATION,
            )
        if frame is not None:
            return channel_closed(frame.code, frame.reason or "", self._scrub)
        return stream_failure(OPERATION, error)

    async def _end(self, error: BaseException) -> None:
        async with self._cond:
            if self._state.closed is None and self._state.exit is None:
                self._state.closed = error
            self._cond.notify_all()

    async def _read_loop(self) -> None:
        try:
            while True:
                message = await self._recv()
                async with self._cond:
                    self._state.feed(message)
                    done = self._state.exit is not None
                    self._cond.notify_all()
                if done:
                    break
        except ConnectionClosed as error:
            if not self._local_close:
                await self._end(self._closed_error(error))
            else:
                await self._end(ChannelStreamEndedError("the stream was closed"))
        except ChannelProtocolError as error:
            await self._end(error)
        except asyncio.CancelledError:
            raise
        except Exception as error:  # a broken transport: reads report it
            await self._end(stream_failure(OPERATION, error))
        finally:
            await self._shut()

    async def _shut(self) -> None:
        try:
            await self._ws.close()
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

    async def _grant(self, n: int) -> None:
        if n:
            await self._send(encode(c.WINDOW_TO_SERVER, self._state.stream_id, struct.pack(">I", n)), quiet=True)

    async def _send(self, message: bytes, *, quiet: bool = False) -> None:
        try:
            await self._ws.send(message)
        except ConnectionClosed as error:
            await self._end(self._closed_error(error))
            if not quiet:
                raise self._ended() from None

    async def _take(self, stream: Optional[str], size: int, timeout: Optional[float]) -> Optional[ExecChunk]:
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout
        async with self._cond:
            while True:
                chunk = self._state.consume(stream, size)
                if chunk is not None:
                    grant = self._state.grant_due()
                    break
                if self._state.finished:
                    if self._state.exit is None:
                        raise self._ended()
                    return None
                remaining = None if deadline is None else deadline - loop.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError("no output within the timeout")
                await self._wait(remaining)
        await self._grant(grant)
        return chunk

    async def _wait(self, remaining: Optional[float]) -> None:
        """Wait on the condition (lock held), for at most ``remaining`` seconds."""
        if remaining is None:
            await self._cond.wait()
            return
        try:
            await asyncio.wait_for(self._cond.wait(), remaining)
        except asyncio.TimeoutError:
            pass

    async def read_stdout(self, size: int = -1, timeout: Optional[float] = None) -> bytes:
        """The next standard output, at most ``size`` bytes (any amount when ``size`` is not
        positive); waits for some. ``b""`` once the stream ended and no stdout is left. A close
        before the exit record raises its typed error."""
        chunk = await self._take("stdout", size, timeout)
        return b"" if chunk is None else chunk.data

    async def read_stderr(self, size: int = -1, timeout: Optional[float] = None) -> bytes:
        """The next standard error: as :meth:`read_stdout`."""
        chunk = await self._take("stderr", size, timeout)
        return b"" if chunk is None else chunk.data

    async def read_output(self, timeout: Optional[float] = None) -> Optional[ExecChunk]:
        """The next chunk of either stream in arrival order, or ``None`` at the end."""
        return await self._take(None, -1, timeout)

    def __aiter__(self) -> AsyncIterator[ExecChunk]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[ExecChunk]:
        while (chunk := await self.read_output()) is not None:
            yield chunk

    # -- writing ------------------------------------------------------------------------------

    async def write(self, data: Union[bytes, bytearray, memoryview]) -> None:
        """Send standard input, in frames of at most 64 KiB and only as far as the server's stdin
        credit allows: it waits while the command is not taking input."""
        view = memoryview(bytes(data))
        while len(view):
            async with self._cond:
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
                    await self._cond.wait()
            await self._send(encode(c.STDIN, self._state.stream_id, bytes(view[:n])))
            view = view[n:]

    async def close_stdin(self) -> None:
        """Half-close: send EOF to the command and continue receiving output while it runs."""
        async with self._cond:
            if self._state.stdin_closed or self._state.finished:
                return
            self._state.stdin_closed = True
        await self._send(encode(c.STDIN_EOF, self._state.stream_id))

    async def _feed(self, source: Stdin) -> None:
        try:
            if isinstance(source, (bytes, bytearray, memoryview)):
                await self.write(bytes(source))
            elif hasattr(source, "__aiter__"):
                async for part in source:  # type: ignore[union-attr]
                    await self.write(part)
            else:
                for part in source:  # type: ignore[union-attr]
                    await self.write(part)
            await self.close_stdin()
        except (ChannelClosedError, ChannelStreamEndedError):
            pass  # the reader reports the close
        except asyncio.CancelledError:
            raise
        except BaseException as error:  # a source that failed: stop the command, report it from wait()
            self._feed_error = error
            await self.cancel()

    # -- ending -------------------------------------------------------------------------------

    async def cancel(self) -> None:
        """Stop the command (TERM, then KILL after the server's grace); ``wait()`` then returns
        the exit record with ``cancelled`` set."""
        if not self._state.finished:
            await self._send(encode(c.CANCEL, self._state.stream_id), quiet=True)

    async def wait(self, timeout: Optional[float] = None) -> ExitFrame:
        """Wait for the exit record and return it. Output that was not read is dropped (it is
        counted as consumed so the command can finish). A close before the record raises its typed
        error (``ChannelClosedError`` and its subclasses)."""
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout
        while True:
            async with self._cond:
                self._state.drop_output()
                grant = self._state.grant_due(force=True)
                if self._state.exit is not None:
                    return self._state.exit
                if self._feed_error is not None:
                    raise self._feed_error
                if self._state.closed is not None:
                    raise self._ended()
                if not grant:
                    remaining = None if deadline is None else deadline - loop.time()
                    if remaining is not None and remaining <= 0:
                        raise TimeoutError("the command did not end within the timeout")
                    await self._wait(remaining)
            await self._grant(grant)

    async def close(self) -> None:
        """Close the socket; a command running is stopped by the server."""
        self._local_close = True
        for task in (self._feeder,):
            if task is not None and not task.done():
                task.cancel()
        await self._shut()
        if self._reader is not None and self._reader is not asyncio.current_task():
            try:
                await asyncio.wait_for(asyncio.shield(self._reader), c.CLOSE_TIMEOUT_SECONDS + 1)
            except (asyncio.TimeoutError, Exception):
                pass
        async with self._cond:
            if self._state.closed is None and self._state.exit is None:
                self._state.closed = ChannelStreamEndedError("the stream was closed")
            self._cond.notify_all()

    async def __aenter__(self) -> "AsyncExecStream":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()


__all__ = ["AsyncExecStream", "ExecChunk"]
