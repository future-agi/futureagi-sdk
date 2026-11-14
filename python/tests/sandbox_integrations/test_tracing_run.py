"""``run_traced`` / ``arun_traced`` over the frozen-OpenAPI mock server (sync and async): a credential
name in ``env`` is refused before any request, exactly one exec is sent, its ``env`` is the caller's
plus the exec span's TRACEPARENT / TRACESTATE (the caller wins), the exit record lands on the span as
attributes, the command line only on request, a non-zero exit is not an error status, and a broken
stream sets ERROR and raises again. Spans go to an in-memory exporter on a private provider (never the
global one); those tests skip where OpenTelemetry's SDK is not installed. Fake credentials only."""

from __future__ import annotations

import json
import re
import sys
from types import SimpleNamespace

import pytest

from fi.sandbox import CommandIncompleteError, ConfigurationError
from fi.sandbox_integrations.tracing import REFUSED_ENV_NAMES, arun_traced, run_traced
from tests.platform._sandbox_mock import (
    EXEC,
    EXIT0,
    MODES,
    SBX,
    Chunks,
    MockServer,
    api,
    run,
    sse,
    stream_response,
)

TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
STARTED = ("started", {"execId": EXEC, "sandboxId": SBX})


def answer(server: MockServer, **exit_fields) -> None:
    body = sse(STARTED, ("stdout", {"data": "out\n"}), ("exit", {**EXIT0, **exit_fields}))
    server.on("sandboxes.commands.run", lambda r: stream_response(body))


def traced(server: MockServer, mode: str, command: str, **kw):
    """Connect a handle (sync or async) over the mock, forget the connect's read, then run the
    command through ``run_traced`` / ``arun_traced``, all in one event loop for the async handle."""
    if mode == "sync":
        sbx = api(server, "sync").connect(SBX)
        server.seen.clear()
        return run_traced(sbx, command, **kw)

    async def go():
        sbx = await api(server, "async").connect(SBX)
        server.seen.clear()
        return await arun_traced(sbx, command, **kw)

    return run(go())


def exec_bodies(server: MockServer) -> list:
    return [seen.json() for seen in server.seen if seen.name == "sandboxes.commands.run"]


@pytest.fixture
def otel():
    """A private provider with an in-memory exporter; ``tracer`` goes to ``run_traced``."""
    pytest.importorskip("opentelemetry.sdk")
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from opentelemetry.trace import SpanKind, StatusCode

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    found = SimpleNamespace(
        trace=trace, exporter=exporter, tracer=provider.get_tracer("tests.sandbox_integrations"),
        SpanKind=SpanKind, StatusCode=StatusCode,
    )
    found.execs = lambda: [s for s in exporter.get_finished_spans() if s.name == "sandbox.exec"]
    yield found
    provider.shutdown()


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("name", sorted(REFUSED_ENV_NAMES))
def test_refused_env_name_raises_before_any_request(mode, name):
    server = MockServer()
    with pytest.raises(ConfigurationError) as caught:
        traced(server, mode, "env", env={"A": "1", name: "fake-value-0000"})
    assert caught.value.code == "secret_in_env"
    assert name in str(caught.value) and "fake-value-0000" not in str(caught.value)
    assert server.seen == []


