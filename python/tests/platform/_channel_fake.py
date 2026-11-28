"""An in-process fake of the sandbox channel server, written from the channel contract (no network
beyond loopback, no real sandbox).

It speaks what the contract says and nothing the SDK could lean on by accident:

- ``POST <prefix>/workspace/sandboxes/{id}/channel/token`` mints a 60 s, single-use token
  (``sct_`` and 43 base64url characters) and answers 201 with the URL, the transport (subprotocol
  list) and the limits; 403 for a sandbox the caller did not create, 404 for an unknown sandbox
  and for every reply while the operator's switch is off, 409 ``channel_remote_unsupported``;
- ``GET /workspace/sandboxes/{id}/channel`` is the WebSocket upgrade: an allowed ``Origin`` (the
  server's own), no query string, exactly one token and ``omega.channel.v1`` among the
  subprotocols (the token is spent whatever the rest of the checks say), then ``101`` answering
  ``omega.channel.v1`` only, no extension. A cookie or an ``Authorization`` header is ignored and
  recorded;
- one binary message per frame, ``[type u8][stream u32 big-endian][payload <= 64 KiB]``; ``hello``
  on connect; ``exec`` with an argv list; ``started``; raw ``stdout`` and ``stderr``; ``stdin`` and
  ``stdinEof`` (half-close); ``cancel``; ``exit`` as the last frame of a stream; ``error`` frames;
- credits both ways: 256 KiB of output the client has not granted, 32 KiB of stdin the command's
  pipe has not taken; ``window`` frames in both directions. The server stops reading a command's
  pipes without credit;
- close codes 4401, 4404, 4409, 4410, 4411 and 1001, sent by :meth:`FakeChannel.close_sockets`;
  closing a socket stops the commands it holds.

Commands run on this machine (``asyncio`` subprocesses in ``root``), so bytes, exit codes and
signals are real. The wire constants (in ``_channel_streams``) are written out on purpose: they are
the contract's, not imported from the SDK under test.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import secrets
import threading
import time
from http import HTTPStatus
from typing import Any, Optional

from websockets.asyncio.server import serve
from websockets.datastructures import Headers
from websockets.frames import Opcode
from websockets.http11 import Response

from ._channel_streams import (  # noqa: F401 (the names tests import from here)
    BEARER,
    MAX_PAYLOAD,
    MAX_STREAMS,
    OTHER_SBX,
    OUTPUT_WINDOW,
    SBX,
    STDIN_WINDOW,
    SUBPROTOCOL,
    TOKEN_PREFIX,
    Connection,
    error_body,
)


class FakeChannel:
    """The server. ``start()`` listens on loopback; ``url`` is its origin (the API base URL when
    ``api_prefix`` is empty)."""

    def __init__(self, root: Any, *, api_prefix: str = "", sandboxes: tuple = (SBX,),
                 forbidden: tuple = (), enabled: bool = True, remote_unsupported: bool = False,
                 mint_error: Optional[tuple] = None, redirect_to: Optional[str] = None,
                 channel_url: Optional[str] = None) -> None:
        self.root = root
        self.api_prefix = api_prefix
        self.sandboxes, self.forbidden = set(sandboxes), set(forbidden)
        self.enabled, self.remote_unsupported, self.mint_error = enabled, remote_unsupported, mint_error
        #: When set, every upgrade is answered with a 302 to this URL (a server that redirects the handshake).
        self.redirect_to = redirect_to
        #: When set, the mint names this channel URL instead of the server's own.
        self.channel_url = channel_url
        self.tokens: dict[str, tuple[str, float]] = {}
        self.token_ttl = 60.0
        self.info: dict = {}
        self.mints: list[dict] = []
        self.minted: list[dict] = []
        self.upgrades: list[dict] = []
        self.refusals: list[tuple[int, str]] = []
        self.sockets: list[Connection] = []
        self.sent = self.granted = self.max_unreleased = 0
        self.max_stdin_pending = self.flow_errors = 0
        self.live = 0
        #: While True the server does not answer a ping (a server that defers pongs under backpressure).
        self.withhold_pongs = False
        self.tasks: list = []
        self.port = 0
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._ready = threading.Event()
        self._stop: Optional[asyncio.Future] = None
        self._thread: Optional[threading.Thread] = None

    # -- lifecycle ----------------------------------------------------------------------------

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def base_url(self) -> str:
        return self.origin + self.api_prefix

    def start(self) -> "FakeChannel":
        self._thread = threading.Thread(target=lambda: asyncio.run(self._main()), daemon=True)
        self._thread.start()
        assert self._ready.wait(10), "the fake channel server did not start"
        return self

    def stop(self) -> None:
        if self.loop is not None and self._stop is not None:
            self.loop.call_soon_threadsafe(lambda: self._stop.done() or self._stop.set_result(None))
        if self._thread is not None:
            self._thread.join(10)

    def __enter__(self) -> "FakeChannel":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.stop()

    def call(self, coro: Any) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(10)

    def close_sockets(self, code: int, reason: str) -> None:
        """Close every open socket with an application close code, as the contract's table says."""
        async def close() -> None:
            await asyncio.gather(*(c.ws.close(code, reason) for c in list(self.sockets)), return_exceptions=True)

        self.call(close())

    def wait_idle(self, seconds: float = 5.0) -> bool:
        """True once no command is running and no socket is open."""
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self.live == 0 and not self.sockets:
                return True
            time.sleep(0.02)
        return False

    # -- the servers --------------------------------------------------------------------------

    async def _main(self) -> None:
        self.loop = asyncio.get_running_loop()
        self._stop = self.loop.create_future()
        inner = await serve(
            self._socket, "127.0.0.1", 0, subprotocols=[SUBPROTOCOL], compression=None,
            process_request=self._upgrade, max_size=MAX_PAYLOAD + 5,
        )
        inner_port = inner.sockets[0].getsockname()[1]
        front = await asyncio.start_server(lambda r, w: self._front(r, w, inner_port), "127.0.0.1", 0)
        self.port = front.sockets[0].getsockname()[1]
        self._ready.set()
        await self._stop
        front.close()
        inner.close()
        await inner.wait_closed()
        for conn in list(self.sockets):
            for stream in list(conn.streams.values()):
                stream.stop("SIGKILL")
        pending = [t for t in self.tasks if not t.done()]
        if pending:
            await asyncio.wait(pending, timeout=5)

    async def _front(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, inner_port: int) -> None:
        """One port for the HTTP routes (mint, info) and the upgrade (handed to the WebSocket
        server), so the server's origin is one origin."""
        try:
            head = await reader.readuntil(b"\r\n\r\n")
        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError, ConnectionError):
            writer.close()
            return
        line, _, rest = head.partition(b"\r\n")
        method, target, _ = line.decode("latin-1").split(" ", 2)
        headers = {}
        for raw in rest.decode("latin-1").split("\r\n"):
            name, _, value = raw.partition(":")
            if name:
                headers[name.strip().lower()] = value.strip()
        if method == "GET" and "upgrade" in headers.get("connection", "").lower():
            try:
                up_reader, up_writer = await asyncio.open_connection("127.0.0.1", inner_port)
            except OSError:
                writer.close()
                return
            up_writer.write(head)
            await up_writer.drain()

            async def pipe(src: asyncio.StreamReader, dst: asyncio.StreamWriter) -> None:
                try:
                    while chunk := await src.read(65536):
                        dst.write(chunk)
                        await dst.drain()
                except (ConnectionError, OSError):
                    pass
                finally:
                    try:
                        dst.close()
                    except Exception:
                        pass

            await asyncio.gather(pipe(reader, up_writer), pipe(up_reader, writer))
            return
        body = b""
        if int(headers.get("content-length", "0") or 0):
            body = await reader.readexactly(int(headers["content-length"]))
        status, payload = self._http(method, target, headers, body)
        data = json.dumps(payload).encode() if not isinstance(payload, bytes) else payload
        writer.write(
            f"HTTP/1.1 {status} {HTTPStatus(status).phrase}\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(data)}\r\nConnection: close\r\n\r\n".encode() + data)
        try:
            await writer.drain()
        finally:
            writer.close()

    # -- HTTP routes --------------------------------------------------------------------------

    def _http(self, method: str, target: str, headers: dict, body: bytes) -> tuple[int, Any]:
        path = target.split("?", 1)[0]
        if self.api_prefix and path.startswith(self.api_prefix):
            path = path[len(self.api_prefix):]
        parts = [p for p in path.split("/") if p]
        if headers.get("authorization") != f"Bearer {BEARER}":
            return 401, json.loads(error_body("unauthorized", "no valid credential"))
        if len(parts) == 3 and parts[:2] == ["workspace", "sandboxes"] and method == "GET":
            if parts[2] not in self.sandboxes:
                return 404, json.loads(error_body("not_found", "no such sandbox"))
            return 200, {"schemaVersion": "omega-workspace-sandboxes/v1",
                         "sandbox": {"id": parts[2], "state": "active", **self.info}}
        if len(parts) == 5 and parts[:2] == ["workspace", "sandboxes"] and parts[3:] == ["channel", "token"] \
                and method == "POST":
            return self._mint(parts[2], headers, body)
        return 404, json.loads(error_body("not_found", "no such route"))

    def _mint(self, sandbox_id: str, headers: dict, body: bytes) -> tuple[int, Any]:
        self.mints.append({"sandbox": sandbox_id, "headers": headers, "body": body})
        if not self.enabled or sandbox_id not in self.sandboxes:
            return 404, json.loads(error_body("not_found", "not found"))
        if self.mint_error:
            status, code, detail = self.mint_error
            return status, json.loads(error_body(code, f"fixture {code}", **detail))
        if sandbox_id in self.forbidden:
            return 403, json.loads(error_body("role_forbidden", "exec is the creator's alone"))
        if self.remote_unsupported:
            return 409, json.loads(error_body("sandboxes_unavailable", "relay not served",
                                               reason="channel_remote_unsupported"))
        token = "sct_" + base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
        self.tokens[hashlib.sha256(token.encode()).hexdigest()] = (sandbox_id, time.monotonic() + self.token_ttl)
        reply = {"schemaVersion": "omega-workspace-sandboxes/v2", "channel": {
            "token": token, "sandboxId": sandbox_id,
            "url": self.channel_url or f"ws://127.0.0.1:{self.port}/workspace/sandboxes/{sandbox_id}/channel",
            "transport": {"kind": "websocket-subprotocol", "protocols": [SUBPROTOCOL, TOKEN_PREFIX + token]},
            "expiresAt": "2026-11-19T15:00:00.000Z", "ttlSeconds": 60,
            "limits": {"maxPayloadBytes": MAX_PAYLOAD, "outputWindowBytes": OUTPUT_WINDOW,
                       "stdinWindowBytes": STDIN_WINDOW, "maxStreams": MAX_STREAMS}}}
        self.minted.append(reply["channel"])
        return 201, reply

    # -- the upgrade --------------------------------------------------------------------------

    def _refuse(self, status: int, code: str, message: str) -> Response:
        self.refusals.append((status, code))
        body = error_body(code, message)
        return Response(status, HTTPStatus(status).phrase, Headers([
            ("Content-Type", "application/json"), ("Content-Length", str(len(body))), ("Connection", "close"),
        ]), body)

    def _upgrade(self, connection: Any, request: Any) -> Optional[Response]:
        headers = {k.lower(): v for k, v in request.headers.raw_items()}
        self.upgrades.append({"path": request.path, "headers": headers, "raw": request.headers})
        if self.redirect_to is not None:
            return Response(302, "Found", Headers([("Location", self.redirect_to), ("Content-Length", "0"),
                                                   ("Connection", "close")]), b"")
        if not self.enabled:
            return self._refuse(404, "not_found", "not found")
        if headers.get("origin") != self.origin:  # the front door: the server's own origin only
            return self._refuse(403, "origin_forbidden", "origin not allowed")
        if "?" in request.path:
            return self._refuse(400, "validation", "no query string")
        wanted = request.path.split("/")
        if len(wanted) != 5 or wanted[:3] != ["", "workspace", "sandboxes"] or wanted[4] != "channel":
            return self._refuse(404, "not_found", "no such path")
        offered = [p.strip() for p in headers.get("sec-websocket-protocol", "").split(",") if p.strip()]
        tokens = [p[len(TOKEN_PREFIX):] for p in offered if p.startswith(TOKEN_PREFIX)]
        if len(tokens) != 1 or SUBPROTOCOL not in offered:
            return self._refuse(401, "token_invalid", "token invalid")
        entry = self.tokens.pop(hashlib.sha256(tokens[0].encode()).hexdigest(), None)  # spent either way
        if entry is None or entry[0] != wanted[3] or entry[1] < time.monotonic():
            return self._refuse(401, "token_invalid", "token invalid")
        if wanted[3] not in self.sandboxes:
            return self._refuse(404, "not_found", "not found")
        connection.sandbox_id = wanted[3]
        return None

    async def _socket(self, ws: Any) -> None:
        conn = Connection(self, ws, getattr(ws, "sandbox_id", SBX))
        send_frame = ws.protocol.send_frame

        def send(frame: Any) -> None:
            if frame.opcode is Opcode.PONG and self.withhold_pongs:
                return
            send_frame(frame)

        ws.protocol.send_frame = send
        self.sockets.append(conn)
        try:
            await conn.run()
        finally:
            self.sockets.remove(conn)
