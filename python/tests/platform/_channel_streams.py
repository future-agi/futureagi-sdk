"""The fake channel server's wire constants, frame helpers and per-socket machinery: the exec
stream (a local process with credit-based output and stdin) and the connection that dispatches
frames. The values are the channel contract's, written out here on purpose (not imported from the
SDK under test). ``_channel_fake`` holds the server that accepts the sockets."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import signal
import struct
import time
from typing import Any, Optional

import websockets

# Frame types (channel contract).
HELLO, EXEC, STARTED, STDIN, STDIN_EOF = 0x80, 0x01, 0x86, 0x02, 0x03
STDOUT, STDERR, EXIT, CANCEL = 0x81, 0x82, 0x83, 0x05
WINDOW_IN, WINDOW_OUT, ERROR = 0x04, 0x85, 0x84  # client grants output / server grants stdin
MAX_PAYLOAD = 65536
OUTPUT_WINDOW = 262144
STDIN_WINDOW = 32768
MAX_STREAMS = 8
SUBPROTOCOL = "omega.channel.v1"
TOKEN_PREFIX = "omega.token."
BEARER = "fake-bearer-token-0003"
SBX = "sbx_" + "a" * 24
OTHER_SBX = "sbx_" + "c" * 24


def frame(kind: int, stream: int, payload: bytes = b"") -> bytes:
    return struct.pack(">BI", kind, stream) + payload


def parse(message: bytes) -> tuple[int, int, bytes]:
    return message[0], struct.unpack(">I", message[1:5])[0], message[5:]


def error_body(code: str, message: str, **detail: Any) -> bytes:
    error: dict = {"code": code, "message": message}
    if detail:
        error["detail"] = detail
    return json.dumps({"schemaVersion": "omega-workspace-sandboxes/v2", "error": error}).encode()


class Stream:
    """One exec stream: a local process, the output credit and the stdin accounting."""

    def __init__(self, owner: "Connection", sid: int) -> None:
        self.owner, self.sid = owner, sid
        self.credit = OUTPUT_WINDOW
        self.event = asyncio.Event()
        self.stdin_pending = 0
        self.queue: asyncio.Queue = asyncio.Queue()
        self.proc: Optional[asyncio.subprocess.Process] = None
        self.cancelled = False
        self.timed_out = False
        self.sent_signal: Optional[str] = None
        self.bytes_out = {STDOUT: 0, STDERR: 0}
        self.task: Optional[asyncio.Task] = None
        self.stopped = False

    async def reserve(self) -> int:
        while self.credit <= 0:
            self.event.clear()
            await self.event.wait()
        n = min(self.credit, MAX_PAYLOAD)
        self.credit -= n
        return n

    def grant(self, n: int) -> None:
        self.credit += n
        self.owner.server.granted += n
        self.event.set()

    async def pump(self, reader: asyncio.StreamReader, kind: int) -> None:
        server = self.owner.server
        while True:
            n = await self.reserve()
            data = await reader.read(n)
            if n != len(data):
                self.credit += n - len(data)
                self.event.set()
            if not data:
                return
            server.sent += len(data)
            server.max_unreleased = max(server.max_unreleased, server.sent - server.granted)
            self.bytes_out[kind] += len(data)
            await self.owner.send(frame(kind, self.sid, data))

    async def feed(self) -> None:
        assert self.proc is not None and self.proc.stdin is not None
        stdin = self.proc.stdin
        try:
            while True:
                data = await self.queue.get()
                if data is None:
                    break
                stdin.write(data)
                await stdin.drain()
                self.stdin_pending -= len(data)
                await self.owner.send(frame(WINDOW_OUT, self.sid, struct.pack(">I", len(data))))
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            try:
                stdin.close()
            except Exception:
                pass

    def _signal(self, number: int) -> None:
        """The signal goes to the command's whole process group, so children end with it."""
        try:
            os.killpg(self.proc.pid, number)
        except ProcessLookupError:
            pass

    def stop(self, name: str = "SIGTERM") -> None:
        if self.proc is not None and self.proc.returncode is None and not self.stopped:
            self.stopped = True
            self.sent_signal = name
            self._signal(getattr(signal, name))

            async def escalate() -> None:
                await asyncio.sleep(1.0)
                if self.proc is not None and self.proc.returncode is None:
                    self._signal(signal.SIGKILL)

            asyncio.ensure_future(escalate())

    async def run(self, spec: dict) -> None:
        server, started = self.owner.server, time.monotonic()
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(server.root), **(spec.get("env") or {})}
        cwd = server.root / spec["cwd"] if spec.get("cwd") else server.root
        try:
            self.proc = await asyncio.create_subprocess_exec(
                *spec["argv"], cwd=str(cwd), env=env,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
        except OSError as problem:
            await self.owner.send(frame(EXIT, self.sid, json.dumps({
                "exitCode": None, "timedOut": False, "cancelled": False, "durationMs": 0,
                "stdoutBytes": 0, "stderrBytes": 0, "error": f"spawn failed: {problem}"}).encode()))
            self.owner.streams.pop(self.sid, None)
            return
        server.live += 1
        await self.owner.send(frame(STARTED, self.sid, json.dumps({
            "execId": "exec_" + secrets.token_hex(12), "outputWindowBytes": OUTPUT_WINDOW,
            "stdinWindowBytes": STDIN_WINDOW}).encode()))
        limit = spec.get("timeoutSeconds")

        async def deadline() -> None:
            await asyncio.sleep(limit)
            self.timed_out = True
            self.stop("SIGTERM")

        timer = asyncio.ensure_future(deadline()) if limit else None
        feeder = asyncio.ensure_future(self.feed())
        try:
            await asyncio.gather(self.pump(self.proc.stdout, STDOUT), self.pump(self.proc.stderr, STDERR))
            await self.proc.wait()
        finally:
            server.live -= 1
            if timer:
                timer.cancel()
            feeder.cancel()
            if self.proc.returncode is None:
                self._signal(signal.SIGKILL)
        code = self.proc.returncode
        body: dict = {
            "exitCode": code if code is not None and code >= 0 else None,
            "timedOut": self.timed_out, "cancelled": self.cancelled,
            "durationMs": int((time.monotonic() - started) * 1000),
            "stdoutBytes": self.bytes_out[STDOUT], "stderrBytes": self.bytes_out[STDERR],
        }
        if code is not None and code < 0:
            body["signal"] = signal.Signals(-code).name
        elif self.sent_signal:
            body["signal"] = self.sent_signal
        self.owner.streams.pop(self.sid, None)
        await self.owner.send(frame(EXIT, self.sid, json.dumps(body).encode()))


class Connection:
    def __init__(self, server: Any, ws: Any, sandbox_id: str) -> None:
        self.server, self.ws, self.sandbox_id = server, ws, sandbox_id
        self.streams: dict[int, Stream] = {}

    async def send(self, data: bytes) -> None:
        try:
            await self.ws.send(data)
        except websockets.ConnectionClosed:
            pass

    async def error(self, sid: int, code: str, message: str, **detail: Any) -> None:
        body: dict = {"code": code, "message": message}
        if detail:
            body["detail"] = detail
        await self.send(frame(ERROR, sid, json.dumps(body).encode()))

    def valid_exec(self, spec: Any) -> Optional[str]:
        if not isinstance(spec, dict) or not set(spec) <= {"argv", "cwd", "env", "timeoutSeconds"}:
            return "exec takes argv, cwd, env and timeoutSeconds only"
        argv = spec.get("argv")
        if not isinstance(argv, list) or not 1 <= len(argv) <= 512 or not all(isinstance(a, str) for a in argv):
            return "argv must be 1 to 512 strings"
        if any("\x00" in a for a in argv) or not argv[0] or argv[0].startswith("-"):
            return "argv[0] must be a program name; no NUL"
        return None

    async def handle(self, message: bytes) -> bool:
        """One frame; False closes the socket (already done)."""
        kind, sid, payload = parse(message)
        if len(payload) > MAX_PAYLOAD:
            await self.ws.close(1009, "message too large")
            return False
        if kind == EXEC:
            if sid == 0:
                await self.error(0, "validation", "a stream id is not zero")
                return True
            if sid in self.streams:
                await self.error(sid, "conflict", "stream in use", reason="stream_in_use")
                return True
            try:
                spec = json.loads(payload)
            except ValueError:
                spec = None
            problem = self.valid_exec(spec)
            if problem:
                await self.error(sid, "validation", problem)
                return True
            if len(self.streams) >= MAX_STREAMS:
                await self.error(sid, "rate_limited", "too many streams")
                return True
            stream = self.streams[sid] = Stream(self, sid)
            stream.task = asyncio.ensure_future(stream.run(spec))
            self.server.tasks.append(stream.task)
            return True
        stream = self.streams.get(sid)
        if kind in (STDIN, STDIN_EOF, CANCEL, WINDOW_IN) and stream is None:
            return True  # a stream that is not open: ignored
        if kind == STDIN:
            stream.stdin_pending += len(payload)
            self.server.max_stdin_pending = max(self.server.max_stdin_pending, stream.stdin_pending)
            if stream.stdin_pending > STDIN_WINDOW:
                self.server.flow_errors += 1
                await self.error(sid, "validation", "stdin past the window", reason="flow_control")
                stream.stop()
                return True
            stream.queue.put_nowait(payload)
        elif kind == STDIN_EOF:
            stream.queue.put_nowait(None)
        elif kind == CANCEL:
            stream.cancelled = True
            stream.stop("SIGTERM")
        elif kind == WINDOW_IN:
            if len(payload) == 4:
                stream.grant(struct.unpack(">I", payload)[0])
        else:
            await self.error(sid, "validation", f"unknown frame type {kind:#x}")
        return True

    async def run(self) -> None:
        await self.send(frame(HELLO, 0, json.dumps({
            "protocol": SUBPROTOCOL, "sandboxId": self.sandbox_id, "maxPayloadBytes": MAX_PAYLOAD,
            "outputWindowBytes": OUTPUT_WINDOW, "stdinWindowBytes": STDIN_WINDOW, "maxStreams": MAX_STREAMS,
        }).encode()))
        try:
            async for message in self.ws:
                if isinstance(message, str):
                    await self.ws.close(1003, "text message")
                    return
                if len(message) < 5:
                    await self.ws.close(1002, "short frame")
                    return
                if not await self.handle(message):
                    return
        except websockets.ConnectionClosed:
            pass
        finally:
            for stream in list(self.streams.values()):
                stream.cancelled = True
                stream.stop("SIGKILL")