@pytest.mark.parametrize("mode", MODES)
def test_merged_env_sent_in_exec_body_and_caller_wins(mode, otel):
    server = MockServer()
    with otel.tracer.start_as_current_span("caller") as caller:
        traced(server, mode, "echo", env={"A": "1", "TRACESTATE": "mine=1"}, tracer=otel.tracer)
    (body,) = exec_bodies(server)
    env = body["env"]
    assert set(env) == {"A", "TRACEPARENT", "TRACESTATE"}  # no OTEL_RESOURCE_ATTRIBUTES, BAGGAGE or FI_*
    assert env["A"] == "1" and env["TRACESTATE"] == "mine=1"
    (span,) = otel.execs()
    trace_id, span_id, _ = TRACEPARENT.match(env["TRACEPARENT"]).groups()
    # the TRACEPARENT names the exec span, a child of the caller's span
    assert span_id == format(span.context.span_id, "016x")
    assert trace_id == format(caller.get_span_context().trace_id, "032x")
    assert span.parent.span_id == caller.get_span_context().span_id
    assert span.kind == otel.SpanKind.CLIENT
    assert "sandbox.id" not in json.dumps(env)

    # the caller's own TRACEPARENT wins too
    own = "00-" + "1" * 32 + "-" + "2" * 16 + "-01"
    traced(server, mode, "echo", env={"TRACEPARENT": own}, tracer=otel.tracer)
    assert exec_bodies(server)[-1]["env"] == {"TRACEPARENT": own}

    # resource attributes only on request, with the sandbox id added
    traced(server, mode, "echo", tracer=otel.tracer, resource_attributes={"team": "a"}, baggage=False)
    env = exec_bodies(server)[-1]["env"]
    assert set(env) == {"TRACEPARENT", "OTEL_RESOURCE_ATTRIBUTES"}
    assert env["OTEL_RESOURCE_ATTRIBUTES"] == f"sandbox.id={SBX},team=a"


@pytest.mark.parametrize("mode", MODES)
def test_span_attributes_set_from_exit_record(mode, otel):
    server = MockServer()
    answer(server, exitCode=3, truncated=True, durationMs=42)
    result = traced(server, mode, "make", tracer=otel.tracer)
    assert result.exit_code == 3 and result.stdout == "out\n"
    (span,) = otel.execs()
    assert dict(span.attributes) == {
        "sandbox.id": SBX,
        "sandbox.exec.id": EXEC,
        "sandbox.exec.exit_code": 3,
        "sandbox.exec.timed_out": False,
        "sandbox.exec.cancelled": False,
        "sandbox.exec.truncated": True,
        "sandbox.exec.duration_ms": 42,
        "sandbox.exec.shell_exit_code": 3,
    }

    answer(server, exitCode=None, signal="SIGTERM")
    traced(server, mode, "sleep 99", tracer=otel.tracer)
    attributes = otel.execs()[-1].attributes
    assert attributes["sandbox.exec.signal"] == "SIGTERM"
    assert "sandbox.exec.exit_code" not in attributes  # None is left off
    assert attributes["sandbox.exec.shell_exit_code"] == 143  # 128 + 15, the one exit-code rule

    answer(server, exitCode=None, signal="SIGKILL", timedOut=True)
    traced(server, mode, "sleep 99", tracer=otel.tracer)
    attributes = otel.execs()[-1].attributes
    assert attributes["sandbox.exec.timed_out"] is True and attributes["sandbox.exec.shell_exit_code"] == 124


@pytest.mark.parametrize("mode", MODES)
def test_command_not_recorded_by_default_and_recorded_on_request(mode, otel):
    server = MockServer()
    command = "deploy --token fake-token-in-command-0000"
    env = {"PLAIN": "fake-env-value-0000"}
    traced(server, mode, command, env=env, tracer=otel.tracer)
    traced(server, mode, command, env=env, tracer=otel.tracer, record_command=True)
    default, recorded = otel.execs()
    assert "sandbox.exec.command" not in default.attributes
    assert "fake-token-in-command-0000" not in json.dumps(dict(default.attributes))
    assert recorded.attributes["sandbox.exec.command"] == command
    for span in (default, recorded):  # an env value never reaches a span
        assert "fake-env-value-0000" not in json.dumps(dict(span.attributes))
        assert "fake-env-value-0000" not in json.dumps([dict(e.attributes or {}) for e in span.events])


@pytest.mark.parametrize("mode", MODES)
def test_nonzero_exit_is_attribute_not_error_status(mode, otel):
    server = MockServer()
    answer(server, exitCode=2)
    result = traced(server, mode, "false", tracer=otel.tracer)
    assert result.exit_code == 2
    (span,) = otel.execs()
    assert span.attributes["sandbox.exec.exit_code"] == 2
    assert span.status.status_code == otel.StatusCode.UNSET

    answer(server, exitCode=None, error="spawn /bin/nope ENOENT")
    traced(server, mode, "/bin/nope", tracer=otel.tracer)
    span = otel.execs()[-1]
    assert span.status.status_code == otel.StatusCode.UNSET
    assert span.attributes["sandbox.exec.shell_exit_code"] == 1
    assert "spawn /bin/nope ENOENT" not in json.dumps(dict(span.attributes))


