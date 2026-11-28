import os
import time
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Dict, Generic, Mapping, Optional, TypeVar, Union

from requests import Response
from requests_futures.sessions import FuturesSession

from fi._core.proxy_routing import carries_credentials, env_proxied, header_pairs
from fi._core.requests_hook_sends import judging_sends, may_add_key_later, proxy_selected, sending_sessions
from fi._core.requests_hook_sends import prepare as prepare_hook_sends
from fi._core.requests_session import (
    LoopbackDirectSession,
    has_callable_auth,
    prepared_headers,
    same_origin_redirect_target,
    sending_chain,
    session_chain,
)
from fi._core.http_security import (
    require_secure_credential_headers,
    require_secure_credentials_url,
    requests_session_proxied,
    requests_session_sdk_built,
)
from fi._extra_headers import ExtraHeaders, ExtraHeadersError, ExtraHeadersInput, on_platform
from fi.api.types import RequestConfig
from fi.errors import KeyedRedirectRefusedError
from fi.utils.constants import (
    API_KEY_ENVVAR_NAME,
    get_base_url,
    DEFAULT_MAX_QUEUE,
    DEFAULT_MAX_WORKERS,
    DEFAULT_TIMEOUT,
    SECRET_KEY_ENVVAR_NAME,
)
# Published 0.6.13 re-export; keep the same class object at this import path.
from fi.utils.errors import MissingAuthError, DatasetNotFoundError
from fi._credentials import resolve as resolve_credentials
from fi.utils.executor import BoundedExecutor
from fi.utils.utils import ApiKeyName

T = TypeVar("T")
U = TypeVar("U")



