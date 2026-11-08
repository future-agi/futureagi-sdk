"""Resumable event streams: run events and deployment build logs.

- Resume after the last durable sequence with ``Last-Event-ID`` (only frames with an ``id:`` line
  advance it; live delta frames have none), and drop repeats by sequence, so a reconnect loses
  nothing and repeats nothing.
- Reconnect across drops and the server's stream cap with a fresh request, within bounds: at most
  ``max_consecutive_failures`` (10) failed reconnects in a row, where a reconnect that delivers no
  new durable sequence counts as a failure; a 401, 403 or 404 on reconnect is terminal; a total
  budget per iterator (``max_reconnects``, 200) and an optional wall-clock cap. A spent budget
  raises ``StreamInterruptedError(last_sequence=...)``.
- Transport ``auto`` starts with SSE and switches to long-poll (``?transport=poll&wait=25000``)
  after two SSE attempts that produced no byte (a buffering proxy); ``sse`` and ``poll`` force one.
- Delta reconciliation (ported from the Omega runtime): every ``message_delta.delta`` and
  ``activity_output.chunk`` yielded is a new increment. On a new connection the server re-seeds
  each open message with its cumulative text; only the unseen remainder is yielded, and a message
  the server regenerated becomes ``message_reset {messageId, text}``. A rolling activity tail
  whose head was dropped yields the non-overlapping rest (``truncated: True`` with no overlap).

Unknown event types are yielded as ``{"type": "unknown", ...}``, never raised.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Iterator, Literal, Mapping, Optional

from fi._core.sse import aiter_frames, decode_frame, iter_frames
from fi.errors import (
    ConfigurationError,
    FutureAGIAPIError,
    FutureAGIError,
    StreamInterruptedError,
)

SSE_ATTEMPTS_BEFORE_POLL = 2
BASE_DELAY_S, MAX_DELAY_S = 0.5, 8.0


def _key(event: dict[str, Any]) -> Optional[tuple[str, str]]:
    if (
        event.get("type") == "message_delta"
        and isinstance(event.get("messageId"), str)
        and isinstance(event.get("delta"), str)
    ):
        return f"m:{event['messageId']}", event["delta"]
    if (
        event.get("type") == "activity_output"
        and isinstance(event.get("stepId"), str)
        and isinstance(event.get("chunk"), str)
    ):
        return f"a:{event['stepId']}:{event.get('stream')}", event["chunk"]
    return None


def _overlap(delivered: str, snapshot: str) -> int:
    for n in range(min(len(delivered), len(snapshot)), 0, -1):
        if delivered.endswith(snapshot[:n]):
            return n
    return 0


class DeltaReconciler:
    """Tracks the text delivered per open message and output stream, across reconnects."""

    def __init__(self) -> None:
        self._delivered: dict[str, str] = {}
        self._seeded: set[str] = set()

    def new_connection(self) -> None:
        """A new connection opened: the next frame per key may be a cumulative snapshot."""
        self._seeded = set()

    def push(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Reconcile one event; returns the events to yield (none, one, or a reset)."""
        if event.get("type") == "message_complete":
            message = event.get("message")
            if isinstance(message, dict) and isinstance(message.get("id"), str):
                self._delivered.pop(f"m:{message['id']}", None)
            return [event]
        keyed = _key(event)
        if keyed is None:
            return [event]
        key, text = keyed
        before = self._delivered.get(key, "")
        first = key not in self._seeded
        self._seeded.add(key)
        if not first or before == "":
            self._delivered[key] = before + text
            return [event] if text else []
        if text.startswith(before):
            rest = text.replace(before, "", 1)
            self._delivered[key] = text
            return [self._with_text(event, rest)] if rest else []
        if event.get("type") == "message_delta":
            self._delivered[key] = text
            return [{"type": "message_reset", "messageId": event["messageId"], "text": text}]
        shared = _overlap(before, text)
        rest = text[shared:]
        self._delivered[key] = before + rest
        if not rest:
            return []
        out = self._with_text(event, rest)
        return [{**out, "truncated": True} if shared == 0 else out]

    @staticmethod
    def _with_text(event: dict[str, Any], text: str) -> dict[str, Any]:
        return {**event, "delta": text} if event.get("type") == "message_delta" else {**event, "chunk": text}


@dataclass(frozen=True)
class StreamBounds:
    """Reconnect bounds and transport (seconds)."""

    idle_timeout: Optional[float] = None
    max_reconnects: int = 200
    max_consecutive_failures: int = 10
    max_stream_duration: Optional[float] = None
    transport: Literal["auto", "sse", "poll"] = "auto"
    #: The long-poll window, at most the contract's maximum.
    poll_wait: float = 25.0
    reconcile_deltas: bool = True


def backoff(failures: int, rand: Callable[[], float] = random.random) -> float:
    """Full-jitter exponential backoff: random in [0, min(8, 0.5 * 2**n))."""
    return float(rand()) * min(MAX_DELAY_S, BASE_DELAY_S * 2.0**failures)


def _after(seq: str, last: Optional[str]) -> bool:
    if last is None:
        return True
    if seq.strip().isdigit() and last.strip().isdigit():
        return int(seq) > int(last)
    return seq != last


def _terminal(error: BaseException) -> bool:
    return isinstance(error, FutureAGIAPIError) and error.status_code in (401, 403, 404)


