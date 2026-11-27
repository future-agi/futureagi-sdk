import os
import threading as _threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Generic, Optional, TypeVar, Union


import requests as _requests
from requests import Response
from requests_futures.sessions import FuturesSession

from fi.api.types import RequestConfig
from fi.utils.constants import (
    API_KEY_ENVVAR_NAME,
    get_base_url,
    DEFAULT_MAX_QUEUE,
    DEFAULT_MAX_WORKERS,
    DEFAULT_TIMEOUT,
    SECRET_KEY_ENVVAR_NAME,
)
from fi.utils.errors import MissingAuthError
from fi.utils.executor import BoundedExecutor
from fi.utils import _http_guard as _guard
from fi.utils.utils import ApiKeyName

T = TypeVar("T")
U = TypeVar("U")


class ResponseHandler(Generic[T, U], ABC):
    """Handles response parsing and validation"""

    @classmethod
    def parse(cls, response: Response) -> Union[T, U]:
        """Parse the response into the expected type"""
        if not (200 <= response.status_code < 300):
            cls._handle_error(response)
        return cls._parse_success(response)

    @classmethod
    @abstractmethod
    def _parse_success(cls, response: Response) -> Union[T, U]:
        """Parse successful response"""
        pass

    @classmethod
    @abstractmethod
    def _handle_error(cls, response: Response) -> None:
        """Handle error responses"""
        pass


