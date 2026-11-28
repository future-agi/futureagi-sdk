"""How a plain-HTTP request is routed to a proxy: CPython's ``NO_PROXY`` rule, the routers of httpx and
``requests``, and the transports and sessions a caller brings. Used by the plain-HTTP policy
(``fi._core.http_security``), which re-exports these names."""
from __future__ import annotations

import os
import re
import threading
from typing import Any, Mapping, Optional

import httpx

from fi._core.header_key_scan import MAX_SCANNED_LENGTH, CredentialJudgement, holds_key
from fi._core.key_refusal_rules import cookie_names_a_key, inner_transports, is_direct_pool, sdk_direct

_PROXY_NAMES = frozenset({"http_proxy", "all_proxy"})
_ENV_LOCK = threading.RLock()


def _written_port(text: str) -> Optional[str]:
    """The port written in the authority of ``text``, as the ASCII digits written (leading zeros kept), else
    ``None``. A default port written out (``:80``) counts; an empty port (``host:``) does not."""
    rest = text.split("://", 1)[1] if "://" in text else text
    authority = re.split(r"[/?#]", rest, maxsplit=1)[0].rsplit("@", 1)[-1]
    if authority.startswith("["):
        end = authority.find("]")
        tail = authority[end + 1 :] if end >= 0 else ""
        port = tail[1:] if tail.startswith(":") else ""
    else:
        port = authority.rsplit(":", 1)[1] if ":" in authority else ""
    return port if port.isascii() and port.isdigit() else None


_PORT_SPLIT = re.compile("(.*):([0-9]*)", re.DOTALL)


def _no_proxy_value(env: Mapping[str, str]) -> Optional[str]:
    """The ``no`` entry of CPython's ``getproxies_environment``: a variable named ``no_proxy`` in any letter case
    with a non-empty value sets it (the last such in the environment's order); then a variable whose name ends
    in lower-case ``_proxy`` (``no_proxy``, ``NO_proxy``) replaces it, and when its value is empty removes it, so
    an empty ``no_proxy`` wins over ``NO_PROXY``."""
    named = [(str(n), v) for n, v in env.items() if len(str(n)) == 8 and str(n).lower() == "no_proxy"]
    value: Optional[str] = None
    for _, text in named:
        if text:
            value = text
    for name, text in named:
        if name[-6:] == "_proxy":
            value = text if text else None
    return value


def _bypassed(host: str, no_proxy: str) -> bool:
    """CPython's ``urllib.request.proxy_bypass_environment``: ``host`` is the host with the port as written
    (``example.com:08``). The whole value ``*`` bypasses every host. Otherwise each comma-separated entry,
    trimmed, without leading dots and lower-case, bypasses the host when it equals it, with or without the
    port, or is a dot-separated suffix of either. The host's trailing dot is part of the name. A ``*`` inside a
    longer list or a name is a literal character. CIDR ranges are not supported."""
    if no_proxy == "*":
        return True
    host = host.lower()
    match = _PORT_SPLIT.fullmatch(host)
    hostonly = match.group(1) if match else host
    for name in no_proxy.split(","):
        name = name.strip()
        if not name:
            continue
        name = name.lstrip(".").lower()
        if hostonly == name or host == name:
            return True
        name = "." + name
        if hostonly.endswith(name) or host.endswith(name):
            return True
    return False


def _routing_host(parsed: httpx.URL, text: str) -> str:
    host = parsed.raw_host.decode("ascii", "replace").lower()
    host = f"[{host}]" if ":" in host else host
    port = _written_port(text)
    return host if port is None else f"{host}:{port}"


def _proxy_variable_set(env: Mapping[str, str]) -> bool:
    return any(str(name).lower() in _PROXY_NAMES and value for name, value in env.items())


def cpython_env_proxied(url: "httpx.URL | str", environ: Optional[Mapping[str, str]] = None) -> bool:
    """Whether the proxy variables and CPython's ``NO_PROXY`` rule (:func:`_bypassed`) route an ``http://``
    request to ``url``: ``HTTP_PROXY`` / ``http_proxy`` or ``ALL_PROXY`` / ``all_proxy`` (any letter case, a
    non-empty value) is set and the host is not exempted. ``HTTPS_PROXY`` alone does not route it. The host is
    lower-case ASCII (IDNA) with the trailing dot kept, an IPv6 address in brackets, and ``:port`` as written
    when the URL has one. This is the rule both languages' clients share (tests/fixtures/loopback/proxy_env.json)."""
    env = os.environ if environ is None else environ
    if not _proxy_variable_set(env):
        return False
    try:
        text = url if isinstance(url, str) else str(url)
        no_proxy = _no_proxy_value(env)
        if no_proxy is None:
            return True
        return not _bypassed(_routing_host(httpx.URL(text), text), no_proxy)
    except Exception:
        return True


