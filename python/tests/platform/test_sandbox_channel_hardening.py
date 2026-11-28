"""The channel's connection rules and what a refusal can carry: one strict URL rule (wss, or ws only to
a loopback channel host), no query, fragment or credential, the offered protocols checked before any
socket opens, no redirect on the handshake, no token in a traceback's locals or in server text, and a
self command that does not import from the working directory."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping

import pytest
from fi._cli import sandbox_channel as cli_channel
from fi.errors import ConfigurationError
from fi.sandbox import SandboxError
from fi.sandbox._channel import connect
from fi.sandbox._channel.protocol import StreamError
from fi.sandbox.channel_errors import ChannelProtocolError, channel_closed

from ._channel_fake import FakeChannel
from ._channel_support import SBX, channel_fixture, sync_sandbox  # noqa: F401

TOKEN = "sct_HARDENINGHARDENINGHARDENINGHARDENING000001"
PROTOCOLS = ["omega.channel.v1", "omega.token." + TOKEN]


def reply(url, protocols=None, token=TOKEN):
    return {"channel": {"url": url, "token": token,
                        "transport": {"protocols": PROTOCOLS if protocols is None else protocols}}}


def holds(value, token=TOKEN, depth=0):
    """Whether the token is in a value: a text, or inside a container or an exception's arguments."""
    if isinstance(value, str):
        return token in value
    if isinstance(value, bytes):
        return token.encode() in value
    if depth > 4:
        return False
    if isinstance(value, Mapping):
        return any(holds(k, token, depth + 1) or holds(v, token, depth + 1) for k, v in dict.items(value))
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(holds(v, token, depth + 1) for v in value)
    if isinstance(value, BaseException):
        return holds(value.args, token, depth + 1)
    return False


def leaks(error, token=TOKEN):
    """Where the token shows in an exception, its causes and contexts: their texts and the locals of
    every frame of their tracebacks (the frames of this file excluded)."""
    found, seen = [], set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        if holds(str(error), token) or holds(repr(error), token):
            found.append(f"text of {type(error).__name__}")
        tb = error.__traceback__
        while tb is not None:
            frame = tb.tb_frame
            if frame.f_code.co_filename != __file__:
                for name, value in frame.f_locals.items():
                    if holds(value, token):
                        found.append(f"{frame.f_code.co_name}.{name}")
            tb = tb.tb_next
        error = error.__cause__ or error.__context__
    return found


# -- the URL rule: the channel's own host decides, not the API's scheme ---------------------------


@pytest.mark.parametrize("api", ["https://api.example.test", "http://api.example.test", "http://127.0.0.1:8080"])
@pytest.mark.parametrize("url", ["ws://sandbox.example.test/channel", "ws://192.0.2.5:9/channel",
                                 "ws://localhost.example.test/channel", "ws://127.0.0.1.example.test/channel"])
def test_plain_ws_to_a_remote_channel_host_is_refused_whatever_the_api_scheme(url, api):
    with pytest.raises(ConfigurationError) as caught:
        connect.plan(reply(url), api)
    assert caught.value.code == "insecure_channel_origin"


@pytest.mark.parametrize("api", ["https://api.example.test", "http://api.example.test"])
@pytest.mark.parametrize("url", ["ws://127.0.0.1:9/channel", "ws://127.9.9.9/channel", "ws://[::1]:9/channel",
                                 "ws://localhost:9/channel", "wss://sandbox.example.test/channel"])
def test_wss_and_ws_to_a_loopback_channel_host_are_allowed_whatever_the_api_scheme(url, api):
    plan = connect.plan(reply(url), api)
    assert plan.url == url and plan.token == TOKEN


@pytest.mark.parametrize("url", ["wss://h.example.test/c?x=1", "wss://h.example.test/c#frag",
                                 "wss://user:pw@h.example.test/c", "wss://user@h.example.test/c"])
def test_a_query_fragment_or_credential_in_the_channel_url_is_refused(url):
    with pytest.raises(ChannelProtocolError):
        connect.plan(reply(url), "https://api.example.test")


@pytest.mark.parametrize("protocols", [["omega.channel.v1"], ["omega.token." + TOKEN],
                                       ["omega.channel.v1", "omega.token.sct_OTHER"]])
def test_protocols_without_the_subprotocol_or_the_token_are_refused(protocols):
    with pytest.raises(ChannelProtocolError):
        connect.plan(reply("wss://h.example.test/c", protocols), "https://api.example.test")


def test_a_refused_url_opens_no_socket(tmp_path):
    root = tmp_path / "w"
    root.mkdir()
    with FakeChannel(root, channel_url=f"ws://sandbox.example.test/workspace/sandboxes/{SBX}/channel") as server:
        sbx, _ = sync_sandbox(server)
        with pytest.raises(ConfigurationError) as caught:
            sbx.commands.exec_stream(["true"])
        assert caught.value.code == "insecure_channel_origin"
        assert server.upgrades == []


