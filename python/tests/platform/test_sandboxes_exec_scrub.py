"""The exec stream's server-written failure text (an ``error`` frame's ``message``, an ``exit``
frame's ``error``) passes through the HTTP error path's scrubber and length cap, with every secret
the request carried (the key pair or token, FI_EXTRA_HEADERS values, ``commands.run``'s ``env``
values), before it reaches a frame, ``CommandFailedError``, a ``CommandResult`` or the command line
(text and ``--json``). Sync and async; fake credentials only."""

from __future__ import annotations

import asyncio
import json

import pytest
from fi._core.redact import REDACTED
from fi._core.transport import MAX_ERROR_BODY
from fi.sandbox import (
    AsyncSandbox,
    CommandFailedError,
    ErrorFrame,
    ExitFrame,
    Sandbox,
    _connection,
)

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    exec_body,
    run,
    server_fixture,
)
from ._sandbox_mock import (
    EXEC,
    FAKE_KEY,
    FAKE_SECRET,
    FAKE_TOKEN,
    HOSTED,
    MODES,
    SBX,
    MockServer,
    collect,
    resolve,
    sse,
    stream_response,
)

PROXY_TOKEN = "fake-proxy-token-" + "z" * 12
ENV_VALUE = "fake-env-value-" + "q" * 10
STARTED = ("started", {"execId": EXEC, "sandboxId": SBX})
LEAKS = (FAKE_KEY, FAKE_SECRET, PROXY_TOKEN, ENV_VALUE)


@pytest.fixture(name="hosted")
def hosted_fixture(monkeypatch):
    for name in ("FUTUREAGI_OMEGA_API_KEY", "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID", "FI_ALLOW_CUSTOM_PLATFORM_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OMEGA_BASE_URL", HOSTED)
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    monkeypatch.setenv("FI_EXTRA_HEADERS", f"Proxy-Authorization=Bearer {PROXY_TOKEN}")
    mock = MockServer()
    monkeypatch.setattr(_connection, "default_transport", mock.transport)
    return mock


def leaky(*secrets):
    return "the runtime saw " + ", ".join(secrets) + " and died"


def cls(mode):
    return AsyncSandbox if mode == "async" else Sandbox


def assert_clean(text):
    assert not any(secret in text for secret in LEAKS + (FAKE_TOKEN,)), text


def answer(*frames):
    return lambda request: stream_response(sse(STARTED, *frames))


@pytest.mark.parametrize("mode", MODES)
def test_an_error_frame_is_scrubbed_before_command_failed(mode, hosted):
    hosted.on("sandboxes.commands.run", answer(("error", {"message": leaky(*LEAKS)})))

    async def go():
        sbx = await resolve(cls(mode).connect(SBX))
        return await resolve(sbx.commands.run("env", env={"TOKEN_VAR": ENV_VALUE}))

    with pytest.raises(CommandFailedError) as caught:
        asyncio.run(go())
    text = str(caught.value) + repr(caught.value)
    assert_clean(text)
    assert REDACTED in str(caught.value) and "the runtime saw" in str(caught.value)
    assert hosted.last.request.headers["proxy-authorization"] == f"Bearer {PROXY_TOKEN}"


@pytest.mark.parametrize("mode", MODES)
def test_an_exit_error_is_scrubbed_in_the_result_and_in_raw(mode, hosted):
    exit_frame = {"exitCode": None, "error": "spawn failed: " + leaky(*LEAKS)}
    hosted.on("sandboxes.commands.run", answer(("exit", exit_frame)))

    async def go():
        sbx = await resolve(cls(mode).connect(SBX))
        result = await resolve(sbx.commands.run("x", env={"TOKEN_VAR": ENV_VALUE}))
        frames = await collect(sbx.commands.stream("x", env={"TOKEN_VAR": ENV_VALUE}))
        return result, frames

    result, frames = asyncio.run(go())
    assert result.error.startswith("spawn failed: the runtime saw ") and REDACTED in result.error
    assert_clean(result.error)
    last = frames[-1]
    assert isinstance(last, ExitFrame) and REDACTED in last.error
    assert_clean(last.error + json.dumps(last.raw))
    assert last.raw["data"]["error"] == last.error


@pytest.mark.parametrize("mode", MODES)
def test_a_streamed_error_frame_is_scrubbed_in_raw_too(mode, hosted):
    hosted.on("sandboxes.commands.run", answer(("error", {"message": leaky(FAKE_SECRET), "code": "x"})))

    async def go():
        sbx = await resolve(cls(mode).connect(SBX))
        return await collect(sbx.commands.stream("ls"))

    frames = asyncio.run(go())
    failed = frames[-1]
    assert isinstance(failed, ErrorFrame) and REDACTED in failed.message
    assert failed.raw["data"] == {"message": failed.message, "code": "x"}
    assert_clean(failed.message + json.dumps(failed.raw))


@pytest.mark.parametrize("mode", MODES)
def test_the_frame_text_is_capped_like_an_error_body(mode, hosted):
    hosted.on("sandboxes.commands.run", answer(("error", {"message": "é" * MAX_ERROR_BODY})))

    async def go():
        sbx = await resolve(cls(mode).connect(SBX))
        return await collect(sbx.commands.stream("ls"))

    failed = asyncio.run(go())[-1]
    assert len(failed.message.encode("utf-8")) <= MAX_ERROR_BODY + 3
    assert len(failed.message) < MAX_ERROR_BODY and failed.message.startswith("éé")


@pytest.mark.parametrize("mode", MODES)
def test_a_self_host_token_is_scrubbed_too(mode, monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_EXTRA_HEADERS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OMEGA_BASE_URL", "http://127.0.0.1:8787")
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", FAKE_TOKEN)
    server = MockServer()
    monkeypatch.setattr(_connection, "default_transport", server.transport)
    server.on("sandboxes.commands.run", answer(("error", {"message": leaky(FAKE_TOKEN)})))

    async def go():
        sbx = await resolve(cls(mode).connect(SBX))
        return await resolve(sbx.commands.run("ls"))

    with pytest.raises(CommandFailedError) as caught:
        asyncio.run(go())
    assert FAKE_TOKEN not in str(caught.value) and REDACTED in str(caught.value)


def test_the_command_line_prints_only_scrubbed_frame_text(server, capsys):
    server.on("sandboxes.commands.run", exec_body(("error", {"message": leaky(FAKE_TOKEN, ENV_VALUE)})))
    assert run("exec", "--env", f"TOKEN_VAR={ENV_VALUE}", SBX, "--", "env") == 1
    err = capsys.readouterr().err
    assert err.startswith("command_failed: ") and REDACTED in err
    assert_clean(err)
    server.on("sandboxes.commands.run", exec_body(("exit", {"exitCode": None, "error": leaky(FAKE_TOKEN)})))
    assert run("exec", SBX, "--", "nope") == 1
    err = capsys.readouterr().err
    assert err.startswith("spawn_failed: ") and REDACTED in err
    assert_clean(err)


def test_the_command_line_json_frames_are_scrubbed(server, capsys):
    server.on("sandboxes.commands.run", exec_body(("error", {"message": leaky(FAKE_TOKEN, ENV_VALUE)})))
    assert run("exec", "--json", "--env", f"TOKEN_VAR={ENV_VALUE}", SBX, "--", "env") == 1
    captured = capsys.readouterr()
    frames = [json.loads(line) for line in captured.out.splitlines()]
    assert frames[-1]["event"] == "error" and REDACTED in frames[-1]["data"]["message"]
    assert_clean(captured.out + captured.err)