class HttpClient:
    """Base HTTP client with improved request handling"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        session: Optional[FuturesSession] = None,
        default_headers: Optional[Dict[str, str]] = None,
        allow_insecure_http: Optional[bool] = None,
        **kwargs,
    ):
        self._allow_insecure_http = allow_insecure_http
        self._base_url = base_url.rstrip("/") if base_url else get_base_url().rstrip("/")
        self._session = session or FuturesSession(
            executor=BoundedExecutor(
                bound=kwargs.get("max_queue", DEFAULT_MAX_QUEUE),
                max_workers=kwargs.get("max_workers", DEFAULT_MAX_WORKERS),
            ),
        )
        self._default_headers = default_headers or {}
        self._default_timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)
        _judge_session_chain(self._session)

    def _session_for_headers(self) -> Optional[_requests.Session]:
        """The ``requests`` session whose headers, cookies and authentication apply to a request."""
        session: object = self._session
        for _ in range(8):
            inner = getattr(session, "session", None)
            if not isinstance(inner, _requests.Session):
                break
            session = inner
        return session if isinstance(session, _requests.Session) else None

    def _send(self, method: str, url: str, headers: Dict[str, str], params: Dict, json, data, files, timeout) -> Response:
        """Send one attempt. With a ``requests`` session, the session's authentication runs once, while the session
        prepares the request, and the prepared request is judged right after it, on the object that is sent."""
        session = self._session_for_headers()
        _judge_session_chain(self._session)
        kwargs: Dict
        if session is None:
            kwargs = _unprepared_kwargs(url, headers, self._allow_insecure_http)
        else:
            keyed = _guard.carries_key(headers) or _guard.carries_key(session.headers)
            _guard.requires_direct(url, keyed, self._allow_insecure_http, ValueError)
            may_add_key = _may_add_key_later(session, url)
            if may_add_key:
                _guard.requires_direct(url, True, self._allow_insecure_http, ValueError)
            maybe_keyed = (
                keyed or may_add_key or session.auth is not None or _session_has_key_cookie(session) or session.trust_env
            )
            try:
                direct = _guard.requires_direct(url, maybe_keyed, self._allow_insecure_http, ValueError) is not None
            except ValueError:
                direct = False
            kwargs = {"auth": _Judging(session, url, self._allow_insecure_http, direct)}
            if direct:
                kwargs["proxies"] = _guard.requests_direct_proxies(url)
        return self._session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            files=files,
            timeout=timeout,
            **kwargs,
        ).result()

    def request(
        self,
        config: RequestConfig,
        response_handler: Optional[ResponseHandler[T, U]] = None,
    ) -> Union[Response, T]:
        """Make an HTTP request, retrying only transport-level failures.

        The network round-trip is the only thing retried. Response parsing runs
        once, after the loop, so a parse/deserialization error (or an HTTP error
        status) never re-sends the request — retrying a non-idempotent POST on a
        parse failure silently duplicates server-side writes. A request refused
        for plain http (``.code`` ``insecure_http_origin``) is raised at once.
        """

        url = config.url
        headers = {**self._default_headers, **(config.headers or {})}
        params = config.params or {}
        json = config.json or {}
        timeout = config.timeout or self._default_timeout
        files = config.files or {}
        data = config.data or {}
        response: Optional[Response] = None
        for attempt in range(config.retry_attempts):
            try:
                response = self._send(config.method.value, url, headers, params, json, data, files, timeout)
                break
            except Exception as exc:
                if getattr(exc, "code", None) == _guard.ERROR_CODE or attempt == config.retry_attempts - 1:
                    raise
                time.sleep(config.retry_delay)

        if response_handler:
            return response_handler.parse(response=response)
        return response

    def close(self):
        """Close the client session"""
        self._session.close()


class APIKeyAuth(HttpClient):
    """An ``HttpClient`` that sends ``X-Api-Key`` and ``X-Secret-Key`` with each request. The keys are held by the
    instance, so each client sends its own keys, whichever clients exist in the process or are created at the same
    time on other threads."""

    _fi_api_key: Optional[str] = None
    _fi_secret_key: Optional[str] = None

    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ):
        api_key = fi_api_key or os.environ.get(API_KEY_ENVVAR_NAME)
        secret_key = fi_secret_key or os.environ.get(SECRET_KEY_ENVVAR_NAME)
        if api_key is None or secret_key is None:
            raise MissingAuthError(api_key, secret_key)
        self._fi_api_key = api_key
        self._fi_secret_key = secret_key

        super().__init__(
            base_url=fi_base_url,
            default_headers={
                "X-Api-Key": api_key,
                "X-Secret-Key": secret_key,
            },
            **kwargs,
        )


class APIKeyManager(APIKeyAuth):
    """A process-wide manager of provider keys. Its own keys come from ``FI_API_KEY`` and ``FI_SECRET_KEY``, read
    each time it is created; without them it raises ``MissingAuthError``, and so does reading its ``headers``. It
    does not take the keys of other clients."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def __init__(self):
        try:
            super().__init__()
        except MissingAuthError:
            self._fi_api_key = None
            self._fi_secret_key = None
            self._default_headers = {}
            raise

    @property
    def url(self) -> str:
        return get_base_url() + "/model_hub/api-keys"

    @property
    def headers(self) -> dict:
        api_key = getattr(self, "_fi_api_key", None)
        secret_key = getattr(self, "_fi_secret_key", None)
        if api_key is None or secret_key is None:
            raise MissingAuthError(api_key, secret_key)
        return {
            "X-Api-Key": api_key,
            "X-Secret-Key": secret_key,
        }

    def _initialize(self):
        self._api_keys: Dict[ApiKeyName, Optional[str]] = {
            key: os.getenv(key.value) for key in ApiKeyName
        }

    def get_api_key(self, provider: ApiKeyName) -> Optional[str]:
        if provider not in self._api_keys:
            raise ValueError(f"Provider {provider} not found in API keys")  # noqa: E713
        return self._api_keys[provider]

    def set_api_key(self, provider: ApiKeyName, key: str) -> None:
        self._api_keys[provider] = key

    def validate_required_keys(self, required_providers: list[ApiKeyName]) -> bool:
        if not required_providers:
            return True

        missing_keys = [
            provider.value
            for provider in required_providers
            if provider not in self._api_keys
        ]

        if missing_keys:
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
        return True


