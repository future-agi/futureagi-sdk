"""commands.run / commands.stream over SSE (sync and async): framing in any chunking, typed
frames, the whole exit record on CommandResult (v2 item 4: a non-zero exit, a timeout, a signal, a
cancel, truncation and a spawn failure are results), the missing exit frame and the error frame as
the only raises, closing cancels, and never a retry."""

from __future__ import annotations

import httpx
import pytest
from fi.sandbox import (
    AsyncSandbox,
    CommandFailedError,
    CommandIncompleteError,
    ExitFrame,
    Sandbox,
    StartedFrame,
    StdoutFrame,
    UnknownFrame,
)
from fi.sandbox import ConnectionError as SandboxConnectionError

from ._sandbox_mock import (
    EXEC,
    EXIT0,
    MODES,
    SBX,
    Chunks,
    MockServer,
    api,
    close,
    collect,
    error,
    resolve,
    run,
    sse,
    stream_response,
)

STARTED = ("started", {"execId": EXEC, "sandboxId": SBX})
HELLO = sse(STARTED, ("stdout", {"data": "héllo\n"}), ("stderr", {"data": "warn\n"}),
            ("exit", {**EXIT0, "exitCode": 3, "stdoutBytes": 7, "stderrBytes": 5}))


def handle(server: MockServer, mode: str):
    cls = AsyncSandbox if mode == "async" else Sandbox
    return cls(api(server, mode), {"id": SBX, "state": "active"})


def splits(data: bytes) -> list[list[bytes]]:
    """The same bytes in one chunk, byte by byte, inside a UTF-8 character, and CRLF split."""
    accent = data.index("é".encode()) + 1
    crlf = data.replace(b"\n", b"\r\n")
    cut = crlf.index(b"\r\n") + 1
    return [[data], [bytes([b]) for b in data], [data[:accent], data[accent:]], [crlf[:cut], crlf[cut:]]]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("split", range(4))
def test_run_reads_every_chunking_and_returns_a_non_zero_exit(mode, split):
    server = MockServer()
    server.on("sandboxes.commands.run", lambda r: stream_response(Chunks(splits(HELLO)[split])))
    seen_out, seen_err = [], []
    sbx = handle(server, mode)
    result = run(resolve(sbx.commands.run("echo", on_stdout=seen_out.append, on_stderr=seen_err.append)))
    assert result.exit_code == 3 and result.exec_id == EXEC
    assert result.stdout == "héllo\n" and result.stderr == "warn\n"
    assert seen_out == ["héllo\n"] and seen_err == ["warn\n"]
    assert result.stdout_bytes == 7 and result.stderr_bytes == 5 and result.duration_ms == 5
    assert not (result.timed_out or result.cancelled or result.truncated)
    assert result.signal is None and result.error is None and result.exit.exit_code == 3
    assert server.last.json() == {"command": "echo"}


@pytest.mark.parametrize("mode", MODES)
def test_run_sends_cwd_env_and_timeout(mode):
    server = MockServer()
    run(resolve(handle(server, mode).commands.run("ls", cwd="src", env={"A": "1"}, timeout_seconds=9)))
    assert server.last.json() == {"command": "ls", "cwd": "src", "env": {"A": "1"}, "timeoutSeconds": 9}


EXITS = {
    "timeout": ({"exitCode": None, "signal": "SIGKILL", "timedOut": True, "durationMs": 9000},
                {"exit_code": None, "signal": "SIGKILL", "timed_out": True, "duration_ms": 9000}),
    "signal": ({"exitCode": None, "signal": "SIGTERM"}, {"exit_code": None, "signal": "SIGTERM", "timed_out": False}),
    "cancel": ({"exitCode": None, "signal": "SIGTERM", "cancelled": True}, {"exit_code": None, "cancelled": True}),
    "truncated": ({"exitCode": 0, "truncated": True, "stdoutBytes": 99999}, {"exit_code": 0, "truncated": True,
                                                                              "stdout_bytes": 99999}),
    "spawn-error": ({"exitCode": None, "error": "spawn /bin/nope ENOENT"},
                    {"exit_code": None, "error": "spawn /bin/nope ENOENT", "signal": None}),
}


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("kind", sorted(EXITS))
def test_every_exit_record_is_a_result_not_an_error(mode, kind):
    wire, expected = EXITS[kind]
    server = MockServer()
    body = sse(STARTED, ("stdout", {"data": "so far"}), ("exit", {**EXIT0, **wire}))
    server.on("sandboxes.commands.run", lambda r: stream_response(body))
    result = run(resolve(handle(server, mode).commands.run("x")))
    for field, value in expected.items():
        assert getattr(result, field) == value, (kind, field)
    assert result.stdout == "so far" and result.exec_id == EXEC and len(server.seen) == 1


