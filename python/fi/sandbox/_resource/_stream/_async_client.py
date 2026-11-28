"""The frames of one running command, read from the exec SSE response (async)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Callable, Mapping, Optional

import httpx

from fi._core.sse import SseParser

from ..._wire import failure_text
from ...errors import CORE_ERRORS, stream_failure, translate
from ...frames import KNOWN_EVENTS, ExecFrame, StartedFrame, private_frame, to_frame

NAME = "sandboxes.commands.run"


def _no_refusal(name: str) -> Optional[BaseException]:
    return None


class AsyncCommandStream:
    """One running command's frames (async): ``async with`` it, ``async for`` over it.

    The request is sent when iteration starts. Closing the stream (leaving ``async with``, or
    its close method) closes the connection, and closing the connection cancels the command
    on the server. It is not retried: another stream is another command. ``exec_id`` is set
    once the ``started`` frame arrives."""

    def __init__(
        self,
        core: Any,
        sandbox_id: str,
        body: Mapping[str, Any],
        refusal: Callable[[str], Optional[BaseException]] = _no_refusal,
        setting: Optional[str] = None,
    ) -> None:
        self._core = core
        self._sandbox_id = sandbox_id
        self._body = dict(body)
        self._refusal = refusal
        self._setting = setting
        self._frames: Any = None
        self._response: Optional[httpx.Response] = None
        self.exec_id: Optional[str] = None
        #: True once the server accepted the command (a response is open).
        self.opened = False

    def __aiter__(self) -> AsyncIterator[ExecFrame]:
        if self._frames is None:
            self._frames = self._read()
        return self._frames

    async def __aenter__(self) -> AsyncCommandStream:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the connection; a command running is cancelled by the server."""
        if self._frames is not None:
            await self._frames.aclose()
        if self._response is not None:
            await self._response.aclose()

    def _take(
        self, sse: Any, known: tuple[str, ...], scrub: Callable[[str], str]
    ) -> ExecFrame:
        """One frame, its server-written failure text scrubbed and capped (``scrub``)."""
        frame = private_frame(to_frame(sse, known), scrub)
        if isinstance(frame, StartedFrame):
            self.exec_id = frame.exec_id
        return frame

    async def _open(self) -> Any:
        failure = self._refusal(NAME)
        if failure is None:
            try:
                return await self._core.open_stream(
                    NAME, path={"id": self._sandbox_id}, body=self._body
                )
            except CORE_ERRORS as error:
                failure = translate(error, NAME, self._setting)
        raise failure  # outside the except block: the error chains nothing

    async def _read(self) -> AsyncIterator[ExecFrame]:
        opened = await self._open()
        self._response, self.opened = opened.response, True
        spec = self._core.operation(NAME).stream
        known = tuple(spec.known_events) if spec and spec.known_events else KNOWN_EVENTS
        parser = SseParser()
        try:
            scrub = failure_text(self._core, NAME, opened.response.request, self._body)
            async for chunk in opened.response.aiter_bytes():
                for sse in parser.push(chunk):
                    yield self._take(sse, known, scrub)
            for sse in parser.end():
                yield self._take(sse, known, scrub)
        except httpx.HTTPError as error:
            raise stream_failure(NAME, error) from None
        finally:
            await opened.response.aclose()


__all__ = ["AsyncCommandStream"]
