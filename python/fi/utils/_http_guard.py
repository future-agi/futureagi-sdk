"""Which requests that carry API keys may be sent over plain ``http://``.

A request carries a key when its final headers (client defaults merged with per-call headers, after
authentication hooks and cookies ran) hold ``X-Api-Key``, ``X-Secret-Key`` or an ``Authorization`` header
with a Bearer or Basic value.

* ``https://`` and requests without a key are left as they are.
* Plain ``http://`` to a loopback host is sent directly, through no proxy.
* Plain ``http://`` to any other host is refused before a connection is made, unless
  ``FI_ALLOW_INSECURE_HTTP=1`` or ``allow_insecure_http=True`` is set. With the opt-in the request is
  sent directly as well.
"""

from __future__ import annotations

import base64
import importlib
import ipaddress
import os
import re
from typing import Any, Callable, Dict, Optional, Tuple

import httpx

INSECURE_HTTP_ENV = "FI_ALLOW_INSECURE_HTTP"
ERROR_CODE = "insecure_http_origin"

_KEY_HEADERS = frozenset({"x-api-key", "x-secret-key"})
_SCHEME = re.compile(r"^([A-Za-z][A-Za-z0-9+.-]*):")
_CONTROL = re.compile(r"[\x00-\x20\x7f]")


def _text(value: Any) -> str:
    return value.decode("latin-1") if isinstance(value, (bytes, bytearray)) else str(value)


def header_name(name: Any) -> str:
    """A header name as compared here: text, trimmed, lower case, with ``_`` read as ``-``."""
    return _text(name).strip().lower().replace("_", "-")


def _items(headers: Any):
    if headers is None:
        return []
    items = getattr(headers, "items", None)
    return list(items()) if callable(items) else list(headers)


def _authorization_holds_key(value: str) -> bool:
    parts = value.split(None, 1)
    scheme = parts[0].lower() if parts else ""
    rest = parts[1].strip() if len(parts) > 1 else ""
    if scheme == "bearer":
        return bool(rest)
    if scheme == "basic":
        try:
            return bool(base64.b64decode(rest + "=" * (-len(rest) % 4)).strip(b":"))
        except Exception:
            return bool(rest)
    return False


def carries_key(headers: Any) -> bool:
    """Whether ``headers`` (a mapping, or ``(name, value)`` pairs; names and values as text or bytes) hold a key."""
    try:
        for name, value in _items(headers):
            key = header_name(name)
            text = _text(value).strip()
            if key in _KEY_HEADERS and text:
                return True
            if key == "authorization" and _authorization_holds_key(text):
                return True
            if key == "cookie" and any(header_name(part.split("=", 1)[0]) in _KEY_HEADERS for part in text.split(";")):
                return True
        return False
    except Exception:
        return True


def is_plain_http(url: Any) -> bool:
    """Whether ``url`` is written with the ``http`` scheme."""
    return _target(url)[0]


def _target(url: Any) -> Tuple[bool, Optional[str]]:
    """``(is_plain_http, host as written)``. The host is ``None`` when the text does not give one readers agree on.

    An authority (host and port) that holds a non-ASCII character is returned as written, without case folding, so
    the caller reads that character: ``str.lower`` turns some of them into ASCII (``\\u212a`` KELVIN SIGN into ``k``),
    and the HTTP libraries map such a host to an ASCII one before they connect."""
    text = str(url).lstrip()
    match = _SCHEME.match(text)
    if match is None or match.group(1).lower() != "http":
        return False, None
    rest = text[match.end():]
    if not rest.startswith("//"):
        return True, None
    authority = re.split(r"[/?#]", rest[2:], maxsplit=1)[0]
    if "\\" in authority or "@" in authority or "%" in authority or _CONTROL.search(authority):
        return True, None
    if not authority.isascii():
        return True, authority
    if authority.startswith("["):
        end = authority.find("]")
        return True, (authority[1:end].lower() if end > 0 else None)
    host = authority.rsplit(":", 1)[0] if ":" in authority else authority
    return True, (host.lower() or None)


def is_loopback_host(host: str) -> bool:
    """``localhost`` or an address in 127.0.0.0/8 or ``::1``, written in ASCII."""
    if not host.isascii():
        return False
    if host == "localhost":
        return True
    try:
        address = ipaddress.ip_address(host)
        return address.is_loopback and getattr(address, "ipv4_mapped", None) is None
    except ValueError:
        return False


_NUMERIC_HOST = re.compile(r"^(0x[0-9a-f]*|[0-9]+)(\.(0x[0-9a-f]*|[0-9]+))*\.?$")


