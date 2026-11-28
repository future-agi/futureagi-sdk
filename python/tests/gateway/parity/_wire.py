"""Scripted HTTP for the recorder: every httpx request goes to a script.

``Wire.install()`` replaces ``httpx.HTTPTransport.handle_request`` and
``httpx.AsyncHTTPTransport.handle_async_request`` for the duration of a case,
so a client the SDK builds itself and one passed as ``http_client`` are both
captured. Sockets are refused outright (loopback included), so no case can
reach a network even through a path that bypasses httpx.

A reply is a plain dict (JSON-able, shared with the TypeScript recorder):
  {"status": 200, "headers": {...}, "json": <any>}       JSON body
  {"status": 200, "sse": ["<data>", ...]}                 one ``data:`` frame each
  {"status": 200, "raw": ["<chunk>", ...]}                body chunks, verbatim
  {"status": 200, "text": "..."}                          text body
  {"raise": "connect"|"connect_timeout"|"read_timeout"|"write_timeout"|"pool_timeout"|"remote_protocol"}
"""

from __future__ import annotations

import base64
import json
import re
import socket
from collections.abc import AsyncIterator, Iterator
from typing import Any

_RAISE = {
    "connect": "ConnectError",
    "connect_timeout": "ConnectTimeout",
    "read_timeout": "ReadTimeout",
    "write_timeout": "WriteTimeout",
    "pool_timeout": "PoolTimeout",
    "remote_protocol": "RemoteProtocolError",
}
UNSCRIPTED = {"status": 599, "json": {"error": {"message": "unscripted request"}}}
_BOUNDARY = re.compile(rb"boundary=([0-9A-Za-z'()+_,./:=?-]+)")


def _content_type(reply: dict[str, Any]) -> str:
    if "sse" in reply:
        return "text/event-stream"
    if "json" in reply:
        return "application/json"
    return "text/plain; charset=utf-8"


def _body_chunks(reply: dict[str, Any]) -> list[bytes]:
    if "sse" in reply:
        return [f"data: {frame}\n\n".encode() for frame in reply["sse"]]
    if "raw" in reply:
        return [chunk.encode() for chunk in reply["raw"]]
    if "json" in reply:
        return [json.dumps(reply["json"], separators=(",", ":")).encode()]
    if "text" in reply:
        return [reply["text"].encode()] if reply["text"] else []
    return []


def _headers(reply: dict[str, Any]) -> list[tuple[str, str]]:
    headers = dict(reply.get("headers") or {})
    if not any(k.lower() == "content-type" for k in headers) and reply.get(
        "content_type", True
    ):
        headers["content-type"] = _content_type(reply)
    return sorted(headers.items())


def _decode(data: bytes) -> dict[str, Any]:
    try:
        return {"text": data.decode("utf-8")}
    except UnicodeDecodeError:
        return {"base64": base64.b64encode(data).decode("ascii")}


def _multipart(body: bytes, boundary: bytes) -> list[dict[str, Any]]:
    parts = []
    for raw in body.split(b"--" + boundary)[1:]:
        if raw.startswith(b"--"):
            break
        head, _, content = raw.strip(b"\r\n").partition(b"\r\n\r\n")
        headers = []
        for line in head.decode("utf-8", "replace").split("\r\n"):
            name, _, value = line.partition(": ")
            if name:
                headers.append(f"{name.lower()}: {value}")
        headers.sort()
        parts.append({"headers": headers, **_decode(content)})
    return parts


class Wire:
    """Holds the replies for one case and the requests it saw."""

    def __init__(self, httpx_module: Any) -> None:
        self._httpx = httpx_module
        self._defaults = dict(httpx_module.Client().headers)
        self.replies: list[dict[str, Any]] = []
        self.requests: list[dict[str, Any]] = []
        self._saved: list[tuple[Any, str, Any]] = []

    # -- scripting ---------------------------------------------------------
    def script(self, *replies: dict[str, Any]) -> None:
        self.replies.extend(replies)

    def _next(self) -> dict[str, Any]:
        return self.replies.pop(0) if self.replies else UNSCRIPTED

    # -- request normalisation --------------------------------------------
    def _record(self, request: Any) -> None:
        url = request.url
        headers = []
        boundary = None
        for name, value in request.headers.multi_items():
            key = name.lower()
            if key == "content-length":
                continue
            if self._defaults.get(key) == value:
                value = "<httpx default>"
            if key == "content-type":
                found = _BOUNDARY.search(value.encode())
                if found:
                    boundary = found.group(1)
                    value = value.replace(boundary.decode(), "BOUNDARY")
            headers.append([key, value])
        content = request.content
        entry: dict[str, Any] = {
            "method": request.method,
            "scheme": url.scheme,
            "host": url.host,
            "port": url.port,
            "path": url.path,
            "query": sorted([k, v] for k, v in url.params.multi_items()),
            "headers": sorted(headers),
            "timeout": request.extensions.get("timeout"),
        }
        if boundary is not None:
            entry["multipart"] = _multipart(content, boundary)
        elif content:
            try:
                entry["json"] = json.loads(content)
            except ValueError:
                entry["body"] = _decode(content)
        self.requests.append(entry)

    # -- responses -----------------------------------------------------------
    def _raise(self, reply: dict[str, Any], request: Any) -> None:
        exc_cls = getattr(self._httpx, _RAISE[reply["raise"]])
        raise exc_cls(f"scripted {reply['raise']}", request=request)

    def handle(self, request: Any) -> Any:
        request.read()
        self._record(request)
        reply = self._next()
        if "raise" in reply:
            self._raise(reply, request)
        chunks = _body_chunks(reply)

        def body() -> Iterator[bytes]:
            yield from chunks
            if reply.get("drop_after"):
                raise self._httpx.RemoteProtocolError("scripted drop", request=request)

        return self._httpx.Response(
            reply.get("status", 200), headers=_headers(reply), content=body()
        )

    async def handle_async(self, request: Any) -> Any:
        await request.aread()
        self._record(request)
        reply = self._next()
        if "raise" in reply:
            self._raise(reply, request)
        chunks = _body_chunks(reply)

        async def body() -> AsyncIterator[bytes]:
            for chunk in chunks:
                yield chunk
            if reply.get("drop_after"):
                raise self._httpx.RemoteProtocolError("scripted drop", request=request)

        return self._httpx.Response(
            reply.get("status", 200), headers=_headers(reply), content=body()
        )

    # -- install / remove ------------------------------------------------------
    def install(self) -> None:
        wire = self

        def handle_request(_self: Any, request: Any) -> Any:
            return wire.handle(request)

        async def handle_async_request(_self: Any, request: Any) -> Any:
            return await wire.handle_async(request)

        def refuse(*_a: Any, **_k: Any) -> None:
            raise OSError("parity recorder: network access is refused")

        targets = [
            (self._httpx.HTTPTransport, "handle_request", handle_request),
            (
                self._httpx.AsyncHTTPTransport,
                "handle_async_request",
                handle_async_request,
            ),
            (socket.socket, "connect", refuse),
            (socket.socket, "connect_ex", refuse),
            (socket, "create_connection", refuse),
            (socket, "getaddrinfo", refuse),
        ]
        for owner, name, replacement in targets:
            self._saved.append((owner, name, getattr(owner, name)))
            setattr(owner, name, replacement)

    def remove(self) -> None:
        while self._saved:
            owner, name, original = self._saved.pop()
            setattr(owner, name, original)
