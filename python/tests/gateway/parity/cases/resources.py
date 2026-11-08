"""Every resource method: method, path, query, body or multipart, headers, result."""

from __future__ import annotations

from typing import Any

from .._fixtures import MSG, chunks, ok, sse
from .._runner import Case, exercises
from .resources_client import cases as client_cases

BOTH = ("sync", "async")
GW = {
    "session_id": "sess-r",
    "trace_id": "trace-r",
    "cache_ttl": 60,
    "properties": {"team": "a"},
    "request_id": "rid-r",
}


def _call(path: str, *args: Any, **kwargs: Any):
    @exercises(path)
    def fn(ctx):
        return ctx.call(ctx.client(max_retries=0), path, *args, **kwargs)

    return fn


def _stream(path: str, **kwargs: Any):
    @exercises(path)
    def fn(ctx):
        stream = ctx.call(ctx.client(max_retries=0), path, **kwargs)
        out = ctx.drain(stream)
        out["agentcc"] = getattr(stream, "agentcc", None)
        return out

    return fn


def _manager(**kwargs: Any):
    @exercises("chat.completions.stream")
    def fn(ctx):
        client = ctx.client(max_retries=0)
        manager = ctx.call(client, "chat.completions.stream", **kwargs)
        entered = ctx.enter(manager)
        events = ctx.drain(entered)
        final = ctx.attempt(lambda: ctx.run(entered.get_final_completion()))
        text = ctx.attempt(lambda: ctx.run(entered.get_final_text()))
        ctx.exit(manager)
        return {"events": events, "final": final, "final_text": text}

    return fn


@exercises("batches.wait")
def _batch_wait(ctx):
    client = ctx.client(max_retries=0)
    return ctx.call(
        client, "batches.wait", "batch-parity", poll_interval=1.5, timeout=30
    )


@exercises("batches.create_and_wait")
def _batch_create_and_wait(ctx):
    client = ctx.client(max_retries=0)
    return ctx.call(
        client,
        "batches.create_and_wait",
        [{"model": "gpt-4o-mini", "messages": MSG}],
        max_concurrency=2,
        poll_interval=1.5,
        timeout=30,
    )


