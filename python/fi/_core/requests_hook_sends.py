"""Keyed sends that run after a ``requests`` call was judged: response hooks and custom adapters (the 0.8.1 rule).

A response hook of a caller's session (or one its authentication registers) may send the request again through
``session.send`` with a key, to another URL or through a proxy, and a mounted adapter that is not exactly
``requests``' own may add a key as it sends. ``HttpClient`` therefore judges a request on such a session as one that
carries a key (:func:`may_add_key_later`), and while its call is in progress every send through that session is judged
as it is made (:func:`judging_sends`): a keyed plain-http send that the shared rule refuses, or that a proxy or an
adapter other than ``requests``' own would carry, raises before it connects.
"""

from __future__ import annotations

import contextlib
import contextvars
import inspect
import threading
from typing import Any, Iterable, Iterator, Mapping, Optional

from requests.adapters import HTTPAdapter

from fi._core.proxy_routing import carries_credentials

_LOCK = threading.Lock()


class _Call:
    """An ``HttpClient`` call in progress and its opt-in."""

    __slots__ = ("allow",)

    def __init__(self, allow: Optional[bool]) -> None:
        self.allow = allow


class _ContextExecutor:
    """Stands in for the thread pool of a caller's ``FuturesSession``: each task runs in a copy of the context of the
    thread that submitted it, so a send the pool makes for an ``HttpClient`` call is judged with that call's opt-in.
    Other attributes are the pool's."""

    def __init__(self, executor: Any) -> None:
        self._executor = executor

    def submit(self, fn: Any, /, *args: Any, **kwargs: Any) -> Any:
        return self._executor.submit(contextvars.copy_context().run, fn, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._executor, name)


# The call this thread or task is making, and the call whose send is in progress on it (a send made inside that send,
# by a response hook or an adapter, is judged with the same call's opt-in).
_CALL: "contextvars.ContextVar[Optional[_Call]]" = contextvars.ContextVar("fi_keyed_call", default=None)
_SENDING: "contextvars.ContextVar[Optional[_Call]]" = contextvars.ContextVar("fi_keyed_send", default=None)


def _origin(url: str) -> str:
    """``scheme://authority/`` of ``url``: the authority runs to the first ``/``, ``?`` or ``#`` after ``://``, so user
    info, a backslash and every other character of the authority stay in it. Text without ``://`` is returned as is."""
    start = url.find("://")
    if start < 0:
        return url
    end = len(url)
    for mark in "/?#":
        found = url.find(mark, start + 3)
        if 0 <= found < end:
            end = found
    return url[:end] + "/"


def _strictest(calls: Iterable[_Call]) -> Optional[bool]:
    allows = [each.allow for each in calls]
    if any(each is False for each in allows):
        return False
    return None if any(each is not True for each in allows) else True


def _own_adapter(adapter: Any) -> bool:
    from fi._core.requests_session import LocalhostAdapter

    return type(adapter) in (HTTPAdapter, LocalhostAdapter)


def _has_hooks(hooks: Any) -> bool:
    """Whether ``hooks`` (a response hook, or a container of them) holds a hook, read by iterating it, so a container
    that reads as false but holds hooks counts. A value that cannot be read counts as holding one."""
    if hooks is None:
        return False
    if callable(hooks) and not hasattr(hooks, "__iter__"):
        return True
    try:
        return any(True for _ in hooks)
    except Exception:  # noqa: BLE001 - unreadable hooks are judged as hooks
        return True


def may_add_key_later(chain: list, url: str) -> bool:
    """Whether a session of ``chain`` may add a key after its request is judged: it holds a response hook, or the
    adapter it mounts for ``url`` is not exactly ``requests``' own (the SDK's localhost adapter included)."""
    for session in chain:
        try:
            hooks = getattr(session, "hooks", None)
            if isinstance(hooks, Mapping) and _has_hooks(hooks.get("response")):
                return True
            get_adapter = getattr(session, "get_adapter", None)
            if callable(get_adapter) and not _own_adapter(get_adapter(url)):
                return True
        except Exception:  # noqa: BLE001 - a session that cannot answer is judged as one that may add a key
            return True
    return False


def _proxied(session: Any, request: Any, url: str, kwargs: Mapping[str, Any]) -> bool:
    """Whether ``session.send(request, **kwargs)`` would go through a proxy or a custom adapter: ``proxies`` as given to
    the send, else the session's proxies and, when it trusts the environment, the environment."""
    from requests.utils import resolve_proxies, select_proxy

    try:
        if "proxies" in kwargs:
            proxies = kwargs.get("proxies") or {}
        else:
            proxies = resolve_proxies(request, getattr(session, "proxies", None) or {}, getattr(session, "trust_env", True))
        if select_proxy(url, proxies):
            return True
        return not _own_adapter(session.get_adapter(url))
    except Exception:  # noqa: BLE001 - fail closed
        return True