class _State:
    """The loop state both twins share; ``attempt()`` and ``after()`` bracket one connection."""

    def __init__(
        self,
        core: Any,
        name: str,
        query: Optional[Mapping[str, Any]],
        last: Optional[str],
        bounds: Optional[StreamBounds],
    ) -> None:
        op = core.operation(name)
        spec = op.stream
        if spec is None or spec.resume != "last-event-id":
            raise ConfigurationError(f"{name} is not a resumable stream", code="not_resumable", operation=name)
        self.name, self.spec, self.query = name, spec, dict(query or {})
        self.limits = bounds or StreamBounds()
        self.idle = core.settings.stream_idle_timeout if self.limits.idle_timeout is None else self.limits.idle_timeout
        self.poll_wait = min(self.limits.poll_wait, (spec.poll_max_wait_ms or 25_000) / 1000)
        self.reconciler = DeltaReconciler() if self.limits.reconcile_deltas else None
        self.started, self.last = time.monotonic(), last
        self.mode = "poll" if self.limits.transport == "poll" and spec.poll_param else "sse"
        self.silent_sse = self.failures = self.reconnects = 0
        self.new_durable = self.saw_byte = False
        self.attempt_started = 0.0
        self.error: Optional[BaseException] = None

    def attempt(self) -> dict[str, Any]:
        self.new_durable = self.saw_byte = False
        self.error = None
        self.attempt_started = time.monotonic()
        if self.reconciler is not None:
            self.reconciler.new_connection()
        params = dict(self.query)
        if self.mode == "poll" and self.spec.poll_param:
            params[self.spec.poll_param] = self.spec.poll_value
            if self.spec.poll_wait_param:
                params[self.spec.poll_wait_param] = int(self.poll_wait * 1000)
        return {
            "query": params,
            "headers": {"Last-Event-ID": self.last} if self.last else None,
            "idle_timeout": self.idle + self.poll_wait if self.mode == "poll" else self.idle,
        }

    def frame(self, frame: Any) -> Optional[list[dict[str, Any]]]:
        """The events to yield for one frame; None for a repeat."""
        self.saw_byte = True
        if frame.id is not None:
            if not _after(frame.id, self.last):
                return None
            self.last, self.new_durable = frame.id, True
        event = decode_frame(frame, self.spec.known_events)
        return self.reconciler.push(event) if self.reconciler is not None else [event]

    def failed(self, error: FutureAGIError) -> None:
        if _terminal(error):
            raise error
        self.error = error

    def after(self) -> float:
        """Account for one finished connection; the delay before the next, or raise when spent."""
        limits = self.limits
        if self.mode == "sse" and not self.saw_byte:
            self.silent_sse += 1
        if (
            limits.transport == "auto"
            and self.spec.poll_param
            and self.mode == "sse"
            and self.silent_sse >= SSE_ATTEMPTS_BEFORE_POLL
        ):
            self.mode = "poll"
        quiet_poll = self.mode == "poll" and self.error is None and time.monotonic() - self.attempt_started >= 1.0
        self.failures = 0 if self.new_durable or quiet_poll else self.failures + 1
        self.reconnects += 1
        over = limits.max_stream_duration is not None and time.monotonic() - self.started >= limits.max_stream_duration
        if self.failures >= limits.max_consecutive_failures or self.reconnects > limits.max_reconnects or over:
            why = (
                "its time cap"
                if over
                else f"{self.failures} reconnects in a row that delivered nothing new"
                if self.failures >= limits.max_consecutive_failures
                else f"{limits.max_reconnects} reconnects"
            )
            raise StreamInterruptedError(
                f"{self.name} stopped after {why}; resume from last_sequence",
                last_sequence=self.last,
                operation=self.name,
            ) from self.error
        return backoff(self.failures - 1) if self.failures > 0 else 0.0


def resumable_events_sync(
    core: Any,
    name: str,
    *,
    path: Optional[Mapping[str, Any]] = None,
    query: Optional[Mapping[str, Any]] = None,
    is_end: Callable[[dict[str, Any]], bool] = lambda event: False,
    last_event_id: Optional[str] = None,
    bounds: Optional[StreamBounds] = None,
) -> Iterator[dict[str, Any]]:
    """Iterate a resumable stream's decoded events (sync; the module docstring has the rules)."""
    state = _State(core, name, query, last_event_id, bounds)
    sleep = core.shared.sleep or time.sleep
    while True:
        try:
            opened = core.open_stream(name, path=path, **state.attempt())
            frames = iter_frames(opened.response, operation=name)
            try:
                for frame in frames:
                    for item in state.frame(frame) or ():
                        yield item
                        if item["type"] != "unknown" and is_end(item):
                            return
            finally:
                frames.close()  # closes the response, also when the consumer stops early
        except FutureAGIError as error:
            state.failed(error)
        delay = state.after()
        if delay:
            sleep(delay)


async def resumable_events(
    core: Any,
    name: str,
    *,
    path: Optional[Mapping[str, Any]] = None,
    query: Optional[Mapping[str, Any]] = None,
    is_end: Callable[[dict[str, Any]], bool] = lambda event: False,
    last_event_id: Optional[str] = None,
    bounds: Optional[StreamBounds] = None,
) -> AsyncIterator[dict[str, Any]]:
    """Iterate a resumable stream's decoded events (async twin of :func:`resumable_events_sync`)."""
    state = _State(core, name, query, last_event_id, bounds)
    while True:
        try:
            opened = await core.open_stream(name, path=path, **state.attempt())
            aframes = aiter_frames(opened.response, operation=name)
            try:
                async for frame in aframes:
                    for item in state.frame(frame) or ():
                        yield item
                        if item["type"] != "unknown" and is_end(item):
                            return
            finally:
                await aframes.aclose()
        except FutureAGIError as error:
            state.failed(error)
        delay = state.after()
        if delay:
            if core.shared.sleep is not None:
                result = core.shared.sleep(delay)
                if asyncio.iscoroutine(result):
                    await result
            else:
                await asyncio.sleep(delay)