def _resource_cases() -> list[Case]:
    chat = {"model": "gpt-4o-mini", "messages": MSG}
    audio = {"model": "whisper-1"}
    spec: list[tuple[str, Any, list[dict[str, Any]]]] = [
        (
            "chat.create",
            _call("chat.completions.create", **chat),
            [ok("chat_completion")],
        ),
        (
            "chat.create.gateway_params",
            _call("chat.completions.create", **chat, **GW),
            [ok("chat_completion")],
        ),
        (
            "chat.create.tools",
            _call(
                "chat.completions.create",
                **chat,
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "parameters": {"type": "object"},
                        },
                    }
                ],
                tool_choice="auto",
            ),
            [ok("chat_completion_tools")],
        ),
        (
            "chat.create.stream",
            _stream("chat.completions.create", **chat, stream=True),
            [sse(chunks("content"))],
        ),
        (
            "chat.create.stream_tools",
            _stream("chat.completions.create", **chat, stream=True),
            [sse(chunks("tool_calls"))],
        ),
        ("chat.stream", _manager(**chat), [sse(chunks("content"))]),
        ("chat.stream.tools", _manager(**chat), [sse(chunks("tool_calls"))]),
        (
            "completions.create",
            _call(
                "completions.create",
                model="gpt-3.5-turbo-instruct",
                prompt="Hello",
                max_tokens=5,
            ),
            [ok("completion")],
        ),
        (
            "completions.create.gateway_params",
            _call(
                "completions.create",
                model="gpt-3.5-turbo-instruct",
                prompt=["a", "b"],
                **GW,
            ),
            [ok("completion")],
        ),
        (
            "completions.create.stream",
            _stream(
                "completions.create",
                model="gpt-3.5-turbo-instruct",
                prompt="Hello",
                stream=True,
            ),
            [sse(chunks("completion"))],
        ),
        (
            "embeddings.create",
            _call(
                "embeddings.create",
                model="text-embedding-3-small",
                input="hi",
                dimensions=3,
                encoding_format="float",
            ),
            [ok("embedding")],
        ),
        (
            "embeddings.create.list",
            _call(
                "embeddings.create",
                model="text-embedding-3-small",
                input=["a", "b"],
                extra_body={"x": 1},
            ),
            [ok("embedding")],
        ),
        (
            "embeddings.create.usage_completion_tokens",
            _call("embeddings.create", model="text-embedding-3-small", input="hi"),
            [ok("embedding_completion_tokens")],
        ),
        (
            "images.generate",
            _call(
                "images.generate",
                prompt="a cat",
                model="dall-e-3",
                size="1024x1024",
                n=1,
            ),
            [ok("image")],
        ),
        (
            "audio.transcriptions.bytes",
            _call("audio.transcriptions.create", file=b"RIFF-parity", **audio),
            [ok("transcription")],
        ),
        (
            "audio.transcriptions.tuple",
            _call(
                "audio.transcriptions.create",
                file=("a.wav", b"RIFF-parity", "audio/wav"),
                **audio,
            ),
            [ok("transcription")],
        ),
        (
            "audio.transcriptions.name",
            _call(
                "audio.transcriptions.create",
                file="a.wav",
                language="en",
                **audio,
                **GW,
            ),
            [ok("transcription")],
        ),
        (
            "audio.translations.name",
            _call("audio.translations.create", file="a.wav", **audio),
            [ok("translation")],
        ),
        (
            "audio.speech",
            _call("audio.speech.create", model="tts-1", input="hello", voice="alloy"),
            [ok("speech_bytes")],
        ),
        (
            "audio.speech.options",
            _call(
                "audio.speech.create",
                model="tts-1",
                input="hello",
                voice="alloy",
                response_format="wav",
                speed=1.25,
                session_id="s",
            ),
            [ok("speech_bytes")],
        ),
        ("models.list", _call("models.list"), [ok("models_list")]),
        ("models.retrieve", _call("models.retrieve", "gpt-4o-mini"), [ok("model")]),
        (
            "models.retrieve.slash",
            _call("models.retrieve", "openai/gpt-4o mini"),
            [ok("model")],
        ),
        (
            "files.create",
            _call(
                "files.create",
                file=("data.jsonl", b'{"a":1}\n', "application/jsonl"),
                purpose="batch",
                session_id="s-f",
            ),
            [ok("file_object")],
        ),
        ("files.list", _call("files.list"), [ok("file_list")]),
        ("files.list.purpose", _call("files.list", purpose="batch"), [ok("file_list")]),
        ("files.retrieve", _call("files.retrieve", "file-parity"), [ok("file_object")]),
        ("files.content", _call("files.content", "file-parity"), [ok("file_content")]),
        ("files.delete", _call("files.delete", "file-parity"), [ok("file_deleted")]),
        (
            "rerank.create",
            _call(
                "rerank.create",
                model="rerank-v1",
                query="q",
                documents=["alpha", "beta"],
                top_n=2,
                return_documents=True,
            ),
            [ok("rerank")],
        ),
        (
            "rerank.create.document_strings",
            _call(
                "rerank.create",
                model="rerank-v1",
                query="q",
                documents=["alpha", "beta"],
            ),
            [ok("rerank_document_strings")],
        ),
        (
            "responses.create",
            _call(
                "responses.create",
                model="gpt-4o-mini",
                input="hi",
                instructions="be brief",
                max_output_tokens=5,
            ),
            [ok("response_object")],
        ),
        (
            "responses.create.gateway_params",
            _call(
                "responses.create",
                model="gpt-4o-mini",
                input=[{"role": "user", "content": "hi"}],
                store=False,
                **GW,
            ),
            [ok("response_object")],
        ),
        (
            "responses.retrieve",
            _call("responses.retrieve", "resp_parity"),
            [ok("response_object")],
        ),
        (
            "responses.delete",
            _call("responses.delete", "resp_parity"),
            [{"status": 200, "json": {"id": "resp_parity", "deleted": True}}],
        ),
        (
            "batches.create",
            _call(
                "batches.create",
                [{"model": "gpt-4o-mini", "messages": MSG}],
                max_concurrency=2,
            ),
            [ok("batch")],
        ),
        ("batches.retrieve", _call("batches.retrieve", "batch-parity"), [ok("batch")]),
        ("batches.cancel", _call("batches.cancel", "batch-parity"), [ok("batch")]),
        (
            "batches.wait",
            _batch_wait,
            [ok("batch_running"), ok("batch_running"), ok("batch")],
        ),
        (
            "batches.create_and_wait",
            _batch_create_and_wait,
            [ok("batch_running"), ok("batch_running"), ok("batch")],
        ),
        (
            "moderations.create",
            _call("moderations.create", input="hello", model="omni-moderation-latest"),
            [ok("moderation")],
        ),
    ]
    return [
        Case(f"resource.{name}", "resources", fn, BOTH, replies=replies)
        for name, fn, replies in spec
    ]


def cases() -> list[Case]:
    return _resource_cases() + client_cases()
