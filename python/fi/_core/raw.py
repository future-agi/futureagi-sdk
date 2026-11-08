"""Raw responses: ``client.<ns>.with_raw_response.<method>(...)``.

A plain call returns the wire-shaped data. The same call through ``with_raw_response`` returns a
:class:`RawResponse`: the method's own return value as ``.data``, plus what the response said about
the call (``request_id``, ``idempotency_key``, the rate-limit headers, the replay flag, the raw
headers with secrets redacted). The executor records each call's :class:`CallMeta` into a
context variable that the proxy opens, so namespaces need no raw twin of any method; this works
for sync and async methods alike (a context variable follows ``await``).

Every platform namespace subclasses :class:`Namespace` (sync) or :class:`AsyncNamespace`, which
carry the proxy. A method that streams (it returns an iterator) is not a request/response call,
so ``with_raw_response`` refuses it.
"""

from __future__ import annotations

import contextvars
import functools
import inspect
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar

from fi._core.redact import redact_headers
from fi.errors import ConfigurationError

T = TypeVar("T")
_RATE_LIMIT_PREFIXES = ("x-ratelimit-", "ratelimit-", "retry-after")
_capture: contextvars.ContextVar[Optional[list["CallMeta"]]] = contextvars.ContextVar("fi_raw_capture", default=None)


@dataclass(frozen=True)
class CallMeta:
    """What one platform call's final response said, besides its data."""

    status_code: int
    operation: str
    request_id: Optional[str] = None
    upstream_request_id: Optional[str] = None
    receipt_id: Optional[str] = None
    #: The ``Idempotency-Key`` the call sent (minted, or yours).
    idempotency_key: Optional[str] = None
    #: True when the server replayed an earlier response for the same key.
    idempotent_replay: bool = False
    #: True for a not-found-means-applied call whose retry answered 404 (the first attempt applied).
    already_applied: bool = False
    #: HTTP attempts the transport made (1 when nothing was retried), plus "in progress" resends.
    attempts: int = 1
    #: The response headers, with secret values redacted.
    headers: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def rate_limit(self) -> dict[str, str]:
        """The rate-limit headers (``x-ratelimit-*``, ``ratelimit-*``, ``retry-after``)."""
        return {k: v for k, v in self.headers.items() if k.startswith(_RATE_LIMIT_PREFIXES)}


def meta_from(
    response: Any, operation: str, *, idempotency_key: Optional[str], attempts: int, replay: bool, applied: bool = False
) -> CallMeta:
    headers = response.headers
    return CallMeta(
        status_code=int(response.status_code),
        operation=operation,
        request_id=headers.get("x-request-id"),
        upstream_request_id=headers.get("x-upstream-request-id"),
        receipt_id=headers.get("x-omega-receipt-id"),
        idempotency_key=idempotency_key,
        idempotent_replay=replay,
        already_applied=applied,
        attempts=attempts,
        headers=redact_headers(headers.multi_items() if hasattr(headers, "multi_items") else headers),
    )


def record(meta: CallMeta) -> None:
    """Called by the executor for every finished call; a no-op outside ``with_raw_response``."""
    sink = _capture.get()
    if sink is not None:
        sink.append(meta)


@dataclass(frozen=True)
class RawResponse(Generic[T]):
    """A method's return value plus its final response's metadata."""

    data: T
    meta: CallMeta

    @property
    def status_code(self) -> int:
        return self.meta.status_code

    @property
    def request_id(self) -> Optional[str]:
        return self.meta.request_id

    @property
    def idempotency_key(self) -> Optional[str]:
        return self.meta.idempotency_key

    @property
    def headers(self) -> dict[str, str]:
        return self.meta.headers

    @property
    def rate_limit(self) -> dict[str, str]:
        return self.meta.rate_limit

    def parse(self) -> T:
        """The data (the name other SDKs use)."""
        return self.data


def _finish(name: str, result: Any, sink: list[CallMeta]) -> RawResponse[Any]:
    if inspect.isgenerator(result) or inspect.isasyncgen(result) or not sink:
        raise ConfigurationError(
            f"{name} is not a single request/response call, so with_raw_response cannot wrap it", code="not_a_raw_call"
        )
    return RawResponse(result, sink[-1])


class _RawProxy:
    """``namespace.with_raw_response``: the same methods, returning :class:`RawResponse`."""

    def __init__(self, target: Any) -> None:
        self._target = target

    def __getattr__(self, name: str) -> Any:
        method = getattr(self._target, name)
        if not callable(method) or name.startswith("_"):
            raise AttributeError(f"with_raw_response has no method {name!r}")
        if inspect.iscoroutinefunction(method):

            @functools.wraps(method)
            async def arun(*args: Any, **kwargs: Any) -> RawResponse[Any]:
                sink: list[CallMeta] = []
                token = _capture.set(sink)
                try:
                    result = await method(*args, **kwargs)
                finally:
                    _capture.reset(token)
                return _finish(name, result, sink)

            return arun

        @functools.wraps(method)
        def run(*args: Any, **kwargs: Any) -> RawResponse[Any]:
            sink: list[CallMeta] = []
            token = _capture.set(sink)
            try:
                result = method(*args, **kwargs)
            finally:
                _capture.reset(token)
            return _finish(name, result, sink)

        return run


class Namespace:
    """The base of every sync platform namespace: holds the client core and the raw proxy."""

    def __init__(self, core: Any) -> None:
        self._core = core

    @property
    def with_raw_response(self) -> Any:
        """The same methods, each returning a :class:`RawResponse` (data plus response metadata)."""
        return _RawProxy(self)


class AsyncNamespace(Namespace):
    """The base of every async platform namespace."""