class _SdkFuturesSession(FuturesSession, LoopbackDirectSession):
    """The session the SDK builds for itself: loopback and plain ``http://`` requests go straight to their host
    (``LoopbackDirectSession.send``), whatever the proxy variables say. A keyed request goes out with redirects off; a
    redirect on its own origin is returned to ``HttpClient.request``, which follows it, and any other 3xx answer is
    refused by the session."""

    returns_same_origin_redirects = True


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
    """Base HTTP client with improved request handling.

    ``FI_EXTRA_HEADERS`` (``Name=value`` entries) and ``extra_headers=`` (which wins for the same
    name) are added to every request whose URL is under the base URL, read when the request is sent;
    any other URL, and a redirect to one, does not get them (``fi._extra_headers``)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        session: Optional[FuturesSession] = None,
        default_headers: Optional[Dict[str, str]] = None,
        allow_insecure_http: Optional[bool] = None,
        *,
        extra_headers: ExtraHeadersInput = None,
        **kwargs,
    ):
        self._base_url = base_url.rstrip("/") if base_url else get_base_url().rstrip("/")
        self._session = session or _SdkFuturesSession(
            executor=BoundedExecutor(
                bound=kwargs.get("max_queue", DEFAULT_MAX_QUEUE),
                max_workers=kwargs.get("max_workers", DEFAULT_MAX_WORKERS),
            ),
        )
        self._default_headers = default_headers or {}
        self._default_timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)
        self._extra_headers = ExtraHeaders(self._base_url, extra_headers)
        # ``allow_insecure_http``: ``True`` opts in to plain http to a host that is not loopback; any other value given
        # (such as ``False``) turns the opt-in off whatever FI_ALLOW_INSECURE_HTTP says; not given, the variable decides.
        self._allow_insecure_http = None if allow_insecure_http is None else allow_insecure_http is True
        _guard_redirects(self._session, self._extra_headers)
        if not requests_session_sdk_built(self._session):
            prepare_hook_sends(sending_sessions(self._session))

    def _platform_headers(self, url: str, headers: Dict[str, str]) -> Dict[str, str]:
        """``headers`` plus the extra headers for ``url`` (none off the base URL); for the few
        modules that send with ``requests`` directly (file uploads)."""
        extra = getattr(self, "_extra_headers", None)  # a subclass that skipped __init__ sends none
        if extra is not None:
            extra.apply(headers, url)
        return headers

    def _direct_kwargs(self, request_kwargs: Dict) -> Dict:
        """``requests.<method>(**kwargs)`` arguments for a one-off call (file uploads) with the extra
        headers for its URL. When any was added, redirects are not followed, so they do not reach
        another host. A call that carries the SDK's keys is decided like any other request
        (the shared checks); it is sent without a session, so a plain request goes directly."""
        headers = dict(request_kwargs.get("headers") or {})
        outgoing = {**headers, "Authorization": ""} if request_kwargs.get("auth") is not None else headers
        # These calls go out on a session the SDK builds (``LoopbackDirectSession``), which sends a plain-HTTP request
        # direct whatever the proxy variables say.
        url = str(request_kwargs["url"])
        require_secure_credential_headers(url, outgoing, proxies_disabled=url[:7].lower() == "http://",
                                          allow_insecure_http=getattr(self, "_allow_insecure_http", None))
        before = len(headers)
        request_kwargs["headers"] = self._platform_headers(request_kwargs["url"], headers)
        # A request that carries keys or extra headers does not follow a redirect: the keys go to the URL asked for only.
        if len(headers) > before or carries_credentials(outgoing):
            request_kwargs["allow_redirects"] = False
        return request_kwargs

    def request(
        self,
        config: RequestConfig,
        response_handler: Optional[ResponseHandler[T, U]] = None,
    ) -> Union[Response, T]:
        """Make an HTTP request, retrying only transport-level failures.

        The network round-trip is the only thing retried. Response parsing runs
        once, after the loop, so a parse/deserialization error (or an HTTP error
        status) does not re-send the request — retrying a non-idempotent POST on a
        parse failure silently duplicates server-side writes.
        """

        url = config.url
        method = config.method.value
        session = getattr(self, "_session", None)
        params = config.params
        # Request preparation and retries can each read the query pairs.
        if isinstance(params, Iterable) and not isinstance(params, (Mapping, str, bytes)):
            params = list(params)
        params = params or {}
        json = config.json or {}
        timeout = config.timeout or self._default_timeout
        files = _replayable_files(config.files) or {}
        data = config.data or {}
        headers = self._platform_headers(url, {**self._default_headers, **(config.headers or {})})
        # One budget of retries for the whole call, its redirect hops included: a hop that fails is sent again only
        # while the call has retries left, as 0.8.1 sent the call again (its redirects included) at most that often.
        failures: list[int] = [0]
        limit = _redirect_limit(session)
        redirects, auth, history = 0, None, []
        while True:
            response = self._judged_send(config, session, method, url, headers, params, json, data, files, timeout,
                                         failures=failures, auth=auth)
            # A 301, 302, 303, 307 or 308 to the origin of the request it answers and of ``config.url`` (scheme, host and
            # port) is followed, as 0.8.1 follows it, and the next hop is judged as any request; any other 3xx answer is
            # an error that names the target's host only (``refuse_redirect``).
            target = same_origin_redirect_target(response, config.url) if response is not None else None
            if target is None:
                break
            redirects += 1
            if redirects > limit:
                import requests

                response.close()
                raise requests.TooManyRedirects(f"Exceeded {limit} redirects.", response=response)
            status = response.status_code
            history.append(response)
            response.close()
            url, method, params = target, _redirect_method(status, method), None  # the target carries its query
            # As ``requests`` sends a redirect: the headers the last request went out with (its authentication's
            # included, which is not run again), the cookies from the session's jar, and the body only for a 307 or 308.
            body = getattr(response.request, "body", None)
            replay = status in (307, 308) and isinstance(body, (bytes, str))
            headers = self._hop_headers(response.request.headers, url, keep_body=status in (307, 308),
                                        files=None if replay else files)
            auth = _keep_prepared_auth
            if status not in (307, 308):
                json = data = files = None
            elif replay:
                json, data, files = None, body, None  # the same bytes and media type go again
        if response is not None and history:
            response.history = history
        if response is not None:
            refuse_redirect(response)
        if response_handler:
            return response_handler.parse(response=response)
        return response

    def _hop_headers(self, sent: Mapping, url: str, *, keep_body: bool, files) -> Dict[str, Optional[str]]:
        headers: Dict[str, Optional[str]] = {
            str(name): value for name, value in sent.items()
            if str(name).lower() not in ("cookie", "content-length", "transfer-encoding")
        }
        extra = getattr(self, "_extra_headers", None)
        if extra is not None:
            try:
                names = {name.lower() for name in extra.names()}
            except ExtraHeadersError:
                names = set()
            headers = {name: value for name, value in headers.items() if name.lower() not in names}
            extra.apply(headers, url)
        if not keep_body or files:
            # A redirect without the body sends no body headers, whatever the session's defaults hold; a multipart
            # body is encoded again with its own boundary.
            headers = {name: value for name, value in headers.items() if name.lower() != "content-type"}
            if not keep_body:
                headers.update({"Content-Type": None, "Content-Length": None, "Transfer-Encoding": None})
        return headers

    def _judged_send(self, config: RequestConfig, session, method: str, url: str, headers: Dict[str, str], params, json,
                     data, files, timeout, *, failures: Optional[list] = None, auth=None) -> Optional[Response]:
        # The headers that go out are what the request holds once the session has added its own headers, its auth and its
        # cookies, and the call's headers have won over them: the prepared request, judged before any byte is sent. The
        # sessions judged are the ones that can send it (``session_chain``): a ``FuturesSession`` hands its requests to the
        # session it wraps, and a session that sends through itself is judged on its own headers.
        judged: list = []
        for each in session_chain(session):
            session_headers = getattr(each, "headers", None)
            if isinstance(session_headers, Mapping):
                judged.extend(header_pairs(session_headers))
        judged.extend((name, value) for name, value in header_pairs(headers) if value is not None)
        if has_callable_auth(session):
            judged.append(("Authorization", ""))  # what a callable auth adds is not known before the send: judged as a key
        for prepared in prepared_headers(session, method, url, headers, params=params):
            judged.extend(header_pairs(prepared))
        built = requests_session_sdk_built(session)  # the SDK's own session sends plain HTTP direct
        chain = [] if built else sending_sessions(session)
        allow = getattr(self, "_allow_insecure_http", None)
        # A caller's session is judged by the proxies it sends through, as ``requests`` picks them for it (its
        # ``proxies``, and the environment while ``trust_env`` is on); a session with ``trust_env=False`` reads no proxy
        # variable, so the environment is not judged for it (0.8.1).
        require_secure_credential_headers(
            url, judged, caller_proxied=not built and requests_session_proxied(session, url), proxies_disabled=True,
            allow_insecure_http=allow,
        )
        if may_add_key_later(chain, url):
            # A response hook or a custom adapter may add a key after this judgement (the 0.8.1 rule): the URL is judged
            # as keyed, and so is a proxy the session that sends it would use; each send is judged as it is made.
            senders = sending_chain(session)
            require_secure_credentials_url(url, allow_insecure_http=allow,
                                           caller_proxied=senders is None or proxy_selected(senders[-1:], url),
                                           proxies_disabled=True)
        with judging_sends(chain, allow):
            return self._send_with_retries(config, url, headers, params, json, data, files, timeout, method=method,
                                           failures=failures, auth=auth)

    def _send_with_retries(self, config: RequestConfig, url: str, headers: Dict[str, str], params, json, data, files,
                           timeout, *, method: Optional[str] = None, failures: Optional[list] = None,
                           auth=None) -> Optional[Response]:
        response: Optional[Response] = None
        failures = [0] if failures is None else failures
        extra = {} if auth is None else {"auth": auth}
        while failures[0] < config.retry_attempts:
            try:
                sent = self._session.request(
                    method=method or config.method.value,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    timeout=timeout,
                    allow_redirects=False,
                    **extra,
                )
                # A ``FuturesSession`` answers with a future; a plain ``requests.Session`` answers with the response.
                wait = getattr(sent, "result", None)
                response = wait() if callable(wait) else sent
                break
            except KeyedRedirectRefusedError:
                # A refused redirect is an answer, not a transient failure: the request is not sent again.
                raise
            except Exception as exc:
                # A key refusal (a send a response hook made, judged as it was made) is not sent again either, and
                # neither is a request the server answered: an error raised while reading the answer (a body cut
                # short, a Location header that cannot be read) comes after the keys reached the server.
                failures[0] += 1
                if failures[0] >= config.retry_attempts or _is_key_refusal(exc) or not _before_answer(exc):
                    raise
                time.sleep(config.retry_delay)
        return response

    def close(self):
        """Close the client session"""
        self._session.close()


_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


def _before_answer(exc: BaseException) -> bool:
    """Whether ``exc`` is a connection failure or a timeout, the failures a retry is for."""
    import requests

    if isinstance(exc, (requests.exceptions.ChunkedEncodingError, requests.exceptions.ContentDecodingError)):
        return False
    return isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout, ConnectionError, TimeoutError))


def _is_key_refusal(exc: BaseException) -> bool:
    from fi.errors import InsecureHttpRefusedError, KeyedProxyRefusedError

    return isinstance(exc, (InsecureHttpRefusedError, KeyedProxyRefusedError)) or (
        getattr(exc, "code", None) == "insecure_http_origin"
    )


def refuse_redirect(response: Response) -> None:
    """Raise ``KeyedRedirectRefusedError`` for a 3xx answer to a request that carries the keys: it was not followed, so
    the keys went to the requested URL only. The error names the target's host, not its path, query or user info."""
    if response.status_code in _REDIRECT_STATUSES:
        raise KeyedRedirectRefusedError(
            f"The server answered {response.status_code} with a redirect; the request was not repeated, so the keys went to the requested URL only.",
            status_code=response.status_code,
            target_host=_redirect_host(response),
        )


