"""Listeners, the resolver replacement and the fixtures shared by the localhost dialing tests."""

from __future__ import annotations

import contextlib
import os
import socket
import socketserver
import threading
from typing import Any, Iterator, Optional
from unittest import mock

import pytest

KEY = "FIMARKERKEY-7f3a91c2"
SECRET = "FIMARKERSECRET-5d08be44"
MARKERS = (KEY.encode(), SECRET.encode())
RESOLVER_ANSWER = "203.0.113.9"  # a routable test address: nothing is ever sent to it
LOOPBACK_ADDRESSES = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}
PROXY_ENV = ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy",
             "GRPC_PROXY", "grpc_proxy", "FI_ALLOW_INSECURE_HTTP")


class Sink:
    """A loopback listener that keeps what it receives; a proxy sink answers a CONNECT with a refusal."""

    def __init__(self, family: int = socket.AF_INET, proxy: bool = False) -> None:
        sink = self
        self.connections = 0
        self.received: list[bytes] = []

        class Handler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                sink.connections += 1
                self.request.settimeout(0.5)
                try:
                    data = self.request.recv(65536)
                    sink.received.append(data)
                    if proxy:
                        self.request.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
                except OSError:
                    pass

        class Server(socketserver.ThreadingTCPServer):
            address_family = family
            allow_reuse_address = True
            daemon_threads = True

        self.server = Server(("::1" if family == socket.AF_INET6 else "127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    @property
    def raw(self) -> bytes:
        return b"".join(self.received)

    @property
    def marker_bytes(self) -> int:
        return sum(self.raw.count(m) for m in MARKERS)

    @property
    def first_lines(self) -> list[bytes]:
        return [chunk.split(b"\r\n", 1)[0] for chunk in self.received if chunk]

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@contextlib.contextmanager
def resolver_shim(environ: Optional[dict] = None) -> Iterator[list[str]]:
    """Answer ``localhost`` (and any name that holds it) with a test address and ``loop.test`` with 127.0.0.1; record
    every address a socket connects to and redirect the test address to this machine."""
    connects: list[str] = []
    real_getaddrinfo, real_connect = socket.getaddrinfo, socket.socket.connect

    def getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        name = host.decode() if isinstance(host, bytes) else host
        if isinstance(name, str) and "localhost" in name.lower():
            name = RESOLVER_ANSWER
        elif name == "loop.test":
            name = "127.0.0.1"
        return real_getaddrinfo(name, *args, **kwargs)

    def connect(self: socket.socket, address: Any) -> Any:
        if isinstance(address, tuple):
            connects.append(str(address[0]))
            if address[0] == RESOLVER_ANSWER:
                address = ("127.0.0.1", *address[1:])
        return real_connect(self, address)

    base = {k: v for k, v in os.environ.items() if k not in PROXY_ENV}
    with mock.patch.dict(os.environ, {**base, **(environ or {})}, clear=True), \
            mock.patch("socket.getaddrinfo", getaddrinfo), mock.patch.object(socket.socket, "connect", connect):
        yield connects


@pytest.fixture()
def target() -> Iterator[Sink]:
    sink = Sink()
    yield sink
    sink.close()


@pytest.fixture()
def proxy() -> Iterator[Sink]:
    sink = Sink(proxy=True)
    yield sink
    sink.close()
