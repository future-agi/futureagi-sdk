"""The channel token stays out of every text a caller or a log can see (repr, str, format, error
text, DEBUG logs of the WebSocket library), and a slow reader is not cut off by keepalive pings
while the server holds output for want of credit."""

from __future__ import annotations

import copy
import dataclasses
import functools
import inspect
import logging
import time
import traceback

import fi.sandbox._channel._async.stream as async_stream
import fi.sandbox._channel._client as channel_client
import fi.sandbox._channel._sync.stream as sync_stream
import pytest
from fi.sandbox import SandboxError
from fi.sandbox._channel import connect
from fi.sandbox.channel_errors import ChannelClosedError

from ._channel_support import (  # noqa: F401
    SBX,
    async_sandbox,
    channel_fixture,
    sync_sandbox,
)

REPLY = {
    "channel": {
        "url": f"wss://example.test/workspace/sandboxes/{SBX}/channel",
        "token": "sct_SECRETSECRETSECRETSECRETSECRETSECRETSECRET1",
        "transport": {
            "protocols": ["omega.channel.v1", "omega.token.sct_SECRETSECRETSECRETSECRETSECRETSECRETSECRET1"]
        },
    }
}
TOKEN = REPLY["channel"]["token"]


def texts(error):
    """Every text of an exception and the ones it came from."""
    seen, out = set(), []
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        out += [repr(error), str(error), f"{error}", "".join(traceback.format_exception(error))]
        error = error.__cause__ or error.__context__
    return out


# -- the connection settings --------------------------------------------------------------------


def test_the_connection_settings_print_no_token():
    plan = connect.plan(REPLY, "https://example.test")
    for text in (repr(plan), str(plan), f"{plan}", format(plan, ""), f"{plan!r}", repr([plan]), repr({"p": plan})):
        assert "SECRET" not in text and "omega.token" not in text, text
    # the settings still carry what connecting needs
    assert plan.protocols == REPLY["channel"]["transport"]["protocols"] and plan.token == TOKEN


def test_the_connection_settings_hold_the_token_outside_their_fields():
    plan = connect.plan(REPLY, "https://example.test")
    views = (dataclasses.asdict(plan), dataclasses.astuple(plan), vars(plan), copy.copy(plan), copy.deepcopy(plan))
    for view in views:
        text = repr(view)
        assert "SECRET" not in text and "omega.token" not in text, text
    assert all("SECRET" not in repr(getattr(plan, f.name)) for f in dataclasses.fields(plan))
    # a copy still connects with the same protocols and scrubs the same token
    assert copy.deepcopy(plan).protocols == plan.protocols and copy.copy(plan).token == TOKEN


# -- an error raised while connecting -----------------------------------------------------------


def spend_tokens_before_connect(monkeypatch, channel):
    real = channel_client.channel_token

    def mint(part, sandbox_id):
        reply = real(part, sandbox_id)
        channel.tokens.clear()  # the upgrade is then refused: the token is not valid
        return reply

    monkeypatch.setattr(channel_client, "channel_token", mint)


def test_a_refused_upgrade_carries_no_token_in_any_text(channel, monkeypatch):
    spend_tokens_before_connect(monkeypatch, channel)
    sbx, core = sync_sandbox(channel)
    with pytest.raises(Exception) as caught:
        sbx.commands.exec_stream(["true"])
    core.shared.close()
    token = channel.minted[0]["token"]
    assert channel.refusals
    for text in texts(caught.value):
        assert token not in text and "omega.token" not in text, text


@pytest.mark.asyncio
async def test_a_refused_upgrade_carries_no_token_in_any_text_async(channel, monkeypatch):
    from fi.sandbox._channel import _async_client as async_client

    asyncio_real = async_client.channel_token

    async def mint(part, sandbox_id):
        reply = await asyncio_real(part, sandbox_id)
        channel.tokens.clear()
        return reply

    monkeypatch.setattr(async_client, "channel_token", mint)
    sbx, core = async_sandbox(channel)
    with pytest.raises(Exception) as caught:
        await sbx.commands.exec_stream(["true"])
    await core.shared.aclose()
    token = channel.minted[0]["token"]
    assert channel.refusals
    for text in texts(caught.value):
        assert token not in text and "omega.token" not in text, text