@pytest.mark.parametrize("mode", MODES)
def test_a_stream_without_an_exit_frame_is_incomplete(mode):
    server = MockServer()
    body = sse(STARTED, ("stdout", {"data": "partial"}))
    server.on("sandboxes.commands.run", lambda r: stream_response(Chunks([body, b"event: exit\ndata: {"])))
    with pytest.raises(CommandIncompleteError) as caught:
        run(resolve(handle(server, mode).commands.run("long")))
    assert caught.value.exec_id == EXEC and caught.value.stdout == "partial"
    assert len(server.seen) == 1  # never run again


@pytest.mark.parametrize("mode", MODES)
def test_a_dropped_connection_mid_command_is_incomplete_and_not_retried(mode):
    server = MockServer()
    body = Chunks([sse(STARTED)], fail=httpx.ReadError("reset"))
    server.on("sandboxes.commands.run", lambda r: stream_response(body))
    with pytest.raises(CommandIncompleteError) as caught:
        run(resolve(handle(server, mode).commands.run("long")))
    assert isinstance(caught.value.__cause__, SandboxConnectionError)
    assert "unknown" in str(caught.value) and len(server.seen) == 1


@pytest.mark.parametrize("mode", MODES)
def test_an_error_frame_raises_command_failed(mode):
    server = MockServer()
    body = sse(STARTED, ("stdout", {"data": "a"}), ("error", {"message": "runtime died"}))
    server.on("sandboxes.commands.run", lambda r: stream_response(body))
    with pytest.raises(CommandFailedError, match="runtime died") as caught:
        run(resolve(handle(server, mode).commands.run("x")))
    assert caught.value.exec_id == EXEC and caught.value.stdout == "a"


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("status", [429, 502, 503])
def test_exec_is_never_retried(mode, status):
    server = MockServer()
    server.on("sandboxes.commands.run", error(status))
    with pytest.raises(Exception) as caught:
        run(resolve(handle(server, mode).commands.run("x")))
    assert getattr(caught.value, "status", None) == status
    assert len(server.seen) == 1


@pytest.mark.parametrize("mode", MODES)
def test_stream_yields_typed_frames_and_keeps_unknown_events(mode):
    server = MockServer()
    body = sse(STARTED, ("progress", {"pct": 5}), ("stdout", {"data": "x"}), ("exit", EXIT0))
    server.on("sandboxes.commands.run", lambda r: stream_response(body))

    async def go():
        stream = handle(server, mode).commands.stream("x")
        frames = await collect(stream)
        assert stream.exec_id == EXEC
        return frames

    frames = run(go())
    assert [type(f) for f in frames] == [StartedFrame, UnknownFrame, StdoutFrame, ExitFrame]
    assert frames[1].event == "progress" and frames[1].data == {"pct": 5}
    assert frames[0].raw == {"event": "started", "id": "1", "data": STARTED[1]}
    assert frames[3].exit_code == 0


@pytest.mark.parametrize("mode", MODES)
def test_a_whole_frame_in_data_is_read_too(mode):
    server = MockServer()
    body = b'data: {"event": "stdout", "id": "2", "data": {"data": "y"}}\n\n'
    server.on("sandboxes.commands.run", lambda r: stream_response(body + sse(("exit", EXIT0))))
    frames = run(collect(handle(server, mode).commands.stream("x")))
    assert isinstance(frames[0], StdoutFrame) and frames[0].data == "y" and frames[0].id == "2"


@pytest.mark.parametrize("mode", MODES)
def test_closing_the_stream_closes_the_connection(mode):
    server = MockServer()
    body = Chunks([sse(STARTED), sse(("stdout", {"data": "tick"}))])
    server.on("sandboxes.commands.run", lambda r: stream_response(body))

    async def go():
        stream = handle(server, mode).commands.stream("tail -f log")
        iterator = stream.__aiter__() if mode == "async" else iter(stream)
        first = await resolve(iterator.__anext__() if mode == "async" else next(iterator))
        assert isinstance(first, StartedFrame) and not body.closed
        await close(stream)

    run(go())
    assert body.closed  # the server cancels a command whose stream closed
    assert len(server.seen) == 1


@pytest.mark.parametrize("mode", MODES)
def test_breaking_out_of_a_with_block_closes_the_connection(mode):
    server = MockServer()
    body = Chunks([sse(STARTED), sse(("stdout", {"data": "tick"}))])
    server.on("sandboxes.commands.run", lambda r: stream_response(body))
    sbx = handle(server, mode)

    async def go():
        if mode == "async":
            async with sbx.commands.stream("x") as stream:
                async for _frame in stream:
                    break
        else:
            with sbx.commands.stream("x") as stream:
                for _frame in stream:
                    break

    run(go())
    assert body.closed


@pytest.mark.parametrize("mode", MODES)
def test_commands_cancel_posts_the_exec_id(mode):
    server = MockServer()
    run(resolve(handle(server, mode).commands.cancel(EXEC)))
    assert server.last.name == "sandboxes.commands.cancel"
    assert server.last.request.url.path.endswith(f"/exec/{EXEC}/cancel")
