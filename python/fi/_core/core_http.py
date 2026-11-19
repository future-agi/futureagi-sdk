"""Typed connection errors for the core (generated) namespaces too.

The generated core client sends through an ``httpx.Client``; :class:`MappedClient` and
:class:`AsyncMappedClient` are that client with one change: a failure with no HTTP response
(after the retrying transport's own retries) leaves ``send`` as an error that is **both** the
SDK's (``fi.errors.APIConnectionError``, or ``APITimeoutError`` for a timeout; an
``SDKException``) **and** the exact httpx class it replaces (``httpx.ConnectError``,
``httpx.ReadTimeout`` ...), built once per httpx class by :func:`hybrid_class`. So every existing
``except httpx.ConnectError`` keeps working, while ``except fi.errors.APIConnectionError`` now
works on core and platform namespaces alike.

A 3xx is never followed (httpx's default, which the clients keep) and never parsed as a body:
:func:`check_redirect` raises :class:`~fi.errors.UnexpectedRedirectError` naming the target host
only, the same class a platform call raises (and TypeScript's core calls, built with
``redirect: "manual"``).

Everything else about the clients is unchanged (the transport, auth, timeouts).
"""

from __future__ import annotations

from typing import Any

import httpx

from fi._core.errors import connection_error
from fi.errors import (
    APIConnectionError,
    APITimeoutError,
    FutureAGIAPIError,
    UnexpectedRedirectError,
)

_HYBRIDS: dict[tuple[type, type], type] = {}


class CoreMappedError(Exception):
    """Marks an error this module built, so it is never wrapped twice."""


def hybrid_class(base: type[APIConnectionError], httpx_cls: type[httpx.TransportError]) -> type:
    """``class <base>(<base>, <httpx_cls>)``, built once per pair."""
    key = (base, httpx_cls)
    if key not in _HYBRIDS:
        name = f"{base.__name__}"
        _HYBRIDS[key] = type(
            name, (base, httpx_cls, CoreMappedError), {"__module__": "fi.errors", "__qualname__": name}
        )
    return _HYBRIDS[key]


def map_transport_error(exc: httpx.TransportError) -> APIConnectionError:
    classes = (hybrid_class(APIConnectionError, type(exc)), hybrid_class(APITimeoutError, type(exc)))
    err = connection_error(exc, classes=classes)  # type: ignore[arg-type]
    try:
        err._request = exc.request  # type: ignore[attr-defined]  # httpx's ``.request`` keeps working
    except RuntimeError:
        pass
    return err


class InvalidJSONError(FutureAGIAPIError, ValueError):
    """A success status whose body is not JSON: a ``FutureAGIAPIError`` (``code="invalid_json"``) that
    is also the ``ValueError`` the generated parse raised, so ``except ValueError`` keeps working."""


def invalid_json(response: httpx.Response) -> InvalidJSONError:
    return InvalidJSONError(
        int(response.status_code),
        None,
        code="invalid_json",
        message="the server's response was not JSON",
        request_id=response.headers.get("x-request-id"),
    )


def check_redirect(response: httpx.Response, operation: str) -> None:
    """Raise :class:`~fi.errors.UnexpectedRedirectError` for a 3xx: the target host only, never the URL."""
    if not 300 <= response.status_code < 400:
        return
    # only on a 3xx: importing a client loads no origin code (tests/platform/test_gates.py)
    from fi._core.origins import display_host

    location = response.headers.get("location")
    host = None
    if location:
        try:
            host = display_host(response.request.url.join(location))
        except Exception:
            host = None
    raise UnexpectedRedirectError(
        f"{operation}: the server answered {response.status_code} and the SDK never follows a redirect "
        f"(target host: {host or 'unknown'})",
        status_code=response.status_code,
        target_host=host,
        request_id=response.headers.get("x-request-id"),
        operation=operation,
    )


class MappedClient(httpx.Client):
    def send(self, request: httpx.Request, **kwargs: Any) -> httpx.Response:
        kwargs["follow_redirects"] = False  # last shared client boundary, even for caller overrides
        try:
            return super().send(request, **kwargs)
        except CoreMappedError:  # type: ignore[misc]
            raise
        except httpx.TransportError as exc:
            raise map_transport_error(exc) from exc


class AsyncMappedClient(httpx.AsyncClient):
    async def send(self, request: httpx.Request, **kwargs: Any) -> httpx.Response:
        kwargs["follow_redirects"] = False  # match sync and TypeScript's forced manual mode
        try:
            return await super().send(request, **kwargs)
        except CoreMappedError:  # type: ignore[misc]
            raise
        except httpx.TransportError as exc:
            raise map_transport_error(exc) from exc
