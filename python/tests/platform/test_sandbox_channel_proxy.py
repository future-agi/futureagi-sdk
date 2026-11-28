"""Requests to a loopback origin do not use an environment proxy: the channel token mint, every other
platform call and the channel handshake go straight to this machine, so a credential meant for it is not
handed to a proxy because ``HTTP_PROXY`` or ``ALL_PROXY`` is set. The platform transport uses the environment
proxy for a remote host and skips it for a loopback one (tests/platform/test_env_proxy.py); the channel handshake
skips it for a loopback host, ``wss://`` included, and a remote ``wss://`` channel keeps the websockets default."""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import urllib.request

import httpx
import pytest
from fi.sandbox._channel import connect

from ._channel_fake import BEARER
from ._channel_support import (  # noqa: F401
    SBX,
    async_sandbox,
    channel_fixture,
    sync_sandbox,
)

# -- loopback ws:// is not sent through an environment proxy ---------------------------------------

PROXY_ENV = ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy", "HTTPS_PROXY", "https_proxy")


class _Listener:
    """A TCP listener that records every byte it receives without sending a reply."""

    def __init__(self):
        self.received = 0
        self._sock = socket.socket()
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(8)
        self.port = self._sock.getsockname()[1]
        self._open = []
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        while True:
            try:
                conn, _ = self._sock.accept()
            except OSError:
                return
            self._open.append(conn)
            threading.Thread(target=self._read, args=(conn,), daemon=True).start()

    def _read(self, conn):
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    return
                self.received += len(data)
        except OSError:
            return

    def close(self):
        self._sock.close()
        for conn in self._open:
            conn.close()


def _direct_plan(server):
    """A connection plan for the fake server, with the mint made without any proxy."""
    request = urllib.request.Request(
        f"{server.base_url}/workspace/sandboxes/{SBX}/channel/token", data=b"{}", method="POST",
        headers={"Authorization": f"Bearer {BEARER}", "Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request) as response:
        minted = json.loads(response.read())
    return connect.plan(minted, server.base_url)


@pytest.fixture(name="proxy")
def proxy_fixture(monkeypatch):
    listener = _Listener()
    for name in PROXY_ENV:
        monkeypatch.setenv(name, f"http://127.0.0.1:{listener.port}")
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    yield listener
    listener.close()


def test_a_loopback_ws_handshake_does_not_go_through_an_environment_proxy(channel, proxy):
    from fi.sandbox._channel._sync.stream import ExecStream

    stream = ExecStream.open(_direct_plan(channel), ["true"])
    stream.close()
    assert proxy.received == 0
    assert channel.upgrades, "the handshake did not reach the channel server directly"


@pytest.mark.asyncio
async def test_async_a_loopback_ws_handshake_does_not_go_through_an_environment_proxy(channel, proxy):
    from fi.sandbox._channel._async.stream import AsyncExecStream

    stream = await AsyncExecStream.open(await asyncio.to_thread(_direct_plan, channel), ["true"])
    await stream.close()
    assert proxy.received == 0
    assert channel.upgrades, "the handshake did not reach the channel server directly"


# -- the token mint and every other call to a loopback origin skip the environment proxy -------------------


def test_a_loopback_api_mint_and_handshake_do_not_go_through_an_environment_proxy(channel, proxy):
    sbx, core = sync_sandbox(channel)
    try:
        stream = sbx.commands.exec_stream(["true"])
        stream.close()
    finally:
        core.shared.close()
    assert proxy.received == 0
    assert len(channel.mints) == 1 and channel.upgrades, "the mint or the handshake did not reach the server directly"


@pytest.mark.asyncio
async def test_async_a_loopback_api_mint_and_handshake_do_not_go_through_an_environment_proxy(channel, proxy):
    sbx, core = async_sandbox(channel)
    try:
        stream = await sbx.commands.exec_stream(["true"])
        await stream.close()
    finally:
        await core.shared.aclose()
    assert proxy.received == 0
    assert len(channel.mints) == 1 and channel.upgrades, "the mint or the handshake did not reach the server directly"


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "127.9.9.9", "[::1]"])
def test_a_platform_call_to_any_loopback_host_skips_the_proxy(channel, proxy, host):
    _, core = sync_sandbox(channel)
    try:
        try:
            core.shared.http().get(f"http://{host}:{channel.port}/health", timeout=2)
        except httpx.TransportError:
            pass  # the fake server listens on 127.0.0.1 only; what matters is that the proxy saw nothing
    finally:
        core.shared.close()
    assert proxy.received == 0


@pytest.mark.asyncio
async def test_async_a_platform_call_to_a_loopback_host_skips_the_proxy(channel, proxy):
    _, core = async_sandbox(channel)
    try:
        await core.shared.ahttp().get(f"{channel.base_url}/health", timeout=2)
    finally:
        await core.shared.aclose()
    assert proxy.received == 0


# -- the channel handshake to a loopback host skips the proxy whatever the scheme --------------------------


@pytest.mark.parametrize("url", ["wss://127.0.0.1:9/c", "wss://localhost:9/c", "wss://127.9.9.9/c", "wss://[::1]:9/c",
                                 "ws://127.0.0.1:9/c"])
def test_a_loopback_channel_url_connects_without_the_environment_proxy_whatever_the_scheme(url):
    def library_connect(uri, *, proxy=True):  # the shape of websockets 15 and later
        return uri

    assert dict(connect.proxy_options(library_connect, url)) == {"proxy": None}


@pytest.mark.parametrize("url", ["wss://sandbox.example.test/c", "wss://127.0.0.1.nip.io/c", "wss://localhost./c",
                                 "wss://[::ffff:127.0.0.1]/c"])
def test_a_remote_wss_channel_keeps_the_library_proxy_default(url):
    def library_connect(uri, *, proxy=True):
        return uri

    assert dict(connect.proxy_options(library_connect, url)) == {}


def test_a_library_without_a_proxy_option_gets_none():
    def old_connect(uri):  # websockets 14 and earlier read no proxy
        return uri

    assert dict(connect.proxy_options(old_connect, "wss://127.0.0.1:9/c")) == {}