MAX_REDIRECTS = 5  # a sixth redirect in a row raises requests.TooManyRedirects
_BODY_HEADERS = frozenset({"content-length", "content-type", "transfer-encoding"})


def _redirect_method(status: int, method: str) -> str:
    """The method ``requests`` sends a redirect with: 303 and 302 as ``GET`` (``HEAD`` stays), 301 ``POST`` as ``GET``."""
    if (status in (302, 303) and method != "HEAD") or (status == 301 and method == "POST"):
        return "GET"
    return method


def _keep_prepared_auth(request):
    """The authentication of a followed redirect hop: the headers the last request went out with already hold what the
    session's authentication added, so it is not run again (as ``requests`` sends a redirect)."""
    return request


def _redirect_limit(session) -> int:
    """At most five redirects in a row, or fewer when the session that sends allows fewer (``max_redirects``)."""
    senders = sending_chain(session) or [session]
    value = getattr(senders[-1], "max_redirects", MAX_REDIRECTS)
    return min(MAX_REDIRECTS, value) if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else MAX_REDIRECTS


def _replayable_files(files):
    """``files`` with each open file read into bytes, so a 307 or 308 sends the same content again."""
    if not files:
        return files

    def read(value):
        if isinstance(value, tuple) and len(value) >= 2 and hasattr(value[1], "read"):
            return (value[0], value[1].read(), *value[2:])
        if hasattr(value, "read"):
            name = getattr(value, "name", None)
            return (os.path.basename(name) if isinstance(name, str) else None, value.read())
        return value

    if isinstance(files, Mapping):
        return {field: read(value) for field, value in files.items()}
    return [(field, read(value)) for field, value in files]


