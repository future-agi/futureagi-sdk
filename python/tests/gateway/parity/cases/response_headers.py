"""Every x-agentcc-* and x-ratelimit-* response header, alone, together, malformed."""

from __future__ import annotations

from .._fixtures import MSG, chunks, ok, response_headers, sse
from .._runner import Case, exercises

BOTH = ("sync", "async")
CHAT = {"model": "gpt-4o-mini", "messages": MSG}


def _meta(ctx):
    result = ctx.call(ctx.client(max_retries=0), "chat.completions.create", **CHAT)
    return {"agentcc": result.agentcc, "type": type(result.agentcc).__qualname__}


def _stream_meta(ctx):
    stream = ctx.call(
        ctx.client(max_retries=0), "chat.completions.create", **CHAT, stream=True
    )
    ctx.drain(stream)
    return stream.agentcc


def _embedding_meta(ctx):
    result = ctx.call(
        ctx.client(max_retries=0),
        "embeddings.create",
        model="text-embedding-3-small",
        input="x",
    )
    return getattr(result, "agentcc", None)


@exercises("reset_cost")
def _cost_accumulates(ctx):
    client = ctx.client(max_retries=0)
    for _ in range(2):
        ctx.call(client, "chat.completions.create", **CHAT)
    before = client.current_cost
    client.reset_cost()
    return {"current_cost": before, "after_reset": client.current_cost}


def cases() -> list[Case]:
    all_headers = response_headers("all")
    out = [
        Case(
            "response_header.none",
            "response_headers",
            _meta,
            BOTH,
            replies=[ok("chat_completion")],
        ),
        Case(
            "response_header.all",
            "response_headers",
            _meta,
            BOTH,
            replies=[ok("chat_completion", headers=all_headers)],
        ),
        Case(
            "response_header.malformed",
            "response_headers",
            _meta,
            BOTH,
            replies=[ok("chat_completion", headers=response_headers("malformed"))],
        ),
        Case(
            "response_header.stream_all",
            "response_headers",
            _stream_meta,
            BOTH,
            replies=[sse(chunks("content"), headers=all_headers)],
        ),
        Case(
            "response_header.embeddings_all",
            "response_headers",
            _embedding_meta,
            BOTH,
            replies=[ok("embedding", headers=all_headers)],
        ),
        Case(
            "response_header.current_cost",
            "response_headers",
            _cost_accumulates,
            BOTH,
            replies=[ok("chat_completion", headers={"x-agentcc-cost": "0.25"})] * 2,
        ),
    ]
    for name, value in all_headers.items():
        out.append(
            Case(
                f"response_header.alone.{name}",
                "response_headers",
                _meta,
                ("sync",),
                replies=[ok("chat_completion", headers={name: value})],
            )
        )
    return out
