"""The testing helpers: MockAgentCC, mock_completion, mock_error, fixtures,
assertions, RequestRecorder, RecordingAgentCC, create_mock_client, mock_response."""

from __future__ import annotations

import tempfile
from pathlib import Path

from .._fixtures import MSG, ok
from .._runner import Case

BOTH = ("sync", "async")


def _mock_client(ctx):
    t = ctx.mod("testing")
    mock = t.MockAgentCC()
    mock.chat.completions.respond_with(
        t.mock_completion(content="first", cost=0.5, cache_status="hit")
    )
    mock.chat.completions.respond_with(t.mock_error(429, "slow down", code="rate"))
    first = mock.chat.completions.create(model="gpt-4o", messages=MSG, temperature=0)
    second = ctx.attempt(
        lambda: mock.chat.completions.create(model="gpt-4o", messages=MSG)
    )
    third = ctx.attempt(
        lambda: mock.chat.completions.create(model="gpt-4o", messages=MSG)
    )
    with t.MockAgentCC() as scoped:
        scoped_result = ctx.attempt(
            lambda: scoped.chat.completions.create(model="m", messages=MSG)
        )
    return {
        "first": first,
        "second": second,
        "third": third,
        "calls": mock.chat.completions.calls,
        "scoped": scoped_result,
    }


def _mock_values(ctx):
    t = ctx.mod("testing")
    return {
        "mock_completion.default": t.mock_completion(),
        "mock_completion.kwargs": t.mock_completion(
            content="x",
            model="m",
            provider="p",
            cost=0.1,
            cache_status="miss",
            id="custom",
        ),
        "mock_error.default": t.mock_error(),
        "mock_error.each": [
            t.mock_error(s, f"m{s}")
            for s in (400, 401, 403, 404, 422, 429, 446, 500, 502, 503, 504, 418)
        ],
        "make_usage": [t.make_usage(), t.make_usage(1, 2), t.make_usage(1, 2, 9)],
        "make_agentcc_metadata": t.make_agentcc_metadata(cost=0.2, cache_status="hit"),
        "make_message": t.make_message(),
        "make_tool_call": t.make_tool_call(),
        "make_completion": t.make_completion(
            tool_calls=[t.make_tool_call()], agentcc=t.make_agentcc_metadata()
        ),
    }


def _assertions(ctx):
    t = ctx.mod("testing")
    good = t.make_completion(
        content="Hello!",
        usage=t.make_usage(),
        agentcc=t.make_agentcc_metadata(cost=0.1, cache_status="hit"),
    )
    bad = t.make_completion(content=None, usage=None)
    blocked = t.mock_error(446, "blocked")
    checks = {
        "has_content.ok": lambda: t.assert_completion_has_content(good, "Hello"),
        "has_content.fail": lambda: t.assert_completion_has_content(good, "nope"),
        "valid.ok": lambda: t.assert_completion_valid(good),
        "valid.fail": lambda: t.assert_completion_valid(object()),
        "stream_valid.empty": lambda: t.assert_stream_valid([]),
        "metadata.ok": lambda: t.assert_agentcc_metadata(
            good, provider="openai", cost=0.1, cache_status="hit"
        ),
        "metadata.fail": lambda: t.assert_agentcc_metadata(good, provider="anthropic"),
        "usage.ok": lambda: t.assert_usage_valid(good),
        "usage.fail": lambda: t.assert_usage_valid(bad),
        "cost.ok": lambda: t.assert_cost_tracked(good),
        "cost.fail": lambda: t.assert_cost_tracked(bad),
        "guardrail.ok": lambda: t.assert_guardrail_blocked(blocked),
        "guardrail.fail": lambda: t.assert_guardrail_blocked(ValueError("x")),
    }
    return {name: ctx.attempt(fn) for name, fn in checks.items()}


def _create_mock_client(ctx):
    t = ctx.mod("testing")
    client = t.create_mock_client()
    custom = t.create_mock_client(
        responses={"gpt-4o": "custom"},
        api_key="parity-gateway-key",
        base_url="https://gateway.example.test",
    )
    return {
        "type": type(client).__qualname__,
        "default": ctx.attempt(
            lambda: client.chat.completions.create(model="gpt-4o", messages=MSG)
        ),
        "custom": ctx.attempt(
            lambda: custom.chat.completions.create(model="gpt-4o", messages=MSG)
        ),
    }


def _recorders(ctx):
    t = ctx.mod("testing")
    folder = Path(tempfile.mkdtemp(prefix="parity-rec-"))
    rec_path = folder / "requests.json"
    with t.RequestRecorder(str(rec_path)) as recorder:
        client = ctx.client(max_retries=0, callbacks=[recorder])
        ctx.call(client, "chat.completions.create", model="gpt-4o-mini", messages=MSG)
        recordings = recorder.recordings
    recording = t.RecordingAgentCC(ctx.client(max_retries=0))
    rc = ctx.attempt(
        lambda: ctx.run(
            recording.chat.completions.create(model="gpt-4o-mini", messages=MSG)
        )
    )
    saved = folder / "interactions.json"
    ctx.attempt(lambda: recording.save(saved))
    loaded = ctx.attempt(lambda: t.RecordingAgentCC.load(saved))
    return {
        "recordings": recordings,
        "file": rec_path.read_text() if rec_path.exists() else None,
        "recording_result": rc,
        "interactions": ctx.attempt(lambda: recording.interactions),
        "loaded": loaded,
    }


def _mock_response(stream: bool):
    def fn(ctx):
        client = ctx.client(max_retries=0)
        result = ctx.call(
            client,
            "chat.completions.create",
            model="gpt-4o",
            messages=MSG,
            mock_response="mocked words here",
            stream=stream,
        )
        if stream:
            entered = ctx.enter(result)
            return {
                "events": ctx.drain(entered),
                "final": ctx.attempt(lambda: ctx.run(entered.get_final_completion())),
            }
        return result

    return fn


def cases() -> list[Case]:
    return [
        Case("mock.mock_client", "mocks", _mock_client),
        Case("mock.values", "mocks", _mock_values),
        Case("mock.assertions", "mocks", _assertions),
        Case(
            "mock.create_mock_client",
            "mocks",
            _create_mock_client,
            replies=[ok("chat_completion"), ok("chat_completion")],
        ),
        Case(
            "mock.recorders",
            "mocks",
            _recorders,
            BOTH,
            replies=[ok("chat_completion"), ok("chat_completion")],
        ),
        Case("mock.mock_response", "mocks", _mock_response(False), BOTH),
        Case("mock.mock_response.stream", "mocks", _mock_response(True), BOTH),
    ]