def _prepare(session: _requests.Session, request: _requests.Request, allow_insecure_http: Optional[bool] = None) -> _requests.PreparedRequest:
    """``session.prepare_request(request)``. A URL ``requests`` cannot read is judged as written first, so a plain
    ``http://`` URL that a key may not be sent to is reported as that refusal."""
    try:
        return session.prepare_request(request)
    except _requests.exceptions.InvalidURL:
        _guard.requires_direct(request.url, True, allow_insecure_http, ValueError)
        raise


def _session_has_key_cookie(session: _requests.Session) -> bool:
    try:
        return any(_guard.header_name(cookie.name) in ("x-api-key", "x-secret-key") for cookie in session.cookies)
    except Exception:
        return True


class _Judging(_requests.auth.AuthBase):
    """Authentication for a send through a ``requests`` session: it runs the session's own authentication (or the
    ``.netrc`` credentials ``requests`` would use) once, then judges the prepared request (see
    :func:`_judge_prepared`) and registers the redirect check and :func:`_judged_connection_hook`. A response hook
    the authentication registered may send the request again with a key, so plain ``http://`` that a key may not be
    sent to is then refused; a send through ``session.send`` that such a hook makes is judged as it is sent (see
    :class:`_InFlightHook`). ``direct`` says whether the send goes through no proxy;
    when it does not, a keyed plain-http request that a proxy setting would carry is refused. Response hooks added
    to the request after it (the session's, and those given to ``Session.request``, which a session subclass may
    add there) are judged as they are added (see :class:`_JudgedHooks`)."""

    def __init__(self, session: _requests.Session, url: str, allow_insecure_http: Optional[bool], direct: bool) -> None:
        self._session = session
        self._url = url
        self._allow = allow_insecure_http
        self._direct = direct

    def __call__(self, request: _requests.PreparedRequest) -> _requests.PreparedRequest:
        _judge_session_sends(self._session)
        auth = self._session.auth
        if auth is None and self._session.trust_env:
            auth = _requests.utils.get_netrc_auth(request.url)
        if isinstance(auth, tuple) and len(auth) == 2:
            auth = _requests.auth.HTTPBasicAuth(*auth)
        if auth is not None:
            request = auth(request)
        if _guard._has_response_hooks((request.hooks or {}).get("response")):
            self._judge_hooked(request)
        keyed, mode = _judge_prepared(self._session, request, self._allow, self._url)
        if mode is not None and not self._direct:
            _guard.refuse_requests_proxy(request.url, dict(self._session.proxies or {}), self._session)
        request.register_hook("response", _guard.requests_redirect_check(keyed, self._allow, self._session))
        request.hooks["response"].insert(0, _judged_connection_hook(self._allow))
        request.hooks["response"] = _JudgedHooks(request.hooks["response"], lambda: self._judge_hooked(request, True), self._allow)
        return request

    def _judge_hooked(self, request: _requests.PreparedRequest, proxy: bool = False) -> None:
        """Judge ``request``, which has a response hook that may send it again with a key, as keyed. With
        ``proxy``, a send that is not direct is refused as well when a proxy of the session would carry it."""
        _guard.requires_direct(self._url, True, self._allow, ValueError)
        mode = _guard.requires_direct(request.url, True, self._allow, ValueError)
        if proxy and mode is not None and not self._direct:
            _guard._refuse_proxy(request.url, dict(self._session.proxies or {}), self._session)


