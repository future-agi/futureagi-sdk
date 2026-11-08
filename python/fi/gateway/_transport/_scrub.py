"""Remove credentials from retained HTTPX requests after a send has finished."""
from __future__ import annotations

import builtins

import httpx

from fi.gateway._constants import CREDENTIAL_HEADER_NAMES
from fi.gateway.callbacks.base import REDACTED

_EXCEPTION_GROUP = getattr(builtins, "BaseExceptionGroup", ())


def scrub_sent_request(
    request: httpx.Request | None,
    response: httpx.Response | None,
    error: BaseException | None,
    composed_names: frozenset[str] = frozenset(),
) -> None:
    """Mask credential and client-composed names on retained exchange headers.

    Run in the send's finally, not in an HTTPX hook: an authentication flow may
    resend the same request before send returns. Retries build a fresh request.
    Follow only HTTPX response links and standard exception chains/groups, not
    arbitrary diagnostic object graphs. Aliases then observe the same scrubbed
    Headers object without copying exceptions or touching caller header dicts.
    """
    names = CREDENTIAL_HEADER_NAMES | composed_names
    pending = [request, response, error]
    seen: set[int] = set()
    while pending:
        value = pending.pop()
        if value is None or id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, (httpx.Request, httpx.Response)):
            for name in names:
                if name in value.headers:
                    value.headers[name] = REDACTED
            if isinstance(value, httpx.Response):
                # _request can be None on synthetic responses not bound to a send.
                pending.extend((value._request, value.next_request, *value.history))
        elif isinstance(value, (list, tuple)):
            pending.extend(value)
        elif isinstance(value, dict):
            pending.extend(value)
            pending.extend(value.values())
        elif isinstance(value, BaseException):
            pending.extend((value.args, value.__cause__, value.__context__))
            if isinstance(value, httpx.HTTPError):
                try:
                    pending.append(value.request)
                except RuntimeError:
                    pass  # HTTPX permits errors without an attached request.
                pending.append(getattr(value, "response", None))
            if isinstance(value, _EXCEPTION_GROUP):
                pending.extend(value.exceptions)