@pytest.mark.parametrize("mode", MODES)
def test_incomplete_stream_sets_error_status_and_reraises(mode, otel):
    server = MockServer()
    body = sse(STARTED, ("stdout", {"data": "partial"}))
    server.on("sandboxes.commands.run", lambda r: stream_response(Chunks([body, b"event: exit\ndata: {"])))
    with pytest.raises(CommandIncompleteError) as caught:
        traced(server, mode, "long", tracer=otel.tracer)
    assert caught.value.exec_id == EXEC
    assert len(exec_bodies(server)) == 1  # never run again
    (span,) = otel.execs()
    assert span.status.status_code == otel.StatusCode.ERROR
    assert span.status.description == "CommandIncompleteError"
    assert span.attributes["error.type"] == "CommandIncompleteError"
    assert span.attributes["sandbox.exec.id"] == EXEC
    assert not span.events  # the error text is not recorded
    assert otel.trace.get_current_span() is otel.trace.INVALID_SPAN  # the span is no longer current


@pytest.mark.parametrize("mode", MODES)
def test_one_exec_request_sync_and_async(mode, otel):
    server = MockServer()
    result = traced(server, mode, "echo hi", cwd="src", timeout_seconds=9, tracer=otel.tracer)
    assert result.exit_code == 0 and result.exec_id == EXEC
    assert [seen.name for seen in server.seen] == ["sandboxes.commands.run"]
    (body,) = exec_bodies(server)
    assert body["command"] == "echo hi" and body["cwd"] == "src" and body["timeoutSeconds"] == 9
    assert set(body["env"]) == {"TRACEPARENT"}
    assert len(otel.execs()) == 1


@pytest.mark.parametrize("mode", MODES)
def test_without_opentelemetry_runs_once_with_the_callers_env(mode, monkeypatch):
    monkeypatch.setitem(sys.modules, "opentelemetry", None)
    server = MockServer()
    result = traced(server, mode, "echo", env={"A": "1"})
    assert result.exit_code == 0
    assert [seen.name for seen in server.seen] == ["sandboxes.commands.run"]
    assert exec_bodies(server) == [{"command": "echo", "env": {"A": "1"}}]
    traced(server, mode, "echo")
    assert exec_bodies(server)[-1] == {"command": "echo"}  # no env at all when there is nothing to send


@pytest.mark.parametrize("mode", MODES)
def test_without_opentelemetry_a_failed_command_chains_no_import_error(mode, monkeypatch):
    monkeypatch.setitem(sys.modules, "opentelemetry", None)
    server = MockServer()
    body = sse(STARTED, ("stdout", {"data": "partial"}))
    server.on("sandboxes.commands.run", lambda r: stream_response(Chunks([body, b"event: exit\ndata: {"])))
    with pytest.raises(CommandIncompleteError) as caught:
        traced(server, mode, "long")
    assert len(exec_bodies(server)) == 1
    chain, error = [], caught.value
    while error is not None and len(chain) < 20:
        chain.append(error)
        error = error.__cause__ or error.__context__
    # the missing OpenTelemetry import is not shown as the cause of the command's failure
    assert not any(isinstance(link, ImportError) for link in chain)


@pytest.mark.skip(
    reason="Cloud walk, waits on how Future AGI keys reach code inside a sandbox: a traced caller on a "
    "self-host stack with network on runs a script that calls context_from_env(), emits one span and flushes; "
    "the stored trace shows sandbox.exec with the in-sandbox span as its child"
)
def test_cloud_walk_in_sandbox_span_is_a_child_of_sandbox_exec():
    raise AssertionError("cloud walk only")