class _JudgedHooks(list):
    """The response hooks of a request :class:`_Judging` judged. ``Session.prepare_request`` adds the session's
    hooks and those given to ``Session.request`` after the authentication ran; when a hook that is not one of the
    SDK's is added, ``judge`` runs first, so a request that may not be sent with a key is refused before it
    connects. Each hook that is not one of the SDK's is held in an :class:`_InFlightHook`, so a send through the
    session that it makes is judged as well."""

    def __init__(self, hooks, judge, allow_insecure_http: Optional[bool] = None) -> None:
        super().__init__(_in_flight_hooks(hooks, allow_insecure_http))
        self._judge = judge
        self._allow = allow_insecure_http

    def _judged(self, hooks) -> list:
        hooks = list(hooks)
        if _guard._has_response_hooks(hooks, foreign_only=True):
            self._judge()
        return _in_flight_hooks(hooks, self._allow)

    def append(self, hook) -> None:
        super().extend(self._judged([hook]))

    def extend(self, hooks) -> None:
        super().extend(self._judged(hooks))

    def insert(self, index, hook) -> None:
        super().insert(index, *self._judged([hook]))

    def __iadd__(self, hooks):
        self.extend(hooks)
        return self


def _judge_prepared(
    session: _requests.Session,
    prepared: _requests.PreparedRequest,
    allow_insecure_http: Optional[bool] = None,
    url: Optional[str] = None,
):
    """``(keyed, mode)`` for ``prepared`` (see ``requires_direct``). ``url`` is the URL as the caller wrote it, judged
    as well as the prepared one. Raises ``ValueError`` (with ``.code``) when the request is refused, including a
    keyed plain-http request that ``session`` would send through a custom adapter."""
    from requests.adapters import HTTPAdapter

    keyed = _guard.carries_key(prepared.headers)
    if url is not None:
        _guard.requires_direct(url, keyed, allow_insecure_http, ValueError)
    mode = _guard.requires_direct(prepared.url, keyed, allow_insecure_http, ValueError)
    if mode is not None and type(session.get_adapter(prepared.url)) is not HTTPAdapter:
        raise _guard.refuse(ValueError, "API keys are not sent over http:// through a custom adapter. Use an https:// base URL.")
    return keyed, mode


def _send_prepared(
    session: _requests.Session,
    prepared: _requests.PreparedRequest,
    timeout,
    allow_insecure_http: Optional[bool] = None,
    url: Optional[str] = None,
) -> Response:
    """Judge ``prepared`` (see :func:`_judge_prepared`) and send that object with ``session`` as ``Session.request``
    would. A keyed request goes over plain ``http://`` through no proxy, and its redirects are judged the same way
    before they are followed. A send through ``session`` that a response hook of ``prepared`` makes is judged as
    well (see :class:`_InFlightHook`)."""
    keyed, _mode = _judge_prepared(session, prepared, allow_insecure_http, url)
    may_add_key = _may_add_key_later(session, prepared.url, (prepared.hooks or {}).get("response"))
    if may_add_key:
        if url is not None:
            _guard.requires_direct(url, True, allow_insecure_http, ValueError)
        _guard.requires_direct(prepared.url, True, allow_insecure_http, ValueError)
    settings = session.merge_environment_settings(prepared.url, {}, None, None, None)
    if keyed or may_add_key:
        settings["proxies"] = _guard.requests_keyed_proxies(settings.get("proxies"))
    hooks = _in_flight_hooks(prepared.hooks.get("response"), allow_insecure_http)
    prepared.hooks["response"] = hooks
    _judge_session_sends(session)
    hooks.insert(0, _guard.requests_redirect_check(keyed, allow_insecure_http, session))
    hooks.insert(0, _judged_connection_hook(allow_insecure_http))
    return session.send(prepared, timeout=timeout, allow_redirects=True, **settings)


def _may_add_key_later(session: _requests.Session, url: str, hooks=None) -> bool:
    """Whether something that runs after the request is judged may add a key to it: a response hook of the session,
    one of ``hooks`` (the request's response hooks, among them those its authentication registered), or a mounted
    adapter for ``url`` that is not exactly ``HTTPAdapter``. A key added inside a custom adapter cannot be judged,
    and a send through ``session.send`` is judged only while a response hook of a judged request runs on that
    thread, so such a send is judged as keyed. Hook containers are judged by
    their items. The same holds for each redirect hop (see ``requests_redirect_check``)."""
    from requests.adapters import HTTPAdapter

    if _guard._has_response_hooks((session.hooks or {}).get("response")) or _guard._has_response_hooks(hooks):
        return True
    try:
        return type(session.get_adapter(url)) is not HTTPAdapter
    except Exception:
        return True


