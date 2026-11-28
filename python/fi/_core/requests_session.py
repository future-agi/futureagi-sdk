"""A ``requests`` session that sends a loopback or plain ``http://`` request straight to its host."""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import urljoin, urlsplit

import requests
from requests.adapters import HTTPAdapter
from requests.utils import requote_uri
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

from fi._core.loopback import is_localhost_name, is_loopback_host, localhost_connection
from fi._core.proxy_routing import carries_credentials
from fi.errors import KeyedRedirectRefusedError

_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


def is_redirect_answer(response: Any) -> bool:
    """True for an answer the SDK refuses as a redirect: 301, 302, 303, 307 or 308 with or without ``Location``, and any
    other 3xx status with a non-empty ``Location``."""
    status = response.status_code
    return status in _REDIRECT_STATUSES or (300 <= status < 400 and bool(response.headers.get("Location")))


def _origin(url: str) -> tuple[str, Optional[str], Optional[int]]:
    """``(scheme, host, port)`` of ``url``, the port written or the scheme's default."""
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    return scheme, parts.hostname, parts.port or {"http": 80, "https": 443}.get(scheme)


def _readable_origin(url: str) -> Optional[tuple[str, Optional[str], Optional[int]]]:
    """:func:`_origin` of ``url``, else ``None`` for a URL whose port cannot be read (out of range, not a number)."""
    try:
        return _origin(url)
    except ValueError:
        return None


# The headers a followed redirect to another origin keeps: the ones that describe the body and the client, the four
# Accept headers, and the body's framing that ``requests`` writes. Each carries no credential; another name is dropped.
_OFF_ORIGIN_HEADERS = frozenset({
    "content-type", "content-encoding", "user-agent", "accept", "accept-charset", "accept-encoding", "accept-language",
    "content-length", "transfer-encoding", "connection",
})


def _kept_off_origin(name: Any) -> bool:
    text = (name.decode("latin-1") if isinstance(name, bytes) else str(name)).strip().lower()
    return text in _OFF_ORIGIN_HEADERS


class _LocalhostConnectionMixin:
    """Dials the name ``localhost`` to 127.0.0.1, then ``::1``, without the system resolver. ``host`` (so the ``Host``
    header, the TLS server name and the certificate check) stays as written; another host is dialed as urllib3 does."""

    def _new_conn(self) -> Any:
        if not is_localhost_name(self.host):  # type: ignore[attr-defined]
            return super()._new_conn()  # type: ignore[misc]
        import socket
        import sys

        from urllib3.exceptions import ConnectTimeoutError, NewConnectionError

        try:
            sock = localhost_connection(self.port, self.timeout, self.source_address, self.socket_options)  # type: ignore[attr-defined]
        except socket.timeout as error:
            raise ConnectTimeoutError(
                self, f"Connection to {self.host} timed out. (connect timeout={self.timeout})"  # type: ignore[attr-defined]
            ) from error
        except OSError as error:
            raise NewConnectionError(self, f"Failed to establish a new connection: {error}") from error  # type: ignore[arg-type]
        sys.audit("http.client.connect", self, self.host, self.port)  # type: ignore[attr-defined]
        return sock


class _LocalhostHTTPConnection(_LocalhostConnectionMixin, HTTPConnection):
    pass


class _LocalhostHTTPSConnection(_LocalhostConnectionMixin, HTTPSConnection):
    pass


class _LocalhostHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = _LocalhostHTTPConnection


class _LocalhostHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = _LocalhostHTTPSConnection


class LocalhostAdapter(HTTPAdapter):
    """``requests``' own adapter with connections that dial the name ``localhost`` to 127.0.0.1, then ``::1``."""

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
        super().init_poolmanager(*args, **kwargs)
        self.poolmanager.pool_classes_by_scheme = {
            "http": _LocalhostHTTPConnectionPool, "https": _LocalhostHTTPSConnectionPool,
        }


def session_chain(session: Any) -> list[Any]:
    """The sessions that can send a request made with ``session.request``, outermost first. A ``FuturesSession`` with the
    ``request`` of ``requests_futures`` hands each request to the session it holds in ``session`` (when it holds one), so
    that session stands in its place. A session with the ``request`` of ``requests.Session`` sends through itself, whatever
    its ``session`` attribute holds. Any other ``request`` can send through the object or through the session it holds, so
    both are in the chain."""
    from requests_futures.sessions import FuturesSession

    first = session
    chain: list[Any] = []
    seen: set[int] = set()
    while session is not None and id(session) not in seen and len(chain) < 16:
        seen.add(id(session))
        request = getattr(type(session), "request", None)
        held = getattr(session, "session", None)
        if isinstance(session, FuturesSession) and request is FuturesSession.request and held:
            session = held
            continue
        chain.append(session)
        if request is requests.Session.request or request is FuturesSession.request:
            break
        session = held
    return chain or ([first] if first is not None else [])