def _ambiguous_host(host: str) -> bool:
    """A host ending in a dot, or written as numbers that are not an IPv4 address in four plain decimal parts
    (``127.1``, ``0x7f.0.0.1``, ``0177.0.0.1``)."""
    if host.endswith("."):
        return True
    if _NUMERIC_HOST.match(host):
        try:
            ipaddress.IPv4Address(host)
        except ValueError:
            return True
    return False


def insecure_http_allowed(allow_insecure_http: Any = None) -> bool:
    """The opt-in: ``allow_insecure_http=True``, else ``FI_ALLOW_INSECURE_HTTP`` set to exactly ``1``.
    An argument that is given and is not ``True`` turns the opt-in off."""
    if allow_insecure_http is not None:
        return allow_insecure_http is True
    return os.environ.get(INSECURE_HTTP_ENV) == "1"


def refuse(error: Callable[[str], Exception], message: str) -> Exception:
    exc = error(message)
    exc.code = ERROR_CODE  # type: ignore[attr-defined]
    return exc


def requires_direct(
    url: Any,
    keyed: bool,
    allow_insecure_http: Any = None,
    error: Callable[[str], Exception] = ValueError,
) -> Optional[str]:
    """Judge one request. Returns ``"loopback"`` or ``"opted_in"`` when it is plain ``http://`` with a key and may be
    sent, in which case it must be sent directly; ``None`` when nothing applies; raises ``error(message)`` (with
    ``.code``) when it is refused."""
    if not keyed:
        return None
    plain, host = _target(url)
    if not plain:
        return None
    if not host:
        raise refuse(error, "API keys are not sent to an http:// URL whose host cannot be read. Use an https:// base URL.")
    if not host.isascii():
        raise refuse(
            error,
            "API keys are not sent to an http:// URL whose host or port is written with non-ASCII characters. Use an "
            "https:// base URL.",
        )
    if is_loopback_host(host):
        return "loopback"
    if _ambiguous_host(host):
        raise refuse(
            error,
            f"API keys are not sent over http:// to {host}: a host ending in a dot or an IPv4 address in a short, hex "
            "or octal form is read differently by different resolvers. Write the host in full, or use an https:// base URL.",
        )
    if insecure_http_allowed(allow_insecure_http):
        return "opted_in"
    raise refuse(
        error,
        f"API keys are not sent over http:// to {host}. Use an https:// base URL, or set "
        f"{INSECURE_HTTP_ENV}=1 (or pass allow_insecure_http=True where the client accepts it) to send over http:// "
        "without a proxy.",
    )


# --- redirects of ``requests`` calls ------------------------------------------------------------