class _Environment:
    """Runs a block with ``os.environ`` reading as ``environ`` (the libraries' routers read the process
    environment); a block with no ``environ`` reads the process environment as it is."""

    def __init__(self, environ: Optional[Mapping[str, str]]) -> None:
        self._environ = None if environ is None or environ is os.environ else dict(environ)

    def __enter__(self) -> None:
        if self._environ is not None:
            _ENV_LOCK.acquire()
            self._saved = os.environ
            os.environ = self._environ  # type: ignore[assignment]

    def __exit__(self, *exc: object) -> None:
        if self._environ is not None:
            os.environ = self._saved  # type: ignore[assignment]
            _ENV_LOCK.release()


def _httpx_routes(text: str) -> bool:
    """Whether an ``httpx.Client(trust_env=True)`` sends ``text`` through a proxy (its own router)."""
    with httpx.Client(trust_env=True) as client:
        return client._transport_for_url(httpx.URL(text)) is not client._transport  # type: ignore[attr-defined]


def _requests_routes(text: str) -> bool:
    """Whether ``requests`` with ``trust_env`` sends ``text`` through a proxy (``get_environ_proxies``)."""
    try:
        from requests.utils import get_environ_proxies, select_proxy
    except ImportError:
        return False
    return bool(select_proxy(text, get_environ_proxies(text)))


def library_env_proxied(url: "httpx.URL | str", environ: Optional[Mapping[str, str]] = None) -> bool:
    """Whether httpx or ``requests`` (each with ``trust_env``) routes an ``http://`` request to ``url`` through an
    environment proxy, by their own routers. A router that cannot answer counts as routing."""
    text = url if isinstance(url, str) else str(url)
    if environ is not None and not _proxy_variable_set(environ):
        return False
    with _Environment(environ):
        for routes in (_httpx_routes, _requests_routes):
            try:
                if routes(text):
                    return True
            except Exception:
                return True
    return False


def env_proxied(url: "httpx.URL | str", environ: Optional[Mapping[str, str]] = None) -> bool:
    """Whether an ``http://`` request to ``url`` counts as routed by an environment proxy: the CPython rule
    (:func:`cpython_env_proxied`) or the router of httpx or ``requests`` (:func:`library_env_proxied`) says so.
    The two disagree on some ``NO_PROXY`` values (httpx does not match ``example.com`` against
    ``.example.com``); a request either routes counts as proxied."""
    return cpython_env_proxied(url, environ) or library_env_proxied(url, environ)


def _proxied(url: "httpx.URL | str", environ: Optional[Mapping[str, str]] = None) -> bool:
    """:func:`env_proxied`."""
    return env_proxied(url, environ)


_PROXY_POOLS = frozenset({"HTTPProxy", "AsyncHTTPProxy", "SOCKSProxy", "AsyncSOCKSProxy"})
_DIRECT_POOLS = frozenset({"ConnectionPool", "AsyncConnectionPool"})
_OWN_TRANSPORTS = (httpx.HTTPTransport, httpx.AsyncHTTPTransport)


def _is_proxy_transport(transport: object, _seen: Optional[set] = None) -> bool:
    """Whether ``transport`` sends through a proxy, or cannot be inspected (fail closed). A transport is
    inspected through its connection pool when it is exactly httpx's own ``HTTPTransport`` or ``AsyncHTTPTransport``
    (a subclass can route a request anywhere), as exactly ``httpx.MockTransport`` (no network; a subclass is a custom
    transport), as decided by the environment check (the SDK's own env-routed transports), or through every transport
    it holds in an attribute, whatever the attribute is called. Anything else is a custom transport the SDK cannot see
    into, and counts as proxied."""
    seen = set() if _seen is None else _seen
    if id(transport) in seen:
        return False
    seen.add(id(transport))
    if type(transport) is httpx.MockTransport or sdk_direct(transport):
        return False
    pool = getattr(transport, "_pool", None)
    if pool is not None and (type(transport) not in _OWN_TRANSPORTS or not is_direct_pool(pool)):
        return True  # 0.8.1: only exactly httpcore's own pool is direct, and every transport held is judged as well
    inner = inner_transports(transport)
    if pool is None and not inner:
        return True
    return any(_is_proxy_transport(each, seen) for each in inner)


_CREDENTIAL_HEADERS = frozenset({"x-api-key", "x-secret-key", "authorization"})
# A key value shorter than this is not looked for inside other header values: a short string would match unrelated text.
_MIN_KEY_VALUE_LENGTH = 8
# The environment variables whose values are looked for in header values.
_KEY_VARIABLES = ("FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN")