def sending_chain(session: Any) -> Optional[list[Any]]:
    """:func:`session_chain` for judging the proxies of a send, or ``None`` when the hand-over comes back to a session
    already seen or goes deeper than 16 sessions (fail closed). A ``requests.Session`` that sends through itself ends
    the walk, whatever its ``session`` attribute holds."""
    from requests_futures.sessions import FuturesSession

    chain: list[Any] = []
    seen: set[int] = set()
    while session is not None:
        if id(session) in seen or len(seen) >= 16:
            return None
        seen.add(id(session))
        request = getattr(type(session), "request", None)
        held = getattr(session, "session", None)
        if isinstance(session, FuturesSession) and request is FuturesSession.request and held:
            session = held
            continue
        chain.append(session)
        if request is requests.Session.request or request is FuturesSession.request:
            break
        session = held
    return chain


def _runs_code(session: Any) -> bool:
    auth = getattr(session, "auth", None)
    if auth is None or type(auth) is list:
        return False
    # A plain pair of strings reads the same when judged and when sent; a tuple subclass runs its own ``__len__``.
    return not (type(auth) is tuple and len(auth) == 2 and all(type(part) in (str, bytes) for part in auth))


def has_callable_auth(session: Any) -> bool:
    """Whether a session in the chain has an ``auth`` that runs code when a request is sent (a callable, an ``AuthBase``,
    ``HTTPDigestAuth``, a tuple subclass). What such an auth adds can differ from one call to the next, so it is judged as
    a key and run once, for the send; a plain ``(user, password)`` tuple of strings is Basic credentials and is judged
    from the prepared request."""
    return any(_runs_code(each) for each in session_chain(session))


def prepared_headers(session: Any, method: str, url: str, headers: Any = None, *, params: Any = None) -> list[Any]:
    """The headers that go on the wire for a call on ``session``, one set for each session in its chain: the session's own
    headers merged with the call's, then what the session's ``auth`` (a tuple, ``HTTPBasicAuth``, a callable that sets a
    header) and its cookies add, and the ``.netrc`` credentials it reads. The request is prepared without a body, so a file
    or a stream the caller passes is not read; a session whose ``auth`` is a callable is not prepared (see
    :func:`has_callable_auth`). A session that
    cannot prepare the request adds nothing (the send fails the same way, before a byte)."""
    found: list[Any] = []
    for target in session_chain(session):
        if _runs_code(target):
            continue
        try:
            request = requests.Request(method=str(method).upper(), url=url, headers=headers, params=params)
            found.append(target.prepare_request(request).headers)
        except Exception:  # noqa: BLE001 - a request that cannot be prepared is not sent
            continue
    return found


def readable_next(redirects: Any) -> Any:
    """The requests ``resolve_redirects`` yields, ending quietly where a ``Location`` cannot be read (``ValueError``)."""
    try:
        yield from redirects
    except ValueError:
        return


def same_origin_redirect_target(response: Any, first_url: str) -> Optional[str]:
    """The URL a 301, 302, 303, 307 or 308 answer with a ``Location`` points to, read as ``requests`` reads it, when it
    is on the origin (scheme, host and port) of the request it answers and of ``first_url``; else ``None``. A target
    on another origin (another scheme, such as https to http on the same host, another host or another port) is not
    followed, and neither is a chain that has left the first origin and points back to it: it was refused at its
    first hop off the origin."""
    if response.status_code not in _REDIRECT_STATUSES:
        return None
    location = response.headers.get("Location")
    if not location:
        return None
    try:
        location = location.encode("latin1").decode("utf8")
    except (UnicodeError, AttributeError):
        return None
    sent = str(getattr(response, "url", None) or "")
    try:
        if location.startswith("//"):
            location = f"{urlsplit(sent).scheme}:{location}"
        target = requote_uri(location) if urlsplit(location).netloc else urljoin(sent, requote_uri(location))
        previous = urlsplit(str(getattr(response.request, "url", "") or "")).fragment
        if previous and not urlsplit(target).fragment:
            target = f"{target}#{previous}"  # a Location without a fragment keeps the last one, as ``requests`` does
        origins = {_readable_origin(target), _readable_origin(sent), _readable_origin(first_url)}
    except (ValueError, TypeError):
        return None
    if len(origins) != 1 or None in origins:
        return None
    scheme, host, _port = next(iter(origins))
    if scheme not in ("http", "https") or not host:
        return None
    return target