# -- no token in a traceback's locals --------------------------------------------------------------


@pytest.mark.parametrize("bad", [reply("ws://h.example.test/c"), reply("wss://h.example.test/c?q=1"),
                                 reply("wss://h.example.test/c", ["omega.channel.v1"]),
                                 {"channel": {"url": "wss://h.example.test/c", "token": TOKEN}}])
def test_a_refused_reply_leaves_the_token_out_of_every_frame(bad):
    with pytest.raises((ConfigurationError, ChannelProtocolError)) as caught:
        connect.plan(bad, "https://api.example.test")
    assert leaks(caught.value) == []


def test_a_refused_upgrade_leaves_the_token_out_of_every_frame(tmp_path):
    root = tmp_path / "w"
    root.mkdir()
    with FakeChannel(root) as server:
        server.token_ttl = -1  # every minted token is already expired: the upgrade answers 401
        sbx, _ = sync_sandbox(server)
        with pytest.raises(SandboxError) as caught:
            sbx.commands.exec_stream(["true"])
        token = server.minted[-1]["token"]
    assert leaks(caught.value, token) == []


# -- no redirect on the handshake ------------------------------------------------------------------


def test_a_redirect_on_the_handshake_is_not_followed(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    with FakeChannel(tmp_path / "a") as target:
        with FakeChannel(tmp_path / "b",
                         redirect_to=f"ws://127.0.0.1:{target.port}/workspace/sandboxes/{SBX}/channel") as front:
            sbx, _ = sync_sandbox(front)
            with pytest.raises(Exception) as caught:
                sbx.commands.exec_stream(["true"])
            assert front.upgrades, "the first server was never asked"
            assert target.upgrades == [], "the redirect target was connected to"
            assert leaks(caught.value, front.minted[-1]["token"]) == []


@pytest.mark.asyncio
async def test_async_a_redirect_on_the_handshake_is_not_followed(tmp_path):
    from ._channel_support import async_sandbox

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    with FakeChannel(tmp_path / "a") as target:
        with FakeChannel(tmp_path / "b",
                         redirect_to=f"ws://127.0.0.1:{target.port}/workspace/sandboxes/{SBX}/channel") as front:
            sbx, _ = async_sandbox(front)
            with pytest.raises(Exception):
                await sbx.commands.exec_stream(["true"])
            assert front.upgrades and target.upgrades == []


# -- server text is scrubbed ------------------------------------------------------------------------


def test_a_stream_error_message_is_scrubbed_of_the_token_and_control_characters():
    error = StreamError("validation", f"bad {TOKEN}\x1b[31m\x00 done " + "x" * 5000, {"note": TOKEN})
    out = connect.stream_refusal(error, scrub=lambda text: text.replace(TOKEN, "[token]"))
    assert TOKEN not in str(out) and "\x1b" not in str(out) and "\x00" not in str(out)
    assert len(str(out)) < 1500
    assert TOKEN not in repr(getattr(out, "payload", None)) and TOKEN not in repr(getattr(out, "detail", None))


def test_a_close_reason_is_scrubbed_of_the_token_and_control_characters():
    out = channel_closed(4999, f"gone {TOKEN}\x07" + "y" * 400, scrub=lambda text: text.replace(TOKEN, "[token]"))
    assert TOKEN not in str(out) and TOKEN not in (out.server_reason or "") and TOKEN not in repr(out.reason)
    assert "\x07" not in (out.server_reason or "") and len(out.server_reason or "") <= 200


def test_a_refused_upgrade_payload_is_scrubbed_of_the_token():
    body = ('{"error": {"code": "x", "message": "%s", "detail": {"echo": "%s"}}}' % (TOKEN, TOKEN)).encode()
    out = connect.refusal(400, body, {}, lambda text: text.replace(TOKEN, "[token]"))
    assert TOKEN not in str(out) and TOKEN not in repr(getattr(out, "payload", None)) \
        and TOKEN not in repr(getattr(out, "detail", None))


# -- the self command ------------------------------------------------------------------------------


def test_the_self_command_fallback_runs_python_isolated(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["/somewhere/other-script.py"])
    assert cli_channel.self_command("fi sandbox") == [sys.executable, "-I", "-m", "fi._cli"]


# -- one name for loopback, one parse for the check and the connect ---------------------------------


@pytest.mark.parametrize("url", ["ws://localhost./c", "ws://localhost.:9/c"])
def test_a_trailing_dot_name_is_not_loopback(url):
    with pytest.raises(ConfigurationError) as caught:
        connect.plan(reply(url), "https://api.example.test")
    assert caught.value.code == "insecure_channel_origin"


BYPASS_TABLE = [
    "127.0.0.1.nip.io", "localhost.evil", "[::ffff:127.0.0.1]", "0x7f.1", "2130706433", "LOCALHOST",
    "localhost.", "bücher.example", "127.0.0.1", "[::1]", "localhost",
]


@pytest.mark.parametrize("host", BYPASS_TABLE)
@pytest.mark.parametrize("scheme", ["ws", "wss"])
def test_the_checked_host_is_the_host_the_websocket_library_connects_to(host, scheme):
    from urllib.parse import urlsplit

    url = f"{scheme}://{host}:9/c"
    try:
        plan = connect.plan(reply(url), "https://api.example.test")
    except (ConfigurationError, ChannelProtocolError):
        return  # refused before any socket
    # websockets reads the URL with urllib: it must name the host the check accepted.
    assert (urlsplit(plan.url).hostname or "").strip("[]") == host.strip("[]").lower()


@pytest.mark.parametrize("url", ["ws://[::ffff:127.0.0.1]:9/c", "ws://0x7f.1:9/c", "ws://2130706433:9/c",
                                 "ws://127.0.0.1.nip.io:9/c", "ws://localhost.evil:9/c"])
def test_plain_ws_to_a_name_that_is_not_plainly_loopback_is_refused(url):
    with pytest.raises(ConfigurationError) as caught:
        connect.plan(reply(url), "https://api.example.test")
    assert caught.value.code == "insecure_channel_origin"


@pytest.mark.parametrize("url", ["ws://bücher.example/c", "wss://bücher.example/c"])
def test_a_host_the_two_url_parsers_read_differently_is_refused(url):
    with pytest.raises((ConfigurationError, ChannelProtocolError)):
        connect.plan(reply(url), "https://api.example.test")


# -- the port: 1 to 5 ASCII digits naming 1-65535, read from the authority --------------------------


@pytest.mark.parametrize("port", ["0", "00", "00000"])
def test_port_zero_is_refused_with_a_message_that_names_it(port):
    with pytest.raises(ChannelProtocolError, match="port 0"):
        connect.plan(reply(f"ws://127.0.0.1:{port}/c"), "https://api.example.test")
    with pytest.raises(ChannelProtocolError, match="port 0"):
        connect.plan(reply(f"wss://h.example.test:{port}/c"), "https://api.example.test")


@pytest.mark.parametrize("port", ["65536", "99999", "100000", "1" * 30])
def test_a_port_above_65535_is_refused(port):
    with pytest.raises(ChannelProtocolError, match="port"):
        connect.plan(reply(f"wss://h.example.test:{port}/c"), "https://api.example.test")


@pytest.mark.parametrize("port", ["+80", " 80", "80 ", "8_0", "-1", "٨٠", "８０", "0x50", "8 0", "80\n", "", "6.5", "http"])
@pytest.mark.parametrize("host", ["h.example.test", "127.0.0.1", "[::1]"])
def test_a_port_that_is_not_plain_ascii_digits_is_refused(host, port):
    with pytest.raises(ChannelProtocolError):
        connect.plan(reply(f"wss://{host}:{port}/c"), "https://api.example.test")


@pytest.mark.parametrize("url", ["wss://h.example.test:/c", "wss://[::1]:/c", "ws://127.0.0.1:/c"])
def test_an_empty_port_after_the_colon_is_refused(url):
    with pytest.raises(ChannelProtocolError):
        connect.plan(reply(url), "https://api.example.test")


@pytest.mark.parametrize("url", ["wss://h.example.test:1/c", "wss://h.example.test:65535/c", "wss://h.example.test:0080/c",
                                 "ws://[::1]:65535/c", "ws://127.0.0.1:1/c", "wss://h.example.test/c"])
def test_a_port_from_1_to_65535_or_none_is_accepted(url):
    assert connect.plan(reply(url), "https://api.example.test").url == url


# -- the redirect-free sync connect ---------------------------------------------------------------


def test_the_sync_connect_that_follows_no_redirect_overrides_process_redirect():
    from fi.sandbox._channel._sync import stream
    from websockets.sync import client as sync_client

    redirecting = getattr(sync_client, "reconnect", None)
    if redirecting is None:
        pytest.skip("this websockets version has no redirecting sync connect")
    assert stream.NoRedirectConnect.process_redirect is not redirecting.process_redirect


# -- the output scrub drops C1 controls and bidi overrides ----------------------------------------


C1_AND_BIDI = "\u0085\u009b‪‮⁦⁩"


def test_server_text_loses_c1_controls_and_bidi_overrides():
    from fi.sandbox.channel_errors import clean_server_text

    assert clean_server_text(f"ok{C1_AND_BIDI}done") == "okdone"


def test_a_stream_error_and_a_close_reason_lose_c1_controls_and_bidi_overrides():
    error = StreamError("validation", f"bad{C1_AND_BIDI} input", {"note": f"x{C1_AND_BIDI}y"})
    out = connect.stream_refusal(error, scrub=lambda text: text)
    assert not any(ch in str(out) for ch in C1_AND_BIDI)
    assert "xy" in repr(getattr(out, "detail", None)) or "xy" in repr(getattr(out, "payload", None))
    closed = channel_closed(4999, f"gone{C1_AND_BIDI}now")
    assert closed.server_reason == "gonenow"


def test_a_refused_upgrade_payload_and_the_private_scrubber_lose_c1_controls_and_bidi_overrides():
    body = json.dumps({"error": {"code": "x", "message": f"m{C1_AND_BIDI}m"}}).encode()
    out = connect.refusal(400, body, {}, lambda text: text)
    assert not any(ch in str(out) for ch in C1_AND_BIDI)

    class Shared:
        error_scrubber = None

        def origin(self):
            return type("O", (), {"secrets": []})()

    assert connect.scrubber(Shared(), TOKEN)(f"a{C1_AND_BIDI}b") == "ab"


# -- one shared table of channel hosts, the same rows and answers in the Python and TypeScript clients ---------

#: (host as the channel URL writes it, whether plain ws to it is allowed)
CHANNEL_HOST_TABLE = [
    ("127.0.0.1", True), ("127.9.9.9", True), ("[::1]", True), ("[0:0:0:0:0:0:0:1]", True), ("localhost", True),
    ("LOCALHOST", True),
    ("localhost.", False), ("127.0.0.1.", False), ("127.0.0.1.nip.io", False), ("localhost.evil", False),
    ("[::ffff:127.0.0.1]", False), ("0x7f.1", False), ("0x7f.0.0.1", False), ("2130706433", False),
    ("017700000001", False), ("127.1", False), ("127.000.000.001", False), ("localhost%2e", False),
    ("\uff4c\uff4f\uff43\uff41\uff4c\uff48\uff4f\uff53\uff54", False), ("\u24db" + "ocalhost", False),
    ("0.0.0.0", False), ("[::]", False), ("[::127.0.0.1]", False),
]


@pytest.mark.parametrize(("host", "allowed"), CHANNEL_HOST_TABLE)
def test_the_shared_channel_host_table(host, allowed):
    url = f"ws://{host}:9/c"
    if allowed:
        assert connect.plan(reply(url), "https://api.example.test").url == url
    else:
        with pytest.raises((ConfigurationError, ChannelProtocolError)):
            connect.plan(reply(url), "https://api.example.test")


# -- the token is found whatever is mixed into it: controls are dropped before the scrub -----------------

SPLIT_TOKEN = "sct_ABCDEF123456"


@pytest.mark.parametrize("filler", ["\x01", "\x85", "\u202e", "\u2066", "\u200b", "\u200c", "\u200d", "\ufeff", "\x7f"])
def test_a_token_split_by_a_control_character_is_scrubbed(filler):
    from fi.sandbox.channel_errors import clean_server_text

    split = SPLIT_TOKEN[:4] + filler + SPLIT_TOKEN[4:]
    out = clean_server_text(f"see {split} now", lambda text: text.replace(SPLIT_TOKEN, "[token]"))
    assert SPLIT_TOKEN not in out
    assert out == "see [token] now"


def test_a_token_split_at_the_cap_is_scrubbed_before_the_cut():
    from fi.sandbox.channel_errors import clean_server_text

    out = clean_server_text("a" * 190 + SPLIT_TOKEN[:4] + "\x01" + SPLIT_TOKEN[4:], lambda text: text.replace(SPLIT_TOKEN, "[token]"))
    assert out == "a" * 190 + "[token]"


def test_a_close_reason_with_a_split_token_is_scrubbed():
    closed = channel_closed(4999, f"gone {SPLIT_TOKEN[:5]}\x01\u200b{SPLIT_TOKEN[5:]}", lambda text: text.replace(SPLIT_TOKEN, "[token]"))
    assert SPLIT_TOKEN not in closed.server_reason
    assert closed.server_reason == "gone [token]"


def test_the_private_scrubber_finds_a_token_split_by_a_control_character():
    class Shared:
        error_scrubber = None

        def origin(self):
            class Origin:
                secrets = []

            return Origin()

    private = connect.scrubber(Shared(), SPLIT_TOKEN)
    out = private(f"see {SPLIT_TOKEN[:4]}\x01\u200b{SPLIT_TOKEN[4:]} now")
    assert SPLIT_TOKEN not in out
    assert "[" in out and out.startswith("see ") and out.endswith(" now")