def _environment_keys() -> list[str]:
    """The values of :data:`_KEY_VARIABLES` in the environment that are long enough to look for in a header value."""
    values = (os.environ.get(name) for name in _KEY_VARIABLES)
    return [value for value in values if value and len(value) >= _MIN_KEY_VALUE_LENGTH]


def header_pairs(headers: Any) -> list[tuple[Any, Any]]:
    """The ``(name, value)`` pairs of a header set in any form the senders are handed: a mapping, ``httpx.Headers``, a list,
    tuple or other iterable of pairs (names as ``str`` or ``bytes``), or a collection of bare names (the value is ``None``).
    An iterator is read once. Raises when an entry cannot be read as a name or a pair."""
    if headers is None:
        return []
    if isinstance(headers, (str, bytes, bytearray)):
        return [(headers, None)]
    multi_items = getattr(headers, "multi_items", None)  # httpx.Headers keeps repeated names
    if callable(multi_items):
        return list(multi_items())
    items = getattr(headers, "items", None)
    if callable(items):
        return list(items())
    pairs: list[tuple[Any, Any]] = []
    for entry in headers:
        if isinstance(entry, (str, bytes, bytearray)):
            pairs.append((entry, None))
        else:
            entry = tuple(entry)
            pairs.append((entry[0], entry[1] if len(entry) > 1 else None))
    return pairs


def normalize_header_name(name: Any) -> str:
    """A header name as the senders compare it: ``bytes`` read as Latin-1, white space around it removed, letter case
    folded, and ``_`` read as ``-`` (servers that map one to the other read ``x_api_key`` as ``x-api-key``)."""
    text = bytes(name).decode("latin-1") if isinstance(name, (bytes, bytearray)) else str(name)
    return text.strip().casefold().replace("_", "-")


def header_text(value: Any) -> str:
    """A header value as text: ``bytes`` read as Latin-1."""
    return bytes(value).decode("latin-1") if isinstance(value, (bytes, bytearray)) else str(value)


def judge_credentials(headers: Any) -> CredentialJudgement:
    """:func:`carries_credentials` with what it found. The values are read in order, each up to the cap once; the first
    value over the cap ends the pass, and the values after it are kept unread for :meth:`CredentialJudgement.only_unscanned`."""
    try:
        pairs = header_pairs(headers)
        if any(normalize_header_name(name) in _CREDENTIAL_HEADERS or cookie_names_a_key(name, value) for name, value in pairs):
            return CredentialJudgement(True)
        keys = _environment_keys()
        if not keys:
            return CredentialJudgement(False)
        texts = [header_text(value) for _, value in pairs if value is not None]
        for index, text in enumerate(texts):
            if len(text) > MAX_SCANNED_LENGTH:
                unread = tuple(later for later in texts[index + 1:] if len(later) <= MAX_SCANNED_LENGTH)
                return CredentialJudgement(True, tuple(keys), unread, over_cap=True)
            if holds_key(text, keys):
                return CredentialJudgement(True)
        return CredentialJudgement(False)
    except Exception:
        return CredentialJudgement(True)


def carries_credentials(headers: Any) -> bool:
    """Whether a request's final headers hold a Future AGI key: ``X-Api-Key``, ``X-Secret-Key`` or ``Authorization``, or,
    for headers that have values, a value that holds ``FI_API_KEY``, ``FI_SECRET_KEY`` or ``FI_PLATFORM_TOKEN`` from the
    environment (eight characters or longer) as written or encoded (:func:`fi._core.header_key_scan.holds_key`); while
    one of them is set, a value longer than 64 KiB counts as holding it without being read. Headers are
    read in every form :func:`header_pairs` reads; a name is compared as :func:`normalize_header_name` writes it (``bytes``
    names, white space around a name, any letter case, ``_`` for ``-``). A request that carries one is a keyed request,
    whether or not the client resolved a key of its own. Headers that cannot be read count as keyed."""
    return judge_credentials(headers).carried


class SdkDirectTransport(httpx.HTTPTransport):
    """The transport the SDK mounts for plain ``http://`` on a client it builds: a direct connection that reads no
    proxy variable. The plain-HTTP check recognises it by ``_fi_decided_by_environment``."""

    _fi_decided_by_environment = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        from fi._core.loopback import pin_localhost

        pin_localhost(self)


class SdkDirectAsyncTransport(httpx.AsyncHTTPTransport):
    """:class:`SdkDirectTransport` for an ``httpx.AsyncClient``."""

    _fi_decided_by_environment = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        from fi._core.loopback import pin_localhost

        pin_localhost(self)


