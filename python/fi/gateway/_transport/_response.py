"""Per-exchange header capture and safe body failure diagnostics."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import json
import threading
from typing import Any, Iterator

import httpx

from fi.gateway._gateway_evidence import GatewayEvidence, capture_gateway_evidence


_capture_scope: ContextVar[tuple[Any, bool, ResponseCapture] | None] = ContextVar(
    "gateway_response_capture", default=None,
)
_capture_lock = threading.RLock()
_capture_boundaries: dict[int, _CaptureBoundary] = {}
_MISSING = object()


class _CaptureBoundary:
    """Temporarily observe HTTPX dispatch without replacing the sending client.

    HTTPX's single-exchange boundary returns before response hooks and auth-body
    consumers, even for transports that do not emit httpcore trace events. The
    auth boundary scopes observation to this send, including newly built auth
    requests, but excludes unrelated nested sends made by a caller hook.
    """

    def __init__(self, client: Any, asynchronous: bool) -> None:
        self.client = client
        self.users = 0
        self.auth = client._send_handling_auth
        self.single = client._send_single_request
        self.wrappers = {
            "_send_handling_auth": self._aauth if asynchronous else self._auth,
            "_send_single_request": self._asingle if asynchronous else self._single,
        }
        self.originals = {name: vars(client).get(name, _MISSING) for name in self.wrappers}
        for name, wrapper in self.wrappers.items():
            setattr(client, name, wrapper)

    @contextmanager
    def _auth_scope(self) -> Iterator[None]:
        scope = _capture_scope.get()
        # Activate the pending send, not a particular Request: a caller's send
        # override or auth flow can rebuild it. Nested sends need their own scope.
        active = ((self.client, False, scope[2]) if scope is not None
                  and scope[0] is self.client and scope[1] else None)
        token = _capture_scope.set(active)
        try:
            yield
        finally:
            _capture_scope.reset(token)

    def _auth(self, request: httpx.Request, *args: Any, **kwargs: Any) -> httpx.Response:
        with self._auth_scope():
            return self.auth(request, *args, **kwargs)

    async def _aauth(self, request: httpx.Request, *args: Any, **kwargs: Any) -> httpx.Response:
        with self._auth_scope():
            return await self.auth(request, *args, **kwargs)

    def _begin(self, request: httpx.Request) -> ResponseCapture | None:
        scope = _capture_scope.get()
        if scope is not None and scope[0] is self.client and not scope[1]:
            capture = scope[2]
            capture.reset()
            capture.requests.append(request)
            return capture
        return None

    def _single(self, request: httpx.Request) -> httpx.Response:
        capture = self._begin(request)
        response = self.single(request)
        if capture is not None:
            capture.capture(response)
        return response

    async def _asingle(self, request: httpx.Request) -> httpx.Response:
        capture = self._begin(request)
        response = await self.single(request)
        if capture is not None:
            capture.capture(response)
        return response

    def restore(self) -> None:
        for name, wrapper in self.wrappers.items():
            # Do not overwrite an owner's concurrent replacement of a method.
            if vars(self.client).get(name) is wrapper:
                original = self.originals[name]
                if original is _MISSING:
                    delattr(self.client, name)
                else:
                    setattr(self.client, name, original)


class ResponseCapture:
    """Keep evidence from only the latest exchange in one SDK attempt.

    The original client's send method, state, transports and hook lists are used
    as given. Dispatch observers are reference-counted across concurrent sends;
    ContextVar scopes keep captures separate across threads, tasks and nested
    calls. Only installation/restoration takes the lock, never network I/O.
    """

    def __init__(self) -> None:
        # Keep exchange handles until the whole send returns: auth may reuse a
        # request, or fail after a challenge whose response never reaches callers.
        self.requests: list[httpx.Request] = []
        self.responses: list[httpx.Response] = []
        self.reset()

    def reset(self) -> None:
        self.response: httpx.Response | None = None
        self.evidence = GatewayEvidence()
        self.status: int | None = None

    def capture(self, response: httpx.Response) -> None:
        if self.response is response:
            return
        self.response = response
        self.responses.append(response)
        self.evidence = capture_gateway_evidence(response)
        self.status = response.status_code

    def scrub(self, composed_names: frozenset[str]) -> None:
        """Mask every captured exchange only after auth has finished sending."""
        from fi.gateway._transport._scrub import scrub_sent_request

        for request in self.requests:
            scrub_sent_request(request, None, None, composed_names)
        for response in self.responses:
            scrub_sent_request(None, response, None, composed_names)

    @contextmanager
    def client(
        self, client: Any, *, asynchronous: bool = False,
    ) -> Iterator[Any]:
        with _capture_lock:
            boundary = _capture_boundaries.get(id(client))
            if boundary is None:
                boundary = _CaptureBoundary(client, asynchronous)
                _capture_boundaries[id(client)] = boundary
            boundary.users += 1
        token = _capture_scope.set((client, True, self))
        try:
            yield client
        finally:
            _capture_scope.reset(token)
            with _capture_lock:
                boundary.users -= 1
                if boundary.users == 0:
                    boundary.restore()
                    del _capture_boundaries[id(client)]


def safe_response(response: httpx.Response) -> httpx.Response:
    """Retain the published response identity after the send boundary scrub.

    Credential and client-composed header values were masked in place when the
    exchange finished. Keep its captured evidence, headers and original request
    rather than replacing the response with a request-free diagnostic snapshot.
    """
    capture_gateway_evidence(response)
    return response


def body_decode_error(error: Exception, evidence: GatewayEvidence) -> Exception:
    """Preserve the public decode family without HTTPX's authenticated request."""
    from fi.gateway._retry_policy import _UNKNOWN_DISPATCH_REMEDY

    message = ("HTTP request failed." if isinstance(error, httpx.RequestError)
               and not isinstance(error, httpx.DecodingError) else "Response body could not be decoded.")
    if evidence.dispatched == "unknown":
        message += " " + _UNKNOWN_DISPATCH_REMEDY
    if isinstance(error, httpx.RequestError):
        translated: Exception = type(error)(message)
    elif isinstance(error, json.JSONDecodeError):
        translated = json.JSONDecodeError(message, "", 0)
    elif isinstance(error, UnicodeDecodeError):
        translated = UnicodeDecodeError(error.encoding, b"", 0, 0, message)
    else:
        translated = ValueError(message)
    translated.gateway_evidence = evidence  # type: ignore[attr-defined]
    translated.dispatched = evidence.dispatched  # type: ignore[attr-defined]
    translated.gateway_request_id = evidence.gateway_request_id  # type: ignore[attr-defined]
    translated.client_request_id = evidence.client_request_id  # type: ignore[attr-defined]
    return translated


class _StreamCleanup(httpx.SyncByteStream, httpx.AsyncByteStream):
    """SDK-owned stream cleanup must not replace its primary read/decode failure."""

    def __init__(self, stream: Any) -> None:
        self.stream = stream

    def __iter__(self) -> Any:
        yield from self.stream

    async def __aiter__(self) -> Any:
        async for part in self.stream:
            yield part

    def close(self) -> None:
        try:
            self.stream.close()
        except Exception:
            pass

    async def aclose(self) -> None:
        try:
            await self.stream.aclose()
        except Exception:
            pass


def protect_stream_cleanup(response: httpx.Response) -> None:
    response.stream = _StreamCleanup(response.stream)


def close_response(response: httpx.Response | None) -> None:
    if response is not None:
        try:
            response.close()
        except Exception:
            pass


async def aclose_response(response: httpx.Response | None) -> None:
    if response is not None:
        try:
            await response.aclose()
        except Exception:
            pass