# -- DEBUG logs of the WebSocket library --------------------------------------------------------


def client_records(caplog):
    """The records of the client side (the fake server of these tests logs in this process too)."""
    return [r for r in caplog.records if not r.name.startswith("websockets.server")]


def test_debug_logging_holds_no_token_sync(channel, caplog):
    caplog.set_level(logging.DEBUG)
    sbx, core = sync_sandbox(channel)
    with sbx.commands.exec_stream(["cat"], stdin=b"hello") as stream:
        assert stream.read_stdout() == b"hello"
        stream.wait()
    core.shared.close()
    token = channel.minted[0]["token"]
    for record in client_records(caplog):
        assert token not in record.getMessage() and token not in repr(record.args), record.getMessage()


@pytest.mark.asyncio
async def test_debug_logging_holds_no_token_async(channel, caplog):
    caplog.set_level(logging.DEBUG)
    sbx, core = async_sandbox(channel)
    async with await sbx.commands.exec_stream(["cat"], stdin=b"hello") as stream:
        assert await stream.read_stdout() == b"hello"
        await stream.wait()
    await core.shared.aclose()
    token = channel.minted[0]["token"]
    for record in client_records(caplog):
        assert token not in record.getMessage() and token not in repr(record.args), record.getMessage()


def test_the_global_websockets_loggers_are_left_alone(channel):
    before = {n: logging.getLogger(n).level for n in ("websockets", "websockets.client", "websockets.server")}
    sbx, core = sync_sandbox(channel)
    with sbx.commands.exec_stream(["true"]) as stream:
        stream.wait()
    core.shared.close()
    assert before == {n: logging.getLogger(n).level for n in before}


# -- keepalive pings against credit backpressure ------------------------------------------------

BIG = "head -c 1048576 /dev/zero"


def short_pings(monkeypatch, module):
    """The library's own keepalive, made short (0.2 s interval, 0.3 s timeout) wherever the client
    does not state its own policy: the old 20 s, 20 s defaults at test speed."""
    real = module.ws_connect
    if "ping_interval" not in inspect.signature(real).parameters:
        pytest.skip("this websockets release has no client keepalive")

    @functools.wraps(real)
    def connect_with(*args, **kwargs):
        kwargs.setdefault("ping_interval", 0.2)
        kwargs.setdefault("ping_timeout", 0.3)
        return real(*args, **kwargs)

    monkeypatch.setattr(module, "ws_connect", connect_with)


def test_a_slow_reader_survives_withheld_pongs_sync(channel, monkeypatch):
    short_pings(monkeypatch, sync_stream)
    sbx, core = sync_sandbox(channel)
    with sbx.commands.exec_stream(["sh", "-c", BIG]) as stream:
        channel.withhold_pongs = True
        time.sleep(1.5)  # unread: the server holds output for want of credit, and answers no ping
        assert channel.sent <= 262144
        total = 0
        try:
            while chunk := stream.read_stdout():
                total += len(chunk)
        except (ChannelClosedError, SandboxError) as error:  # a keepalive close
            pytest.fail(f"the connection was closed while output was unread: {error!r}")
        done = stream.wait()
    core.shared.close()
    assert total == 1048576 and done.exit_code == 0


@pytest.mark.asyncio
async def test_a_slow_reader_survives_withheld_pongs_async(channel, monkeypatch):
    import asyncio

    short_pings(monkeypatch, async_stream)
    sbx, core = async_sandbox(channel)
    async with await sbx.commands.exec_stream(["sh", "-c", BIG]) as stream:
        channel.withhold_pongs = True
        await asyncio.sleep(1.5)
        assert channel.sent <= 262144
        total = 0
        try:
            while chunk := await stream.read_stdout():
                total += len(chunk)
        except (ChannelClosedError, SandboxError) as error:
            pytest.fail(f"the connection was closed while output was unread: {error!r}")
        done = await stream.wait()
    await core.shared.aclose()
    assert total == 1048576 and done.exit_code == 0
