import os
import time
import warnings
from abc import ABC, abstractmethod
from typing import Dict, Generic, Optional, TypeVar, Union
from urllib.parse import urljoin, urlsplit

from requests import Response, sessions
from requests_futures.sessions import FuturesSession

from fi._extra_headers import ExtraHeaders, ExtraHeadersError, ExtraHeadersInput, on_platform
from fi.api.types import HttpMethod, RequestConfig
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
_SDK_AUTH_HEADERS = ("x-api-key", "x-secret-key")
_AUTH_HEADERS = (*_SDK_AUTH_HEADERS, "authorization", "proxy-authorization")


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
    any other URL, and a redirect to one, never gets them (``fi._extra_headers``)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        session: Optional[FuturesSession] = None,
        default_headers: Optional[Dict[str, str]] = None,
        extra_headers: ExtraHeadersInput = None,
        **kwargs,
    ):
        self._base_url = base_url.rstrip("/") if base_url else get_base_url().rstrip("/")
        self._session = session or FuturesSession(
            executor=BoundedExecutor(
                bound=kwargs.get("max_queue", DEFAULT_MAX_QUEUE),
                max_workers=kwargs.get("max_workers", DEFAULT_MAX_WORKERS),
            ),
        )
        self._default_headers = default_headers or {}
        self._default_timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)
        self._extra_headers = ExtraHeaders(self._base_url, extra_headers)
        _guard_redirects(self._session, self._extra_headers)

    def _platform_headers(self, url: str, headers: Dict[str, str]) -> Dict[str, str]:
        """``headers`` plus the extra headers for ``url`` (none off the base URL); for the few
        modules that send with ``requests`` directly (file uploads)."""
        extra = getattr(self, "_extra_headers", None)  # a subclass that skipped __init__ sends none
        if extra is not None:
            extra.apply(headers, url)
        return headers

    def _direct_kwargs(self, request_kwargs: Dict) -> Dict:
        """Arguments for a one-off call (file uploads), including its platform headers.

        Credential-bearing calls follow only same-origin redirects, using requests' method/body
        rules. Disable unguarded following and let a response hook resolve the permitted hops.
        """
        headers = dict(request_kwargs.get("headers") or {})
        before = len(headers)
        request_kwargs["headers"] = self._platform_headers(request_kwargs["url"], headers)
        if len(headers) > before or any(name.lower() in _AUTH_HEADERS for name in headers):
            if request_kwargs.get("allow_redirects", True):
                extra = getattr(self, "_extra_headers", None) or ExtraHeaders(request_kwargs["url"])
                hooks = dict(request_kwargs.get("hooks") or {})
                response_hooks = hooks.get("response") or []
                if callable(response_hooks):
                    response_hooks = [response_hooks]
                hooks["response"] = [*response_hooks, _direct_redirects(extra)]
                request_kwargs["hooks"] = hooks
            request_kwargs["allow_redirects"] = False
        return request_kwargs

    def request(
        self,
        config: RequestConfig,
        response_handler: Optional[ResponseHandler[T, U]] = None,
    ) -> Union[Response, T]:
        """Make an HTTP request, retrying transport failures for idempotent methods.

        POST and PATCH failures propagate without replay: the server may have
        applied the write before its response was lost. GET, PUT and DELETE keep
        the configured attempt budget. Response parsing runs once, outside the
        loop, so HTTP errors and parse failures never re-send a request.
        """

        url = config.url
        headers = self._platform_headers(url, {**self._default_headers, **(config.headers or {})})
        params = config.params or {}
        json = config.json or {}
        timeout = config.timeout or self._default_timeout
        files = config.files or {}
        data = config.data or {}
        response: Optional[Response] = None
        for attempt in range(config.retry_attempts):
            try:
                response = self._session.request(
                    method=config.method.value,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    timeout=timeout,
                ).result()
                break
            except Exception:
                if config.method not in (HttpMethod.GET, HttpMethod.PUT, HttpMethod.DELETE):
                    raise
                if attempt == config.retry_attempts - 1:
                    raise
                time.sleep(config.retry_delay)

        if response_handler:
            return response_handler.parse(response=response)
        return response

    def close(self):
        """Close the client session"""
        self._session.close()


def _redirect_origin(url: str) -> tuple:
    """Compare scheme, hostname and effective port, independent of the base path."""
    parts = urlsplit(url)
    port = parts.port
    if port is None:
        port = 443 if parts.scheme == "https" else 80
    return parts.scheme, parts.hostname, port


def _direct_redirects(extra: ExtraHeaders):
    """Follow safe one-off redirects without changing the legacy upload call sites."""
    def follow(response, **kwargs):
        if not response.is_redirect:
            return response
        with sessions.Session() as session:
            original_target = session.get_redirect_target

            def same_origin_target(current):
                target = original_target(current)
                if target and _redirect_origin(urljoin(current.url, target)) == _redirect_origin(extra.base_url):
                    return target
                return None

            session.get_redirect_target = same_origin_target
            _guard_redirects(session, extra)
            request = response.request.copy()
            # Keep caller hooks on each hop, but do not recursively resolve redirects ourselves.
            request.hooks = {**request.hooks, "response": [
                hook for hook in request.hooks.get("response", []) if hook is not follow
            ]}
            history = list(session.resolve_redirects(response, request, **kwargs))
            if history:
                history.insert(0, response)
                response = history.pop()
                response.history = history
            return response

    return follow


def _guard_redirects(session, extra: ExtraHeaders) -> None:
    """Strip authentication headers when a redirect leaves the configured origin.

    ``requests`` keeps custom headers across origins and drops ``Proxy-Authorization`` even on
    the same host. Extra headers retain their stricter base-path scope and are restored only there.
    """
    original = getattr(session, "rebuild_auth", None)
    if original is None:
        return

    def rebuild_auth(prepared_request, response):
        original(prepared_request, response)
        same_origin = _redirect_origin(prepared_request.url) == _redirect_origin(extra.base_url)
        if not same_origin:
            for name in _AUTH_HEADERS:
                prepared_request.headers.pop(name, None)
        if same_origin and on_platform(prepared_request.url, extra.base_url):
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
    environment- or login-derived client credentials, never a per-tenant store.
    ``set_api_key`` changes provider keys for the whole process; credential
    isolation applies only to separate ``APIKeyAuth`` client instances.
    Behaviour is unchanged in 0.7.0; deprecation is planned for 0.7.x.
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
        """Set a provider key for the whole process, never for a single tenant.
        This process-scoped manager is not a per-tenant store; credential isolation
        applies only to separate ``APIKeyAuth`` client instances.
        Behaviour is unchanged in 0.7.0; deprecation is planned for 0.7.x.
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