class _JudgedConnection:
    """Stands in for ``response.connection`` (the adapter that sent the response), so that a request a response hook
    sends again through it (as ``HTTPDigestAuth.handle_401`` does) is judged first: a keyed request to plain
    ``http://`` that may not be sent is refused, and so is one the adapter would send through a proxy (``proxies`` as
    given to that send) or one sent through an adapter that is not exactly ``HTTPAdapter``. Other attributes are the
    adapter's."""

    def __init__(self, adapter, allow_insecure_http: Optional[bool]) -> None:
        self._adapter = adapter
        self._allow = allow_insecure_http

    def send(self, request, **kwargs):
        from requests.adapters import HTTPAdapter
        from requests.utils import select_proxy

        mode = _guard.requires_direct(request.url, _guard.carries_key(request.headers), self._allow, ValueError)
        if mode is not None:
            if select_proxy(request.url, kwargs.get("proxies") or {}):
                raise _guard.refuse(
                    ValueError, "API keys are not sent over http:// through a proxy. Send without a proxy, or use an https:// base URL."
                )
            if type(self._adapter) is not HTTPAdapter:
                raise _guard.refuse(ValueError, "API keys are not sent over http:// through a custom adapter. Use an https:// base URL.")
        response = self._adapter.send(request, **kwargs)
        try:
            response.connection = self
        except Exception:
            pass
        return response

    def __getattr__(self, name):
        return getattr(self._adapter, name)


_IN_FLIGHT = _threading.local()


class _InFlightHook:
    """A response hook of a judged request, called as the hook it holds and returning what that hook returns. While
    it runs, a send that a response hook makes on this thread through a session whose ``send`` is a
    :class:`_JudgedSessionSend` is judged with the hook's ``allow_insecure_http``. It compares equal to the hook it
    holds."""

    __slots__ = ("hook", "allow")

    def __init__(self, hook, allow_insecure_http: Optional[bool]) -> None:
        self.hook = hook
        self.allow = allow_insecure_http

    def __call__(self, *args, **kwargs):
        stack = getattr(_IN_FLIGHT, "allow", None)
        if stack is None:
            stack = _IN_FLIGHT.allow = []
        stack.append(self.allow)
        try:
            return self.hook(*args, **kwargs)
        finally:
            stack.pop()

    def __eq__(self, other) -> bool:
        if isinstance(other, _InFlightHook):
            other = other.hook
        return bool(self.hook == other)

    def __hash__(self) -> int:
        return hash(self.hook)

    def __repr__(self) -> str:
        return repr(self.hook)


def _in_flight_hook(hook, allow_insecure_http: Optional[bool]):
    """``hook`` held in an :class:`_InFlightHook`, unless it is one of the SDK's hooks, already held, or not callable."""
    if not callable(hook) or isinstance(hook, _InFlightHook) or getattr(hook, _guard._OWN_HOOK, False):
        return hook
    return _InFlightHook(hook, allow_insecure_http)


def _in_flight_hooks(hooks, allow_insecure_http: Optional[bool]) -> list:
    """The response hooks ``hooks`` (a hook, or a container of them) as a list, each held by :func:`_in_flight_hook`."""
    if hooks is None:
        return []
    if callable(hooks) and not hasattr(hooks, "__iter__"):
        hooks = [hooks]
    return [_in_flight_hook(hook, allow_insecure_http) for hook in hooks]


