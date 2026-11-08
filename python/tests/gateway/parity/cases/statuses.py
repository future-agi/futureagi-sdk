"""Statuses 246, 400 ... 504, each with every error-envelope variant."""

from __future__ import annotations

from .._fixtures import MSG, body, error_reply, statuses
from .._runner import Case

BOTH = ("sync", "async")
CHAT = {"model": "gpt-4o-mini", "messages": MSG}
ENVELOPES = (
    "error_object",
    "error_object_minimal",
    "top_level_message",
    "non_json",
    "empty",
)
GUARD = {
    "x-agentcc-request-id": "req-err-1",
    "x-agentcc-guardrail-name": "pii",
    "x-agentcc-guardrail-action": "block",
    "x-agentcc-guardrail-confidence": "0.97",
    "x-agentcc-guardrail-message": "PII found",
    "x-ratelimit-limit-requests": "10",
    "x-ratelimit-remaining-requests": "0",
    "x-ratelimit-reset-requests": "30",
}


def _create(ctx):
    return ctx.call(ctx.client(max_retries=0), "chat.completions.create", **CHAT)


def _stream(ctx):
    stream = ctx.call(
        ctx.client(max_retries=0), "chat.completions.create", **CHAT, stream=True
    )
    return ctx.drain(stream)


def _embed(ctx):
    return ctx.call(
        ctx.client(max_retries=0), "embeddings.create", model="e", input="x"
    )


def _speech(ctx):
    return ctx.call(
        ctx.client(max_retries=0),
        "audio.speech.create",
        model="tts-1",
        input="x",
        voice="alloy",
    )


def _warning_completion(ctx):
    try:
        _create(ctx)
    except Exception as exc:
        completion = getattr(exc, "completion", None)
        return {"raised": type(exc).__qualname__, "completion": completion}
    return {"raised": None}


def cases() -> list[Case]:
    out = []
    for status in statuses():
        for env in ENVELOPES:
            out.append(
                Case(
                    f"status.{status}.{env}",
                    "statuses",
                    _create,
                    BOTH,
                    replies=[error_reply(status, env)],
                )
            )
        out.append(
            Case(
                f"status.{status}.headers",
                "statuses",
                _create,
                BOTH,
                replies=[error_reply(status, "error_object", GUARD)],
            )
        )
    for status in (400, 401, 429, 446, 500, 503):
        out.append(
            Case(
                f"status.stream.{status}",
                "statuses",
                _stream,
                BOTH,
                replies=[error_reply(status, "error_object", GUARD)],
            )
        )
    out.append(
        Case(
            "status.stream.246",
            "statuses",
            _stream,
            BOTH,
            replies=[
                {"status": 246, "headers": GUARD, "json": body("chat_completion")}
            ],
        )
    )
    out.append(
        Case(
            "status.246.completion_body",
            "statuses",
            _warning_completion,
            BOTH,
            replies=[
                {"status": 246, "headers": GUARD, "json": body("chat_completion")}
            ],
        )
    )
    out.append(
        Case(
            "status.embeddings.429",
            "statuses",
            _embed,
            BOTH,
            replies=[error_reply(429, "error_object", GUARD)],
        )
    )
    out.append(
        Case(
            "status.speech.500",
            "statuses",
            _speech,
            BOTH,
            replies=[error_reply(500, "non_json")],
        )
    )
    out.append(
        Case(
            "status.418_unmapped",
            "statuses",
            _create,
            BOTH,
            replies=[error_reply(418, "error_object")],
        )
    )
    out.append(
        Case(
            "status.599_unmapped",
            "statuses",
            _create,
            BOTH,
            replies=[error_reply(599, "empty")],
        )
    )
    out.append(
        Case(
            "status.200_non_json",
            "statuses",
            _create,
            BOTH,
            replies=[{"status": 200, "text": "not json"}],
        )
    )
    out.append(
        Case(
            "status.200_wrong_shape",
            "statuses",
            _create,
            BOTH,
            replies=[{"status": 200, "json": {"unexpected": True}}],
        )
    )
    out.append(
        Case(
            "status.201_ok",
            "statuses",
            _create,
            BOTH,
            replies=[{"status": 201, "json": body("chat_completion")}],
        )
    )
    return out
