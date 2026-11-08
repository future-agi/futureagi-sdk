"""Streams: the 6 gateway error-frame cases, the 4 catalog additions, malformed
SSE, StreamManager events and final usage, each through every consumer."""

from __future__ import annotations

from typing import Any

from .._fixtures import MSG, load, stream_error_cases, stream_extra_cases
from .._runner import Case

BOTH = ("sync", "async")
CHAT = {"model": "gpt-4o-mini", "messages": MSG}


def _malformed() -> dict[str, list[str]]:
    return load("sse-malformed.json")["cases"]


def _iter(ctx, path: str = "chat.completions.create", **kw: Any):
    stream = ctx.call(ctx.client(max_retries=0), path, **kw, stream=True)
    out = ctx.drain(stream)
    out["agentcc"] = getattr(stream, "agentcc", None)
    return out


def _manager(ctx, consume: str):
    manager = ctx.call(ctx.client(max_retries=0), "chat.completions.stream", **CHAT)
    entered = ctx.enter(manager)
    if consume == "events":
        out = ctx.drain(entered)
    elif consume == "text":
        out = ctx.drain(entered.text_stream)
    elif consume == "break_on_done":
        out = _break_on_done(ctx, entered)
    else:
        out = ctx.attempt(lambda: ctx.run(entered.get_final_completion()))
    snapshot = ctx.attempt(lambda: entered.current_completion_snapshot)
    ctx.exit(manager)
    return {"consumed": out, "snapshot": snapshot}


def _break_on_done(ctx, entered: Any) -> dict[str, Any]:
    """A consumer that stops at the first ``done`` event (the D-16 hazard)."""
    seen: list[Any] = []

    async def go_async() -> None:
        async for event in entered:
            seen.append(event)
            if getattr(event, "type", None) == "done":
                break

    def go_sync() -> None:
        for event in entered:
            seen.append(event)
            if getattr(event, "type", None) == "done":
                break

    result = ctx.attempt(
        lambda: ctx.run(go_async()) if hasattr(entered, "__aiter__") else go_sync()
    )
    return {"types": [getattr(e, "type", None) for e in seen], "result": result}


CONSUMERS = ("iter", "events", "text", "final", "break_on_done")


def _consumer(name: str, path: str = "/v1/chat/completions"):
    def fn(ctx):
        if path == "/v1/responses":
            return _iter(ctx, "responses.create", model="gpt-4o-mini", input="hi")
        if name == "iter":
            return _iter(ctx, **CHAT)
        return _manager(ctx, name)

    return fn


def _frames_reply(frames: list[str]) -> dict[str, Any]:
    return {
        "status": 200,
        "headers": {"content-type": "text/event-stream"},
        "sse": frames,
    }


def cases() -> list[Case]:
    out = []
    for fixture in stream_error_cases():
        for consumer in CONSUMERS:
            out.append(
                Case(
                    f"stream.fixture.{fixture['name']}.{consumer}",
                    "stream_fixture",
                    _consumer(consumer),
                    BOTH,
                    replies=[_frames_reply(fixture["frames"])],
                )
            )
    for extra in stream_extra_cases():
        consumers = ("iter",) if extra["path"] == "/v1/responses" else CONSUMERS
        for consumer in consumers:
            out.append(
                Case(
                    f"stream.extra.{extra['name']}.{consumer}",
                    "stream_extra",
                    _consumer(consumer, extra["path"]),
                    BOTH,
                    replies=[extra["reply"]],
                )
            )
    for name, raw in _malformed().items():
        reply = {
            "status": 200,
            "headers": {"content-type": "text/event-stream"},
            "raw": raw,
        }
        out.append(
            Case(
                f"stream.malformed.{name}.iter",
                "sse",
                _consumer("iter"),
                BOTH,
                replies=[reply],
            )
        )
        out.append(
            Case(
                f"stream.malformed.{name}.final",
                "sse",
                _consumer("final"),
                BOTH,
                replies=[reply],
            )
        )
    out.append(
        Case(
            "stream.text_plain_200",
            "sse",
            _consumer("iter"),
            BOTH,
            replies=[
                {
                    "status": 200,
                    "headers": {"content-type": "text/plain"},
                    "text": "hello",
                }
            ],
        )
    )
    out.append(
        Case(
            "stream.responses.normal",
            "sse",
            _consumer("iter", "/v1/responses"),
            BOTH,
            replies=[
                {
                    "status": 200,
                    "headers": {"content-type": "text/event-stream"},
                    "raw": [
                        'event: response.created\ndata: {"type":"response.created","sequence_number":0}\n\n',
                        'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":1,"delta":"Hi"}\n\n',
                        'event: response.completed\ndata: {"type":"response.completed","sequence_number":2,"response":{"id":"resp_1","status":"completed"}}\n\n',
                    ],
                }
            ],
        )
    )
    return out
