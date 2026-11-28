"""Server text, the channel URL's port and the loopback host rule.

Every format or control character (Unicode Cc and Cf), the combining grapheme joiner, the variation selectors and
the line and paragraph separators are dropped before a token is looked for, so none of them can hide a token. A
channel URL with a port above 65535 is refused, as the TypeScript client refuses it. The loopback host rule is the
one table both clients share (tests/fixtures/loopback/hosts.json). The blocking WebSocket connect refuses to run
without its redirect hook rather than follow a redirect with the token.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fi._core.loopback import is_loopback_host
from fi.sandbox._channel import connect
from fi.sandbox.channel_errors import (
    ChannelProtocolError,
    channel_closed,
    clean_server_text,
)

from .test_sandbox_channel_hardening import reply

SPLIT_TOKEN = "sct_ABCDEF123456"
HOSTS = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "loopback" / "hosts.json"

#: Format characters (Cf), marks, separators, and two C0/C1 controls for contrast.
HIDING = [
    "\u2060", "\u00ad", "\u200e", "\u200f", "\u061c", "\u034f", "\ufe0f", "\U000e0041", "\u180e", "\u2062", "\ufff9",
    "\ufe00", "\U000e0001", "\u2028", "\u2029", "\x01", "\x85", "\u0890", "\U00013439", "\ud800", "\udfff",
]


def _scrub(text: str) -> str:
    return text.replace(SPLIT_TOKEN, "[token]")


@pytest.mark.parametrize("filler", HIDING, ids=lambda ch: f"U+{ord(ch):04X}")
def test_a_token_split_by_a_format_character_or_separator_is_scrubbed(filler):
    split = SPLIT_TOKEN[:4] + filler + SPLIT_TOKEN[4:]
    assert clean_server_text(f"see {split} now", _scrub) == "see [token] now"


@pytest.mark.parametrize("filler", HIDING, ids=lambda ch: f"U+{ord(ch):04X}")
def test_a_close_reason_and_the_private_scrubber_find_the_split_token(filler):
    split = SPLIT_TOKEN[:5] + filler + SPLIT_TOKEN[5:]
    assert channel_closed(4999, f"gone {split}", _scrub).server_reason == "gone [token]"

    class Shared:
        error_scrubber = None

        def origin(self):
            return type("O", (), {"secrets": []})()

    out = connect.scrubber(Shared(), SPLIT_TOKEN)(f"see {split} now")
    assert SPLIT_TOKEN not in out and filler not in out


def test_text_without_them_is_unchanged():
    assert clean_server_text("plain text, ünïcödé and 漢字 stay", _scrub) == "plain text, ünïcödé and 漢字 stay"


@pytest.mark.parametrize("port", ["65536", "70000", "99999", "123456"])
def test_a_channel_url_with_a_port_above_65535_is_refused(port):
    with pytest.raises(ChannelProtocolError):
        connect.plan(reply(f"ws://localhost:{port}/c"), "https://api.example.test")
    with pytest.raises(ChannelProtocolError):
        connect.plan(reply(f"wss://channel.example.test:{port}/c"), "https://api.example.test")


@pytest.mark.parametrize("port", ["1", "443", "65535"])
def test_a_channel_url_with_a_port_in_range_is_accepted(port):
    url = f"ws://localhost:{port}/c"
    assert connect.plan(reply(url), "https://api.example.test").url == url


@pytest.mark.parametrize("row", json.loads(HOSTS.read_text(encoding="utf-8"))["hosts"], ids=lambda row: row["host"])
def test_the_shared_loopback_host_table(row):
    assert is_loopback_host(row["host"]) is row["loopback"]


def test_the_blocking_connect_refuses_a_redirecting_connect_without_its_redirect_hook():
    from fi.sandbox._channel._sync import stream

    class Plain:
        pass

    class Hooked:
        def process_redirect(self, exc):
            raise exc

    assert stream.no_redirect_class(type("M", (), {})) is None
    assert issubclass(stream.no_redirect_class(type("M", (), {"reconnect": Hooked})), Hooked)
    with pytest.raises(ImportError, match="process_redirect"):
        stream.no_redirect_class(type("M", (), {"reconnect": Plain}))