def _redirect_host(response: Response) -> Optional[str]:
    """The host a redirect names (not its path, query or user info), else ``None``."""
    from urllib.parse import urlsplit

    try:
        return urlsplit(str(response.headers.get("Location") or "")).hostname
    except ValueError:
        return None


def _guard_redirects(session, extra: ExtraHeaders) -> None:
    """On a redirect ``requests`` keeps custom headers for any host and drops ``Proxy-Authorization``
    even on the same host. So: a redirect off the base URL loses every extra header, and one that
    stays under it gets them back."""
    original = getattr(session, "rebuild_auth", None)
    if original is None:
        return

    def rebuild_auth(prepared_request, response):
        original(prepared_request, response)
        if on_platform(prepared_request.url, extra.base_url):
            extra.apply(prepared_request.headers, prepared_request.url)
            return
        try:
            names = extra.names()
        except ExtraHeadersError:
            names = []
        for name in names:
            prepared_request.headers.pop(name, None)

    session.rebuild_auth = rebuild_auth


class _InstanceCredential:
    """Value-free class access; instance attributes shadow this non-data descriptor."""

    def __get__(self, instance, owner=None) -> Optional[str]:
        if instance is None:
            warnings.warn(
                "Class-level credential access is deprecated; read credentials from the client instance.",
                DeprecationWarning,
                stacklevel=2,
            )
        return None


class APIKeyAuth(HttpClient):
    _fi_api_key = _InstanceCredential()
    _fi_secret_key = _InstanceCredential()

    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ):
        # One resolver for every platform module (fi._credentials): arguments, then the
        # environment, then one saved login whose keys are bound to its base URL.
        creds = resolve_credentials(fi_api_key, fi_secret_key, fi_base_url)
        # Credentials stay on the instance, including for subclasses and the evals registry lookup.
        self._fi_api_key = creds.api_key
        self._fi_secret_key = creds.secret_key
        if self._fi_api_key is None or self._fi_secret_key is None:
            raise MissingAuthError(self._fi_api_key, self._fi_secret_key)

        # a caller's default_headers are kept; the SDK's own keys win over them
        caller_headers = dict(kwargs.pop("default_headers", None) or {})
        for name in [k for k in caller_headers if str(k).lower() in ("x-api-key", "x-secret-key")]:
            del caller_headers[name]
        super().__init__(
            base_url=fi_base_url or (creds.base_url if creds.base_url_source == "login" else None),
            default_headers={
                **caller_headers,
                "X-Api-Key": self._fi_api_key,
                "X-Secret-Key": self._fi_secret_key,
            },
            **kwargs,
        )


class APIKeyManager(APIKeyAuth):
    """Process-scoped singleton with environment-derived provider keys and
    environment- or login-derived client credentials, and is not a per-tenant store.
    ``set_api_key`` changes provider keys for the whole process. For per-tenant
    credentials, use a separate ``APIKeyAuth`` client instance for each tenant.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    @property
    def url(self) -> str:
        return get_base_url() + "/model_hub/api-keys"

    @property
    def headers(self) -> dict:
        return {
            "X-Api-Key": self._fi_api_key,
            "X-Secret-Key": self._fi_secret_key,
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
        """Set a provider key for the whole process, not for a single tenant.
        For per-tenant credentials, use a separate ``APIKeyAuth`` client instance
        for each tenant.
        """
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
