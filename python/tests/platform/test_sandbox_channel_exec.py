"""Exec streams over the channel, sync and async: binary round trips (NUL bytes, 5 MB), stdin
half-close, separate stderr and the exit record, credit-based backpressure both ways, typed close
reasons, one token per connection, no cookie, and the Origin header. Every command really runs
(the fake server executes argv on this machine)."""

from __future__ import annotations

import os
import threading
import time

import fi.sandbox as sandbox
import pytest
from fi.sandbox import ExitFrame, SandboxError

from ._channel_fake import FakeChannel
from ._channel_support import async_sandbox, channel_fixture, sync_sandbox  # noqa: F401

ALL_BYTES = bytes(range(256))


@pytest.fixture(name="sbx")
def sbx_fixture(channel):
    sbx, core = sync_sandbox(channel)
    yield sbx
    core.shared.close()


def read_all(stream, kind="stdout"):
    out = []
    read = getattr(stream, f"read_{kind}")
    while chunk := read():
        out.append(chunk)
    return b"".join(out)


# -- round trips --------------------------------------------------------------------------------


def test_binary_round_trip_with_nul_bytes_and_every_byte_value(sbx, channel):
    payload = ALL_BYTES * 3 + b"\x00\x00\x00" + b"\xff\xfe invalid utf-8 \xc3\x28"
    with sbx.commands.exec_stream(["cat"]) as stream:
        assert stream.exec_id and stream.exec_id.startswith("exec_")
        stream.write(payload)
        stream.close_stdin()
        assert read_all(stream) == payload
        done = stream.wait()
    assert isinstance(done, ExitFrame) and done.exit_code == 0 and not done.timed_out
    assert done.stdout_bytes == len(payload)


def test_five_megabytes_round_trip_under_the_windows(sbx, channel):
    payload = os.urandom(5 * 1024 * 1024 - 7) + b"\x00" * 7
    with sbx.commands.exec_stream(["cat"], stdin=payload) as stream:
        got = read_all(stream)
        done = stream.wait()
    assert got == payload and done.exit_code == 0 and done.stdout_bytes == len(payload)
    assert channel.max_stdin_pending <= 32768 and channel.flow_errors == 0
    assert channel.max_unreleased <= 262144


def test_stdin_half_close_then_remote_output(sbx):
    with sbx.commands.exec_stream(["sh", "-c", "cat > /dev/null; echo after-eof"]) as stream:
        stream.write(b"some input\n")
        stream.close_stdin()
        assert read_all(stream) == b"after-eof\n"
        assert stream.wait().exit_code == 0


def test_stderr_is_separate_and_the_exit_code_is_the_commands(sbx):
    with sbx.commands.exec_stream(["sh", "-c", "echo out; echo err >&2; exit 3"]) as stream:
        out, err = read_all(stream, "stdout"), read_all(stream, "stderr")
        done = stream.wait()
    assert (out, err) == (b"out\n", b"err\n")
    assert done.exit_code == 3 and done.stdout_bytes == 4 and done.stderr_bytes == 4


def test_iteration_yields_tagged_chunks_in_arrival_order(sbx):
    with sbx.commands.exec_stream(["sh", "-c", "printf a; sleep 0.2; printf b >&2"]) as stream:
        chunks = [(c.stream, c.data) for c in stream]
        stream.wait()
    assert chunks == [("stdout", b"a"), ("stderr", b"b")]


def test_a_signal_ends_the_command_without_an_exit_code(sbx):
    with sbx.commands.exec_stream(["sh", "-c", "kill -9 $$"]) as stream:
        done = stream.wait()
    assert done.exit_code is None and done.signal == "SIGKILL"


def test_cancel_stops_the_command(sbx, channel):
    with sbx.commands.exec_stream(["sleep", "30"]) as stream:
        stream.cancel()
        done = stream.wait()
    assert done.cancelled and done.signal == "SIGTERM"
    assert channel.wait_idle()


def test_time_limit(sbx):
    with sbx.commands.exec_stream(["sleep", "30"], timeout_seconds=1) as stream:
        done = stream.wait()
    assert done.timed_out


def test_argv_is_a_list_and_cwd_and_env_apply(sbx, channel):
    argv = ["printf", "%s\n", "a b", "$HOME", "*", "it's", "x\ny"]
    with sbx.commands.exec_stream(argv) as stream:
        assert read_all(stream) == b"a b\n$HOME\n*\nit's\nx\ny\n"
    with sbx.commands.exec_stream(["sh", "-c", "pwd; echo $WHO"], cwd="sub", env={"WHO": "me"}) as stream:
        assert read_all(stream) == (str(channel.root / "sub") + "\nme\n").encode()