def _is_sdk_built(transport: object, _seen: Optional[set] = None) -> bool:
    """Whether ``transport`` is one the SDK built for itself (it carries ``_fi_decided_by_environment``, directly
    or in every transport it wraps). Such a transport sends a plain ``http://`` request straight to its host and
    reads no proxy variable for it."""
    seen = set() if _seen is None else _seen
    if id(transport) in seen:
        return True
    seen.add(id(transport))
    if sdk_direct(transport):
        return True
    if getattr(transport, "_pool", None) is not None:
        return False
    inner = [v for v in getattr(transport, "__dict__", {}).values()
             if isinstance(v, (httpx.BaseTransport, httpx.AsyncBaseTransport))]
    return bool(inner) and all(_is_sdk_built(each, seen) for each in inner)


def httpx_client_sdk_built(client: object, url: "httpx.URL | str") -> bool:
    """Whether the transport an ``httpx`` client uses for ``url`` is one the SDK built (see :func:`_is_sdk_built`),
    so that a plain ``http://`` request goes direct whatever the environment says. A caller's client is not."""
    try:
        parsed = url if isinstance(url, httpx.URL) else httpx.URL(str(url))
        return _is_sdk_built(client._transport_for_url(parsed))  # type: ignore[attr-defined]
    except Exception:
        return False


def httpx_client_proxied(client: object, url: "httpx.URL | str") -> bool:
    """Whether an ``httpx.Client`` or ``httpx.AsyncClient`` may send a request to ``url`` through a proxy: its
    transport for that URL (a ``proxy=`` argument, ``mounts=`` or ``trust_env`` proxies) is a proxy transport,
    seen through any transport it holds. A custom transport the SDK cannot see into, and a client that cannot
    answer, count as proxied (fail closed)."""
    try:
        parsed = url if isinstance(url, httpx.URL) else httpx.URL(str(url))
        return _is_proxy_transport(client._transport_for_url(parsed))  # type: ignore[attr-defined]
    except Exception:
        return True


def requests_session_sdk_built(session: object) -> bool:
    """Whether ``session`` is the SDK's own session class, which sends plain ``http://`` requests direct."""
    from fi._core.requests_session import LoopbackDirectSession

    return isinstance(session, LoopbackDirectSession)


def requests_session_proxied(session: object, url: "httpx.URL | str") -> bool:
    """Whether a ``requests`` session may send a request to ``url`` through a proxy of its own: a ``proxies``
    entry for the scheme, for ``all`` or for the scheme and host (``requests.utils.select_proxy``), or an
    adapter that is not exactly ``HTTPAdapter`` (or the SDK's localhost adapter). The sessions judged are the ones that send
    the request (:func:`fi._core.requests_session.session_chain`): a ``FuturesSession(session=inner)`` hands its requests
    to ``inner``, so the proxies and ``trust_env`` of ``inner`` decide and those of the outer session, which sends
    nothing, do not (0.8.1 judged the session that sends). A session that cannot be inspected, and a chain of sessions
    that hand their requests on and comes back to one of them, count as proxied (fail closed); an object with no
    adapters (a stand-in) has nothing to inspect. A session with its own ``request`` that hands requests on is not judged
    here: a send it makes itself, through its proxies, adapters or environment, is judged as it is made (``judging_sends``)."""
    from fi._core.requests_session import sending_chain

    try:
        chain = sending_chain(session)
    except Exception:
        return True
    return chain is None or any(_one_session_proxied(each, url) for each in chain[-1:])


def _one_session_proxied(session: object, url: "httpx.URL | str") -> bool:
    """:func:`requests_session_proxied` for one session of the chain."""
    try:
        from requests.adapters import HTTPAdapter
        from requests.utils import select_proxy

        from fi._core.requests_session import LocalhostAdapter

        text = str(url)
        proxies = getattr(session, "proxies", None)
        if proxies and select_proxy(text, dict(proxies)):
            return True
        # A session reads the proxy variables when it sends (``trust_env``, on by default), also after it was built: the
        # request counts as proxied when the environment's rule or the router of ``requests`` says so, loopback included.
        if getattr(session, "trust_env", True):
            import requests

            if isinstance(session, requests.Session):
                # ``requests`` routes by its own rule (``NO_PROXY`` with hosts, ports and CIDR ranges included), so its answer decides.
                if select_proxy(text, session.merge_environment_settings(text, {}, None, None, None)["proxies"]):
                    return True
            elif env_proxied(text):
                return True
        get_adapter = getattr(session, "get_adapter", None)
        adapter = get_adapter(text) if get_adapter is not None else None
        if adapter is None:
            return False
        # Only requests' own adapter class is known to send direct: a subclass can route a request anywhere. Its cache of
        # proxy managers is not read: requests' own adapter uses a proxy only when one is selected for the request (0.8.1).
        return type(adapter) not in (HTTPAdapter, LocalhostAdapter)
    except Exception:
        return True
