"""Responses API streams: typed ``ResponseStreamEvent`` items from ``/v1/responses`` (D-17).

The gateway relays the Responses API's own events (``event: response.created``,
``response.output_text.delta``, ``response.completed``, ...) and ends a stream it
refuses with ``event: error`` and ``data: {"type":"error","code","message","param"}``
(handlers_responses.go, responsesStreamErrorEvent). agentcc 1.x parsed these frames as
chat completion chunks, so every event failed validation.
"""

from __future__ import annotations

import json as _json
from collections.abc import AsyncIterator, Iterator
from typing import Any

from fi.gateway._exceptions import StreamError
from fi.gateway._streaming._sse import AsyncSSEParser, SSEEvent, SSEParser
from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.responses import ResponseObject, ResponseStreamEvent

_DONE = object()


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def responses_error(data: Any, request_id: str | None) -> StreamError:
    """The StreamError for an ``event: error`` frame's data.

    ``type``, ``code``, ``param`` and the message come from the frame, and ``body`` is
    the whole frame. The gateway's frame is flat,
    ``{"type": "error", "code", "message", "param"}``, so ``type`` is ``"error"``. A
    frame that nests the details, ``{"type": "error", "error": {"type", "code",
    "message", "param"}}``, gives the nested values, each falling back to the frame's
    own. A frame that is not an object raises with ``type="error"`` and the frame as
    ``body``. agentcc 1.x parsed these frames as chat chunks (D-17).
    """
    if not isinstance(data, dict):
        return StreamError(
            f"Stream error: {_json.dumps(data, separators=(',', ':'))}",
            type="error",
            body=data,
            request_id=request_id,
        )
    nested = data.get("error")
    nested = nested if isinstance(nested, dict) else {}

    def field(name: str) -> str | None:
        return _str_or_none(nested.get(name)) or _str_or_none(data.get(name))

    message = field("message")
    if not message:
        message = f"Stream error: {_json.dumps(data, separators=(',', ':'))}"
    if field("code") == "wrong_region":
        message = "Gateway request reached the wrong region; check the explicitly configured origin."
    return StreamError(
        message,
        type=field("type") or "error",
        code=field("code"),
        param=field("param"),
        body=data,
        request_id=request_id,
    )


def _event(event: SSEEvent, request_id: str | None) -> Any:
    """One frame's typed event, ``None`` to skip, ``_DONE``, or the StreamError of an error frame."""
    if event.data is None:
        return None
    if event.data == "[DONE]":
        return _DONE
    try:
        data = _json.loads(event.data)
    except _json.JSONDecodeError as e:
        if event.event == "error":
            # An error frame whose data is not JSON is still the gateway refusing.
            return StreamError(
                f"Stream error: {event.data[:200]}",
                type="error",
                body=event.data,
                request_id=request_id,
            )
        raise StreamError(f"Invalid JSON in SSE event: {e}") from e
    if event.event == "error" or (
        isinstance(data, dict) and data.get("type") == "error"
    ):
        return responses_error(data, request_id)
    if not isinstance(data, dict):
        raise StreamError(f"Unexpected Responses stream frame: {event.data[:200]}")
    if "type" not in data and event.event:
        data = {**data, "type": event.event}
    return ResponseStreamEvent.model_validate(data)


def _cache_hit(body: Any) -> ResponseStreamEvent:
    """A JSON answer to a stream request (a cache hit) as one ``response.completed`` event."""
    return ResponseStreamEvent(
        type="response.completed", response=ResponseObject.model_validate(body)
    )


from fi.gateway._streaming._stream import Stream, AsyncStream


class ResponseStream(Stream):
    """Typed Responses events with single-pass iteration and lifecycle callbacks."""

    def __init__(self, response: Any, *, on_chunk: Any = None, on_finish: Any = None) -> None:
        super().__init__(response, ResponseStreamEvent, on_chunk=on_chunk, on_finish=on_finish)

    def _iterate_chunks(self, parser: SSEParser) -> Iterator[ResponseStreamEvent]:
        if self._closed:
            return
        for frame in parser:
            if self._closed:
                return
            item = _event(frame, self._response.headers.get("x-agentcc-request-id"))
            if item is _DONE:
                return
            if isinstance(item, StreamError):
                raise item
            if item is not None:
                yield item

    def _cache_hit_iterator(self, body: Any) -> Iterator[ResponseStreamEvent]:
        if not self._closed:
            yield _cache_hit(body)


class AsyncResponseStream(AsyncStream):
    """Async typed Responses events, retaining accounting on close/exhaustion."""

    def __init__(self, response: Any, *, on_chunk: Any = None, on_finish: Any = None) -> None:
        super().__init__(response, ResponseStreamEvent, on_chunk=on_chunk, on_finish=on_finish)

    async def _async_iterate_chunks(self) -> AsyncIterator[ResponseStreamEvent]:
        if self._closed:
            return
        async for frame in AsyncSSEParser(self._response.aiter_bytes()):
            if self._closed:
                return
            item = _event(frame, self._response.headers.get("x-agentcc-request-id"))
            if item is _DONE:
                return
            if isinstance(item, StreamError):
                raise item
            if item is not None:
                yield item

    async def _async_cache_hit_iterator(self) -> AsyncIterator[ResponseStreamEvent]:
        if self._closed:
            return
        body = await self._response.aread()
        if not self._closed:
            yield _cache_hit(_json.loads(body))