def test_leaving_the_with_block_stops_a_running_command(sbx, channel):
    with sbx.commands.exec_stream(["sleep", "30"]):
        pass
    assert channel.wait_idle()


def test_unread_output_is_dropped_by_wait_so_the_command_can_end(sbx):
    with sbx.commands.exec_stream(["sh", "-c", "head -c 3000000 /dev/zero"]) as stream:
        done = stream.wait()
    assert done.exit_code == 0 and done.stdout_bytes == 3000000


# -- backpressure -------------------------------------------------------------------------------


def test_a_reader_that_never_reads_leaves_the_command_blocked_within_the_window(sbx, channel):
    with sbx.commands.exec_stream(["sh", "-c", "head -c 6291456 /dev/zero"]) as stream:
        time.sleep(0.6)
        assert channel.sent <= 262144
        assert stream.buffered_bytes <= 262144
        total = len(read_all(stream))
        stream.wait()
    assert total == 6291456


def test_a_slow_reader_never_holds_more_than_the_window(sbx, channel):
    consumed, worst_unconsumed, worst_buffered = 0, 0, 0
    with sbx.commands.exec_stream(["sh", "-c", "head -c 6291456 /dev/zero"]) as stream:
        while chunk := stream.read_stdout(65536):
            consumed += len(chunk)
            time.sleep(0.004)
            worst_unconsumed = max(worst_unconsumed, channel.sent - consumed)
            worst_buffered = max(worst_buffered, stream.buffered_bytes)
        stream.wait()
    assert consumed == 6291456
    assert worst_unconsumed <= 262144, worst_unconsumed
    assert worst_buffered <= 262144, worst_buffered
    assert channel.max_unreleased <= 262144


def test_stdin_never_runs_past_the_window_when_the_command_is_slow(sbx, channel):
    payload = os.urandom(4 * 1024 * 1024)
    with sbx.commands.exec_stream(["sh", "-c", "sleep 0.4; cat > /dev/null"]) as stream:
        stream.write(payload)
        stream.close_stdin()
        done = stream.wait()
    assert done.exit_code == 0
    assert 0 < channel.max_stdin_pending <= 32768 and channel.flow_errors == 0


# -- typed close reasons ------------------------------------------------------------------------


@pytest.mark.parametrize("code,reason,cls", [
    (4409, "emergency_stop", "ChannelEmergencyStopError"),      # stop
    (4410, "sandbox_hibernated", "ChannelSandboxHibernatedError"),  # pause / hibernate
    (4404, "sandbox_gone", "ChannelSandboxGoneError"),          # destroy
    (4401, "access_revoked", "ChannelAccessRevokedError"),      # epoch bump / revoked
    (4411, "sandbox_frozen", "ChannelSandboxFrozenError"),
    (1001, "server_stopping", "ChannelServerStoppingError"),
])
def test_close_reasons_are_typed_and_stop_the_command(sbx, channel, code, reason, cls):
    cls = getattr(sandbox, cls)
    stream = sbx.commands.exec_stream(["sleep", "30"])
    channel.close_sockets(code, reason)
    with pytest.raises(cls) as caught:
        stream.wait()
    error = caught.value
    assert isinstance(error, sandbox.ChannelClosedError) and isinstance(error, SandboxError)
    assert error.close_code == code and error.reason == reason
    with pytest.raises(cls):
        stream.read_stdout()
    with pytest.raises(cls):
        stream.write(b"x")
    stream.close()
    assert channel.wait_idle()


def test_a_close_after_the_exit_record_is_not_an_error(sbx, channel):
    with sbx.commands.exec_stream(["true"]) as stream:
        assert stream.wait().exit_code == 0
    channel.close_sockets(4410, "sandbox_hibernated")
    assert stream.exit.exit_code == 0


def test_output_that_arrived_before_the_close_is_readable(sbx, channel):
    stream = sbx.commands.exec_stream(["sh", "-c", "echo early; sleep 30"])
    deadline = time.monotonic() + 5
    while not stream.buffered_bytes and time.monotonic() < deadline:
        time.sleep(0.01)
    channel.close_sockets(4410, "sandbox_hibernated")
    assert stream.read_stdout() == b"early\n"
    with pytest.raises(sandbox.ChannelSandboxHibernatedError):
        stream.read_stdout()
    stream.close()


# -- tokens, cookies, origin --------------------------------------------------------------------