def requests_redirect_target(response: Any, strict: bool = True) -> Optional[str]:
    """The URL ``requests`` connects to when it follows ``response`` (as ``Session.resolve_redirects`` builds it), or
    ``None`` when ``response`` is not a redirect. With ``strict``, raises ``ValueError`` (with ``.code``) for a
    ``Location`` that holds a control character, DEL or whitespace."""
    from urllib.parse import urljoin, urlparse

    from requests.models import PreparedRequest
    from requests.utils import requote_uri

    if not getattr(response, "is_redirect", False):
        return None
    location = _text(response.headers.get("location"))
    try:
        location = location.encode("latin-1").decode("utf8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    if strict and (_CONTROL.search(location) or any(ch.isspace() for ch in location)):
        raise refuse(ValueError, "API keys are not sent to a redirect target whose Location holds control characters or whitespace.")
    previous = urlparse(response.url or "")
    if location.startswith("//"):
        location = f"{previous.scheme}:{location}"
    parsed = urlparse(location)
    if parsed.fragment == "" and previous.fragment:
        parsed = parsed._replace(fragment=previous.fragment)
    url = parsed.geturl()
    url = urljoin(response.url, requote_uri(url)) if not parsed.netloc else requote_uri(url)
    prepared = PreparedRequest()
    prepared.prepare_url(url, None)
    return prepared.url


def _redirect_adds_key(response: Any, target: str, session: Any) -> bool:
    """Whether ``requests`` adds a key to the request for ``target`` when it follows ``response``: a cookie named
    ``X-Api-Key`` or ``X-Secret-Key`` from the request, the response or the session, or ``.netrc`` credentials."""
    from requests.cookies import RequestsCookieJar, merge_cookies
    from requests.models import PreparedRequest
    from requests.utils import get_netrc_auth

    try:
        jar = RequestsCookieJar()
        request_jar = getattr(getattr(response, "request", None), "_cookies", None)
        if request_jar is not None:
            merge_cookies(jar, request_jar)
        merge_cookies(jar, response.cookies)
        if session is not None:
            merge_cookies(jar, session.cookies)
        hop = PreparedRequest()
        hop.prepare_url(target, None)
        hop.prepare_headers({})
        hop.prepare_cookies(jar)
        if carries_key(hop.headers):
            return True
        return bool(getattr(session, "trust_env", True) and get_netrc_auth(target))
    except Exception:
        return True


_OWN_HOOK = "_fi_http_guard_hook"


def _own_hook(hook: Callable[..., Any]) -> Callable[..., Any]:
    """Mark ``hook`` as one of the response hooks registered here, which add no key."""
    setattr(hook, _OWN_HOOK, True)
    return hook


def _has_response_hooks(hooks: Any, foreign_only: bool = False) -> bool:
    """Whether ``hooks`` (a response hook, or a container of them) holds a hook, judged by iterating it, so a
    container that reads as false but holds hooks counts. With ``foreign_only``, hooks registered here are left
    out. A value that cannot be read counts as holding a hook."""
    if hooks is None:
        return False
    if callable(hooks) and not hasattr(hooks, "__iter__"):
        return not (foreign_only and getattr(hooks, _OWN_HOOK, False))
    try:
        return any(not (foreign_only and getattr(hook, _OWN_HOOK, False)) for hook in hooks)
    except Exception:
        return True


def _hop_may_add_key(response: Any, target: str, session: Any) -> bool:
    """Whether something the session holds may add a key to the request for ``target`` when ``requests`` follows
    ``response``: a response hook of the session or of the request (other than those registered here, among them
    the hooks the request's authentication registered), the session's authentication, or a mounted adapter for
    ``target`` that is not exactly ``HTTPAdapter``. Such a hook may set the key on the request or a session cookie
    before the hop is built, or send the hop again with a key through ``session.send``, which cannot be judged."""
    from requests.adapters import HTTPAdapter

    if session is None:
        return False
    try:
        if getattr(session, "auth", None) is not None:
            return True
        if _has_response_hooks((getattr(session, "hooks", None) or {}).get("response")):
            return True
        request_hooks = getattr(getattr(response, "request", None), "hooks", None) or {}
        if _has_response_hooks(request_hooks.get("response"), foreign_only=True):
            return True
        return type(session.get_adapter(target)) is not HTTPAdapter
    except Exception:
        return True


def requests_redirect_check(
    keyed: bool,
    allow_insecure_http: Any,
    session: Any = None,
) -> Callable[..., Any]:
    """A ``requests`` response hook that refuses to follow a redirect of a keyed request to plain ``http://`` that
    may not be sent (see :func:`requires_direct`), through a proxy, or through a custom adapter. The redirect is
    keyed when the request was, or when following it adds a key (see :func:`_redirect_adds_key`). It is judged as
    keyed as well when the session may add a key to the hop (see :func:`_hop_may_add_key`): then the hop may not go
    to plain ``http://`` that a key may not be sent to, nor through a proxy that ``requests`` would use for it."""

    def check(response, *args, **kwargs):
        if not getattr(response, "is_redirect", False):
            return response
        request = getattr(response, "request", None)
        keyed_hop = True
        if not (keyed or carries_key(getattr(request, "headers", None))):
            target = requests_redirect_target(response, strict=False)
            if target is None:
                return response
            if not _redirect_adds_key(response, target, session):
                if not _hop_may_add_key(response, target, session):
                    return response
                keyed_hop = False
        target = requests_redirect_target(response)
        if target is None:
            return response
        from urllib.parse import urljoin

        requires_direct(urljoin(response.url or "", response.headers.get("location") or ""), True, allow_insecure_http, ValueError)
        if requires_direct(target, True, allow_insecure_http, ValueError) is None:
            return response
        proxies = kwargs.get("proxies")
        if proxies is None and session is not None:
            proxies = dict(getattr(session, "proxies", None) or {})
        if keyed_hop:
            refuse_requests_proxy(target, proxies, session)
        else:
            _refuse_proxy(target, proxies, session)
        return response

    return _own_hook(check)


def _refuse_proxy(url: str, proxies: Any, session: Any) -> None:
    """Raise when ``requests`` would send ``url`` through a proxy: ``proxies`` as given to the send (the session's
    proxies merged in), then, when the session trusts the environment, the environment, as
    ``Session.rebuild_proxies`` resolves them for a redirect hop."""
    from requests.models import PreparedRequest
    from requests.utils import resolve_proxies, select_proxy

    prepared = PreparedRequest()
    prepared.prepare_url(url, None)
    trust_env = getattr(session, "trust_env", True)
    if select_proxy(url, resolve_proxies(prepared, proxies or {}, trust_env)):
        raise refuse(ValueError, "API keys are not sent over http:// through a proxy. Send without a proxy, or use an https:// base URL.")


def refuse_requests_proxy(url: str, proxies: Any, session: Any) -> None:
    """Raise when ``requests`` would send ``url`` through a proxy (``proxies`` as given to the send, then the
    environment) or through an adapter other than ``HTTPAdapter``."""
    from requests.adapters import HTTPAdapter

    _refuse_proxy(url, proxies, session)
    if session is not None and type(session.get_adapter(url)) is not HTTPAdapter:
        raise refuse(ValueError, "API keys are not sent over http:// through a custom adapter. Use an https:// base URL.")


# --- sending directly -------------------------------------------------------------------------


def requests_direct_proxies(url: Any) -> Dict[str, Optional[str]]:
    """``proxies=`` for a ``requests`` call that must not use a proxy: every entry that could match is cleared."""
    from urllib.parse import urlparse

    host = urlparse(str(url)).hostname or ""
    return {
        "http": None,
        "all": None,
        f"http://{host}": None,
        f"all://{host}": None,
        "no_proxy": "*",
    }


def requests_keyed_proxies(proxies: Any) -> Dict[str, Optional[str]]:
    """``proxies=`` for a keyed ``requests`` send: ``proxies`` (the session and environment settings) with every
    plain-http entry cleared, so plain ``http://``, on the first request or a redirect, goes through no proxy."""
    kept = {k: v for k, v in dict(proxies or {}).items() if not str(k).lower().startswith("http://")}
    kept["http"] = None
    return kept


def direct_mounts(limits: Optional[httpx.Limits] = None) -> Dict[str, httpx.HTTPTransport]:
    """``mounts=`` for an ``httpx.Client`` the SDK builds: plain ``http://`` goes direct, whatever the environment says."""
    return {"http://": httpx.HTTPTransport(limits=limits) if limits else httpx.HTTPTransport()}


def direct_async_mounts(limits: Optional[httpx.Limits] = None) -> Dict[str, httpx.AsyncHTTPTransport]:
    """:func:`direct_mounts` for an ``httpx.AsyncClient``."""
    return {"http://": httpx.AsyncHTTPTransport(limits=limits) if limits else httpx.AsyncHTTPTransport()}


_PROXY_POOL_NAMES = ("HTTPProxy", "AsyncHTTPProxy", "SOCKSProxy", "AsyncSOCKSProxy")
# A pool counts as direct only when it is exactly one of these httpcore classes (a subclass may route anywhere), holds
# no ``proxy=`` setting and uses exactly one of httpcore's own network backends for that pool.
_DIRECT_POOL_BACKENDS = (
    ("ConnectionPool", (("httpcore", "SyncBackend"),)),
    (
        "AsyncConnectionPool",
        (("httpcore._backends.auto", "AutoBackend"), ("httpcore", "AnyIOBackend"), ("httpcore", "TrioBackend")),
    ),
)
_IN_PROCESS = (httpx.MockTransport, httpx.WSGITransport, httpx.ASGITransport)
_TRANSPORTS = (httpx.BaseTransport, httpx.AsyncBaseTransport)


def _pool_classes(names: Tuple[str, ...]) -> Tuple[type, ...]:
    import httpcore

    return tuple(cls for cls in (getattr(httpcore, name, None) for name in names) if isinstance(cls, type))


def _httpcore_class(module: str, name: str) -> Optional[type]:
    try:
        cls = getattr(importlib.import_module(module), name, None)
    except Exception:
        return None
    return cls if isinstance(cls, type) else None


# Methods that, set on a pool or backend instance, take the place of httpcore's own.
_POOL_METHODS = ("handle_request", "handle_async_request", "create_connection")
_BACKEND_METHODS = ("connect_tcp", "connect_unix_socket")
# The backends httpcore's automatic backend hands each connection to, once it has picked one.
_AUTO_INNER_BACKENDS = (("httpcore", "AnyIOBackend"), ("httpcore", "TrioBackend"))


def _instance_names(value: Any) -> dict:
    return getattr(value, "__dict__", None) or {}


def _is_own_backend(backend: Any, classes: Tuple[Tuple[str, str], ...]) -> bool:
    """Whether ``backend`` is exactly one of ``classes``, with none of its methods set on the instance and, when it
    holds a backend it hands connections to (httpcore's automatic backend), that backend exactly httpcore's AnyIO or
    Trio backend with none of its methods set on the instance."""
    if not any(cls is not None and type(backend) is cls for cls in (_httpcore_class(*each) for each in classes)):
        return False
    names = _instance_names(backend)
    if any(name in names for name in _BACKEND_METHODS):
        return False
    if "_backend" in names:
        return _is_own_backend(names["_backend"], _AUTO_INNER_BACKENDS)
    return True


def _is_direct_pool(pool: Any) -> bool:
    """Whether ``pool`` is exactly httpcore's ``ConnectionPool`` or ``AsyncConnectionPool`` (not a subclass), with no
    ``proxy=`` setting, none of its request or connection methods set on the instance, and exactly one of httpcore's
    own network backends (see :func:`_is_own_backend`). A pool without a readable backend, or a class httpcore does
    not provide, counts as not direct."""
    missing = object()
    backend = getattr(pool, "_network_backend", missing)
    if backend is missing or getattr(pool, "_proxy", None) is not None:
        return False
    if any(name in _instance_names(pool) for name in _POOL_METHODS):
        return False
    for pool_name, backends in _DIRECT_POOL_BACKENDS:
        pool_class = _httpcore_class("httpcore", pool_name)
        if pool_class is not None and type(pool) is pool_class:
            return _is_own_backend(backend, backends)
    return False


def _attributes(holder: Any) -> list:
    values = list(getattr(holder, "__dict__", {}).values())
    for cls in type(holder).__mro__:
        slots = cls.__dict__.get("__slots__", ())
        for slot in (slots,) if isinstance(slots, str) else slots:
            if slot not in ("__dict__", "__weakref__") and hasattr(holder, slot):
                values.append(getattr(holder, slot))
    return values


def _inner_transports(transport: Any) -> list:
    """Transports held by ``transport``: in its attributes (``__dict__`` and ``__slots__``), in dicts, lists, tuples
    and sets at any depth, and the transports of an ``httpx`` client it holds (its own and every mounted one)."""
    found: list = []
    seen: set = set()
    pending = _attributes(transport)
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, _TRANSPORTS):
            found.append(value)
        elif isinstance(value, (httpx.Client, httpx.AsyncClient)):
            pending.append(getattr(value, "_transport", None))
            pending.extend((getattr(value, "_mounts", None) or {}).values())
        elif isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, (list, tuple, set, frozenset)):
            pending.extend(value)
    return found