class _JudgedSend:
    """Stands in for ``send`` on a caller's session, or on an adapter it mounts (a response hook may send again through
    ``response.connection``, the adapter). While an ``HttpClient`` call on that session is in progress, each send is
    judged first (see :func:`judge_send`) with the opt-in of the call it belongs to (see :meth:`call_for`); then it goes
    to the ``send`` set on the object before this one, else to the ``send`` its class has, bound as an attribute read
    binds it (a static or class method, or a callable object, keeps its own binding)."""

    def __init__(self, owner: Any, session: Any, own_send: Any) -> None:
        self._owner = owner
        self._session = session
        self._own_send = own_send
        self.calls: list = []

    def call_for(self, request: Any) -> "tuple[_Call, bool]":
        """The call in progress that ``request`` belongs to, and whether the send is made inside a send of that call:
        the call whose send is in progress on this thread or task, else the call this thread or task is making (the pool
        of a ``FuturesSession`` runs a task in the context it was submitted from). Only calls in progress on this
        session count (a context saved during an earlier call names none). Any other send is judged with the strictest
        opt-in of the calls in progress."""
        calls = list(self.calls)
        for found, inner in ((_SENDING.get(), True), (_CALL.get(), False)):
            if found is not None and found in calls:
                return found, inner
        return (calls[0] if len(calls) == 1 else _Call(_strictest(calls))), False

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        call = None
        if self.calls:
            request = args[0] if args else kwargs.get("request")
            call, inner = self.call_for(request)
            # A send made inside another send (a response hook runs inside it) is judged on its headers; the outer send
            # is judged as keyed too when a hook or a custom adapter may add a key to it.
            adapter = None if self._owner is self._session else self._owner
            judge_send(self._session, request, kwargs, call.allow, outer=not inner, adapter=adapter)
        sending = _SENDING.set(call) if call is not None else None
        try:
            if self._own_send is not None:
                response = self._own_send(*args, **kwargs)
            else:
                response = _class_send(self._owner)(*args, **kwargs)
        finally:
            if sending is not None:
                _SENDING.reset(sending)
        if call is not None and self._owner is not self._session:
            _judge_connection(response, self, call)
        return response


def _class_send(owner: Any) -> Any:
    """The ``send`` the class of ``owner`` has, bound to ``owner`` as reading ``owner.send`` would bind it."""
    found = inspect.getattr_static(type(owner), "send")
    get = getattr(type(found), "__get__", None)
    return get(found, owner, type(owner)) if get is not None else found


class _JudgedConnection:
    """Stands in for ``response.connection`` when it is an adapter the session does not mount (a mounted adapter that
    hands the request to another one): a response hook that sends again through it is judged first, as a send through a
    mounted adapter is (0.8.1 ``_JudgedConnection``). Other attributes are the adapter's."""

    def __init__(self, adapter: Any, judged: "_JudgedSend", call: _Call) -> None:
        self._adapter = adapter
        self._judged = judged
        self._call = call

    def send(self, request: Any, **kwargs: Any) -> Any:
        if self._judged.calls:
            # The connection keeps the opt-in of the call whose response named it (0.8.1 ``_JudgedConnection``).
            judge_send(self._judged._session, request, kwargs, self._call.allow, adapter=self._adapter)
        return self._adapter.send(request, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._adapter, name)


def _judge_connection(response: Any, judged: _JudgedSend, call: _Call) -> None:
    connection = getattr(response, "connection", None)
    if connection is None or isinstance(connection, _JudgedConnection) or isinstance(vars(connection).get("send") if hasattr(connection, "__dict__") else None, _JudgedSend):
        return
    try:
        response.connection = _JudgedConnection(connection, judged, call)
    except Exception:  # noqa: BLE001 - a response that takes no attribute keeps its connection
        pass


def judge_send(session: Any, request: Any, kwargs: Mapping[str, Any], allow_insecure_http: Optional[bool],
               outer: bool = False, adapter: Any = None) -> None:
    """Judge ``request``, sent through ``session.send`` with ``kwargs`` while a keyed call is in progress. A request that
    carries a key is refused (``ConfigurationError``, ``InsecureHttpRefusedError`` or ``KeyedProxyRefusedError``) when
    the shared rule does not send a key to its origin (``scheme://authority/``: a path or query the authentication
    wrote is not judged as a host), or when it is plain ``http://`` and a proxy or a custom adapter would carry it."""
    from fi._core.http_security import require_secure_credentials_url

    url = str(getattr(request, "url", "") or "")
    keyed = carries_credentials(getattr(request, "headers", None))
    if not keyed and not (outer and _may_add_key(session, request, url)):
        return
    if not keyed:
        # A key may be added later (0.8.1): the URL is judged as keyed, and so is a proxy the send settings name.
        from requests.utils import select_proxy

        proxies = kwargs["proxies"] or {} if "proxies" in kwargs else None
        proxied = url[:5].lower() == "http:" and (bool(select_proxy(url, proxies)) if proxies is not None
                                                   else _proxied_by_settings(session, request, url))
    elif adapter is not None:
        from requests.utils import select_proxy

        proxied = url[:5].lower() == "http:" and (bool(select_proxy(url, kwargs.get("proxies") or {}))
                                                   or not _own_adapter(adapter))
    else:
        proxied = url[:5].lower() == "http:" and _proxied(session, request, url, kwargs)
    require_secure_credentials_url(_origin(url), allow_insecure_http=allow_insecure_http, caller_proxied=proxied,
                                   proxies_disabled=True)