class LoopbackDirectSession(requests.Session):
    """A session whose request to a loopback host (the one rule, :func:`fi._core.loopback.is_loopback_host`) or
    over plain ``http://`` with keys in its headers skips ``HTTP_PROXY`` / ``HTTPS_PROXY`` / ``ALL_PROXY`` and goes
    straight to its host. Any other request to another host keeps the proxies and ``NO_PROXY`` that ``requests`` reads from the
    environment. Certificates, ``.netrc`` and the other environment settings stay in force.

    A request that carries a key or a token is sent with redirects off, whatever the caller asked for, and a 3xx answer
    raises ``KeyedRedirectRefusedError`` (a subclass that reports the answer itself sets ``refuse_redirects`` to False;
    one that sets ``returns_same_origin_redirects`` returns a 301, 302, 303, 307 or 308 to the request's own origin)."""

    refuse_redirects = True
    returns_same_origin_redirects = False
    _fi_localhost_adapter: Optional[LocalhostAdapter] = None

    def get_adapter(self, url: str) -> Any:
        adapter = super().get_adapter(url)
        # The session's own adapter class dials ``localhost`` to the loopback addresses; an adapter a caller mounted
        # is theirs and is used as it is.
        if type(adapter) is HTTPAdapter and is_localhost_name(urlsplit(url).hostname):
            if self._fi_localhost_adapter is None:
                self._fi_localhost_adapter = LocalhostAdapter(
                    max_retries=adapter.max_retries, pool_connections=adapter._pool_connections,
                    pool_maxsize=adapter._pool_maxsize, pool_block=adapter._pool_block,
                )
            return self._fi_localhost_adapter
        return adapter

    def close(self) -> None:
        super().close()
        if self._fi_localhost_adapter is not None:
            self._fi_localhost_adapter.close()

    def rebuild_proxies(self, prepared_request: Any, proxies: Any) -> Any:
        # A ``Location`` whose port cannot be read is refused in ``send``, before a byte: no proxy is looked up for it.
        if _readable_origin(prepared_request.url) is None:
            return {}
        return super().rebuild_proxies(prepared_request, proxies)

    def resolve_redirects(self, response: Any, request: Any, *args: Any, yield_requests: bool = False, **kwargs: Any) -> Any:
        """With redirects off, ``requests`` prepares the next request only to set ``Response.next``. A ``Location`` it
        cannot read (a bracketed IPv4 address, bytes that are not UTF-8) leaves ``next`` unset instead of raising, so
        the 3xx answer reaches ``send`` and is refused there like any other redirect."""
        redirects = super().resolve_redirects(response, request, *args, yield_requests=yield_requests, **kwargs)
        return readable_next(redirects) if yield_requests else redirects

    def rebuild_auth(self, prepared_request: Any, response: Any) -> None:
        """A followed redirect to an origin (scheme, host, port) other than the first request's keeps only
        ``Content-Type``, ``Content-Encoding``, ``User-Agent``, the ``Accept`` headers and the body's framing
        (``Content-Length``, ``Transfer-Encoding``, ``Connection``). Every other header that the caller or the session
        set (a vendor key such as an Arize ``api_key`` or ``x-honeycomb-team``, ``Cookie``, ``Authorization``) stays
        with the first origin; ``.netrc`` credentials for the new host apply as ``requests`` reads them, except on a
        session whose ``auth`` skips netrc (the Future AGI exporters' sessions), which reads ``.netrc`` on no hop. On a
        redirect that stays on the first origin the SDK removes no header; ``requests`` itself rebuilds ``Cookie`` and
        ``Proxy-Authorization`` and can drop the body's headers. A ``Location`` whose port cannot be read is refused
        when the redirect is sent: ``KeyedRedirectRefusedError``."""
        first = getattr(response.request, "_fi_first_origin", None) or _origin(response.request.url)
        prepared_request._fi_first_origin = first
        target = _readable_origin(prepared_request.url)
        if target != first:
            headers = prepared_request.headers
            for name in [name for name in headers if not _kept_off_origin(name)]:
                del headers[name]
        if target is None:
            prepared_request._fi_unreadable_location = response.status_code
            return
        if getattr(self.auth, "skips_netrc", False) is True:
            return
        super().rebuild_auth(prepared_request, response)

    def send(self, request: Any, **kwargs: Any) -> Any:
        refused = getattr(request, "_fi_unreadable_location", None)
        if refused is not None:
            raise KeyedRedirectRefusedError(
                "A redirect named a Location whose port cannot be read; it was not followed.", status_code=refused
            )
        keyed = carries_credentials(request.headers)
        if keyed:
            kwargs["allow_redirects"] = False
        parts = urlsplit(request.url)
        if is_loopback_host(parts.hostname or "") or (
            parts.scheme.lower() == "http" and keyed
        ):
            kwargs["proxies"] = {}
        response = super().send(request, **kwargs)
        if keyed and self.refuse_redirects and is_redirect_answer(response):
            # A session that returns a redirect on the request's own origin leaves following it to its caller
            # (``HttpClient.request``), which judges the next hop as any request.
            if not (self.returns_same_origin_redirects and same_origin_redirect_target(response, request.url)):
                response.close()
                raise KeyedRedirectRefusedError(status_code=response.status_code)
        return response