def _is_proxy_transport(transport: Any, seen: Optional[set] = None) -> bool:
    """Whether ``transport``, or a transport it holds, sends through a proxy. A connection pool counts as a proxy
    unless it is exactly httpcore's ``ConnectionPool`` or ``AsyncConnectionPool`` (a subclass counts as a proxy) with
    no ``proxy=`` setting and httpcore's own network backend; an ``httpx`` HTTP transport that holds no pool counts as
    a proxy too. Another transport with no pool and no inner transport is direct."""
    seen = set() if seen is None else seen
    if id(transport) in seen:
        return False
    seen.add(id(transport))
    if isinstance(transport, _IN_PROCESS):
        return False
    pool = getattr(transport, "_pool", None)
    if pool is None and isinstance(transport, (httpx.HTTPTransport, httpx.AsyncHTTPTransport)):
        return True
    if pool is not None:
        if isinstance(pool, _pool_classes(_PROXY_POOL_NAMES)) or not _is_direct_pool(pool):
            return True
    return any(_is_proxy_transport(each, seen) for each in _inner_transports(transport))


def in_process_transport(client: Any, url: Any) -> bool:
    """Whether a client the caller supplied answers ``url`` in the process (``MockTransport``, ``WSGITransport``,
    ``ASGITransport``), so the request makes no connection."""
    try:
        return isinstance(client._transport_for_url(httpx.URL(str(url))), _IN_PROCESS)
    except Exception:
        return False


def httpx_client_may_use_proxy(client: Any, url: Any) -> bool:
    """Whether a client the caller supplied may send ``url`` through a proxy, or cannot be inspected: its transport
    lookup is missing, raises or returns something that is not an ``httpx`` transport."""
    try:
        transport = client._transport_for_url(httpx.URL(str(url)))
        if not isinstance(transport, _TRANSPORTS):
            return True
        return _is_proxy_transport(transport)
    except Exception:
        return True


def refuse_proxied_client(client: Any, url: Any, error: Callable[[str], Exception]) -> None:
    """Raise when a client the caller supplied may route a keyed plain ``http://`` request through a proxy."""
    if httpx_client_may_use_proxy(client, url):
        raise refuse(
            error,
            "API keys are not sent over http:// through a proxy. Send without a proxy, or use an https:// base URL.",
        )