def _may_add_key(session: Any, request: Any, url: str) -> bool:
    """Whether a request without a key may get one as it is sent: it holds a response hook (a session subclass may add
    one in ``request``), or the adapter for ``url`` is not exactly ``requests``' own."""
    try:
        if _has_hooks((getattr(request, "hooks", None) or {}).get("response")):
            return True
        return not _own_adapter(session.get_adapter(url))
    except Exception:  # noqa: BLE001 - fail closed
        return True


def sending_sessions(session: Any) -> list:
    """Follow ``session`` attributes from the supplied object, outermost first.

    Return up to 16 objects with a callable ``send``. The walk ends at ``None``, a repeated object, or the
    16th object with a callable ``send``; deeper objects, including a 17th session, are not returned.
    """
    found: list = []
    seen: set = set()
    while session is not None and id(session) not in seen and len(found) < 16:
        seen.add(id(session))
        if callable(getattr(session, "send", None)):
            found.append(session)
        session = getattr(session, "session", None)
    return found


def prepare(chain: list) -> None:
    """Put the judged ``send`` on each session of ``chain`` and on the adapters it mounts when the client is built (it
    judges only while a call is in progress), so that a hook that reads ``session.send`` early holds the judged one."""
    with _LOCK:
        for session in chain:
            _install_all(session)


def _install(owner: Any, session: Any) -> Optional[_JudgedSend]:
    send = vars(owner).get("send") if hasattr(owner, "__dict__") else None
    if isinstance(send, _JudgedSend):
        return send
    try:
        judged = _JudgedSend(owner, session, send)
        owner.send = judged
        return judged
    except Exception:  # noqa: BLE001 - an object that takes no attribute keeps its own send
        return None


def _install_all(session: Any) -> list:
    from concurrent.futures import ThreadPoolExecutor

    executor = getattr(session, "executor", None)
    if isinstance(executor, ThreadPoolExecutor):
        try:
            session.executor = _ContextExecutor(executor)
        except Exception:  # noqa: BLE001 - a session that takes no attribute keeps its pool (its sends get the strictest opt-in)
            pass
    adapters = getattr(session, "adapters", None)
    owners = [session] + (list(adapters.values()) if isinstance(adapters, Mapping) else [])
    return [judged for judged in (_install(owner, session) for owner in owners) if judged is not None]


@contextlib.contextmanager
def judging_sends(chain: list, allow_insecure_http: Optional[bool]) -> Iterator[None]:
    """Judge every send through the sessions of ``chain``, and their adapters, while the block runs (see
    :class:`_JudgedSend`): the call is registered with its opt-in and is the call of this thread or task while the
    block runs."""
    call = _Call(allow_insecure_http)
    installed = []
    with _LOCK:
        for session in chain:
            for judged in _install_all(session):
                judged.calls.append(call)
                installed.append(judged)
    # A call made inside a send of another call (by a response hook) starts as a call of its own.
    tokens = ((_SENDING, _SENDING.set(None)), (_CALL, _CALL.set(call)))
    try:
        yield
    finally:
        with _LOCK:
            for judged in installed:
                judged.calls.remove(call)
        for variable, token in tokens:
            with contextlib.suppress(ValueError):  # a block left in another context keeps that context's values
                variable.reset(token)


def proxy_selected(chain: list, url: str) -> bool:
    """Whether a session of ``chain`` would send ``url`` through a proxy (its proxies and, when it trusts the
    environment, the environment)."""
    import requests

    for session in chain:
        try:
            prepared = requests.Request("GET", url).prepare()
            if _proxied_by_settings(session, prepared, url):
                return True
        except Exception:  # noqa: BLE001 - fail closed
            return True
    return False


def _proxied_by_settings(session: Any, request: Any, url: str) -> bool:
    from requests.utils import resolve_proxies, select_proxy

    proxies = resolve_proxies(request, getattr(session, "proxies", None) or {}, getattr(session, "trust_env", True))
    return bool(select_proxy(url, proxies))