class _JudgedSessionSend:
    """Stands in for ``session.send`` on the session object. While an :class:`_InFlightHook` runs on the current
    thread, a send is judged first: a keyed request to plain ``http://`` that may not be sent is refused, and so is
    one that ``Session.send`` would send through a proxy (``proxies`` as given to the send, else the session's
    proxies and, when it trusts the environment, the environment) or through an adapter that is not exactly
    ``HTTPAdapter``. Each send then goes to the ``send`` the session's class has at that time (so a ``send``
    replaced on the class applies), or to the ``send`` set on the session object before this one."""

    def __init__(self, session: _requests.Session, own_send=None) -> None:
        self._session = session
        self._own_send = own_send

    def __call__(self, *args, **kwargs):
        stack = getattr(_IN_FLIGHT, "allow", None)
        if stack:
            request = args[0] if args else kwargs.get("request")
            _judge_hook_send(self._session, request, kwargs, stack[-1])
        if self._own_send is not None:
            return self._own_send(*args, **kwargs)
        return type(self._session).send(self._session, *args, **kwargs)


def _judge_hook_send(session: _requests.Session, request, kwargs: Dict, allow_insecure_http: Optional[bool]) -> None:
    """Judge ``request``, sent through ``session.send`` with ``kwargs`` by a response hook (see
    :class:`_JudgedSessionSend`). Raises ``ValueError`` (with ``.code``) when it is refused."""
    from requests.adapters import HTTPAdapter
    from requests.utils import resolve_proxies, select_proxy

    url = getattr(request, "url", None)
    mode = _guard.requires_direct(url, _guard.carries_key(getattr(request, "headers", None)), allow_insecure_http, ValueError)
    if mode is None:
        return
    if "proxies" in kwargs:
        proxies = kwargs["proxies"] or {}
    else:
        proxies = resolve_proxies(request, session.proxies, session.trust_env)
    if select_proxy(url, proxies):
        raise _guard.refuse(
            ValueError, "API keys are not sent over http:// through a proxy. Send without a proxy, or use an https:// base URL."
        )
    if type(session.get_adapter(url)) is not HTTPAdapter:
        raise _guard.refuse(ValueError, "API keys are not sent over http:// through a custom adapter. Use an https:// base URL.")


def _judge_session_sends(session: _requests.Session) -> None:
    """Put a :class:`_JudgedSessionSend` on ``session.send``. A ``send`` set on the session object itself is held
    and called; otherwise each send goes to the class's ``send`` (a subclass's own included). A session that has
    one keeps it."""
    send = getattr(session, "send", None)
    if send is None or isinstance(send, _JudgedSessionSend):
        return
    try:
        session.send = _JudgedSessionSend(session, vars(session).get("send"))
    except Exception:
        pass


def _judge_session_chain(session: object) -> None:
    """:func:`_judge_session_sends` for ``session`` and each ``requests`` session it wraps as ``.session``."""
    for _ in range(8):
        if isinstance(session, _requests.Session):
            _judge_session_sends(session)
        inner = getattr(session, "session", None)
        if inner is None or inner is session:
            return
        session = inner


def _judged_connection_hook(allow_insecure_http: Optional[bool]):
    """A response hook, registered first, that puts a :class:`_JudgedConnection` on ``response.connection``."""

    def hook(response, *args, **kwargs):
        connection = getattr(response, "connection", None)
        if connection is not None and not isinstance(connection, _JudgedConnection):
            try:
                response.connection = _JudgedConnection(connection, allow_insecure_http)
            except Exception:
                pass
        return response

    return _guard._own_hook(hook)


def _unprepared_kwargs(url: str, headers: Dict[str, str], allow_insecure_http: Optional[bool]) -> Dict:
    """Extra arguments for a session object that is not a ``requests`` session: judged on ``headers`` alone."""
    keyed = _guard.carries_key(headers)
    if not keyed:
        return {}
    kwargs: Dict = {"hooks": {"response": _guard.requests_redirect_check(keyed, allow_insecure_http)}}
    if _guard.requires_direct(url, keyed, allow_insecure_http, ValueError):
        kwargs["proxies"] = _guard.requests_direct_proxies(url)
    return kwargs