def test_every_connection_mints_its_own_single_use_token(sbx, channel):
    for _ in range(2):
        with sbx.commands.exec_stream(["true"]) as stream:
            stream.wait()
    first, second = channel.minted
    assert len(channel.mints) == 2 and first["token"] != second["token"]
    for minted, upgrade in zip(channel.minted, channel.upgrades):
        offered = [p.strip() for p in upgrade["headers"]["sec-websocket-protocol"].split(",")]
        assert offered == minted["transport"]["protocols"]  # exactly transport.protocols
    assert channel.refusals == []


def test_a_used_token_is_refused_on_a_second_connection(sbx, channel):
    from websockets.exceptions import InvalidStatus
    from websockets.sync.client import connect

    with sbx.commands.exec_stream(["true"]) as stream:
        stream.wait()
    used = channel.minted[0]
    with pytest.raises(InvalidStatus) as caught:
        connect(used["url"], subprotocols=used["transport"]["protocols"], origin=channel.origin)
    assert caught.value.response.status_code == 401
    assert channel.refusals[-1] == (401, "token_invalid")


def test_no_cookie_and_no_credential_in_the_upgrade_or_its_url(sbx, channel):
    with sbx.commands.exec_stream(["true"]) as stream:
        stream.wait()
    (upgrade,) = channel.upgrades
    assert "cookie" not in upgrade["headers"] and "authorization" not in upgrade["headers"]
    assert "?" not in upgrade["path"] and "sct_" not in upgrade["path"]
    assert "x-api-key" not in upgrade["headers"] and "x-secret-key" not in upgrade["headers"]


def test_origin_is_derived_from_the_api_base_url(tmp_path):
    with FakeChannel(tmp_path, api_prefix="/omega/api") as server:
        sbx, core = sync_sandbox(server)
        with sbx.commands.exec_stream(["true"]) as stream:
            stream.wait()
        core.shared.close()
    (upgrade,) = server.upgrades
    assert server.base_url.endswith("/omega/api")
    assert upgrade["headers"]["origin"] == server.origin  # scheme, host and port: no path


def test_the_socket_offers_only_the_servers_protocol_and_no_extension(sbx, channel):
    with sbx.commands.exec_stream(["true"]) as stream:
        stream.wait()
    assert "sec-websocket-extensions" not in channel.upgrades[0]["headers"]


# -- async --------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_round_trip_half_close_stderr_and_exit(channel):
    sbx, core = async_sandbox(channel)
    payload = ALL_BYTES + b"\x00" * 5
    async with await sbx.commands.exec_stream(["sh", "-c", "cat; echo err >&2; exit 4"]) as stream:
        await stream.write(payload)
        await stream.close_stdin()
        out = b""
        while chunk := await stream.read_stdout():
            out += chunk
        err = b""
        while chunk := await stream.read_stderr():
            err += chunk
        done = await stream.wait()
    await core.shared.aclose()
    assert out == payload and err == b"err\n" and done.exit_code == 4


@pytest.mark.asyncio
async def test_async_large_payload_with_background_stdin(channel):
    sbx, core = async_sandbox(channel)
    payload = os.urandom(2 * 1024 * 1024)
    async with await sbx.commands.exec_stream(["cat"], stdin=payload) as stream:
        got = b""
        async for chunk in stream:
            got += chunk.data
        done = await stream.wait()
    await core.shared.aclose()
    assert got == payload and done.exit_code == 0
    assert channel.max_stdin_pending <= 32768 and channel.flow_errors == 0 and channel.max_unreleased <= 262144


@pytest.mark.asyncio
async def test_async_close_reason_is_typed(channel):
    sbx, core = async_sandbox(channel)
    stream = await sbx.commands.exec_stream(["sleep", "30"])
    threading.Timer(0.2, channel.close_sockets, args=(4404, "sandbox_gone")).start()
    with pytest.raises(sandbox.ChannelSandboxGoneError) as caught:
        await stream.wait()
    assert caught.value.close_code == 4404
    await stream.close()
    await core.shared.aclose()
    assert channel.wait_idle()


@pytest.mark.asyncio
async def test_async_cancel_and_context_exit(channel):
    sbx, core = async_sandbox(channel)
    async with await sbx.commands.exec_stream(["sleep", "30"]) as stream:
        await stream.cancel()
        done = await stream.wait()
    assert done.cancelled
    async with await sbx.commands.exec_stream(["sleep", "30"]):
        pass
    await core.shared.aclose()
    assert channel.wait_idle()
