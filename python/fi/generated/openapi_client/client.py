import ssl
from typing import Any

import httpx
from attrs import define, evolve, field

from fi._core.http_security import (
    httpx_client_proxied,
    httpx_client_sdk_built,
    require_secure_credentials_url,
)
from fi._core.proxy_routing import SdkDirectAsyncTransport, SdkDirectTransport


@define
class Client:
    """A class for keeping track of data related to the API

    The following are accepted as keyword arguments and will be used to construct httpx Clients internally:

        ``base_url``: The base URL for the API, all requests are made to a relative path to this URL

        ``cookies``: A dictionary of cookies to be sent with every request

        ``headers``: A dictionary of headers to be sent with every request

        ``timeout``: The maximum amount of a time a request can take. API functions will raise
        httpx.TimeoutException if this is exceeded.

        ``verify_ssl``: Whether or not to verify the SSL certificate of the API server. This should be True in production,
        but can be set to False for testing purposes.

        ``follow_redirects``: Whether or not to follow redirects. Default value is False.

        ``httpx_args``: A dictionary of additional arguments to be passed to the ``httpx.Client`` and ``httpx.AsyncClient`` constructor.


    Attributes:
        raise_on_unexpected_status: Whether or not to raise an errors.UnexpectedStatus if the API returns a
            status code that was not documented in the source OpenAPI document. Can also be provided as a keyword
            argument to the constructor.
    """

    raise_on_unexpected_status: bool = field(default=False, kw_only=True)
    _base_url: str = field(alias="base_url")
    _cookies: dict[str, str] = field(factory=dict, kw_only=True, alias="cookies")
    _headers: dict[str, str] = field(factory=dict, kw_only=True, alias="headers")
    _timeout: httpx.Timeout | None = field(default=None, kw_only=True, alias="timeout")
    _verify_ssl: str | bool | ssl.SSLContext = field(
        default=True, kw_only=True, alias="verify_ssl"
    )
    _follow_redirects: bool = field(
        default=False, kw_only=True, alias="follow_redirects"
    )
    _httpx_args: dict[str, Any] = field(factory=dict, kw_only=True, alias="httpx_args")
    _client: httpx.Client | None = field(default=None, init=False)
    _async_client: httpx.AsyncClient | None = field(default=None, init=False)

    def _off_origin_httpx_args(self, hook: Any) -> dict[str, Any]:
        """The caller's ``httpx_args`` with ``hook`` run after the caller's own request ``event_hooks``"""
        hooks = dict(self._httpx_args.get("event_hooks") or {})
        hooks["request"] = [*hooks.get("request", ()), hook]
        return {**self._httpx_args, "event_hooks": hooks}

    def _drop_credentials_off_origin(self, request: httpx.Request) -> None:
        """Remove ``Authorization``, ``Cookie``, ``X-Api-Key`` and ``X-Secret-Key`` from a request to an origin other
        than ``base_url``'s (scheme, host or port differ), such as the target of a followed redirect: httpx removes
        only ``Authorization`` there, and sends the cookies of ``cookies=`` to any host. A client of the caller's
        (``set_httpx_client``, ``set_async_httpx_client``) sends as the caller built it"""
        ports = {"http": 80, "https": 443}
        base, url = httpx.URL(self._base_url), request.url
        if (url.scheme, url.host, url.port or ports.get(url.scheme)) != (
            base.scheme,
            base.host,
            base.port or ports.get(base.scheme),
        ):
            for name in ("Authorization", "Cookie", "X-Api-Key", "X-Secret-Key"):
                request.headers.pop(name, None)

    async def _drop_credentials_off_origin_async(self, request: httpx.Request) -> None:
        """The request event hook of the ``httpx.AsyncClient``; see ``_drop_credentials_off_origin``"""
        self._drop_credentials_off_origin(request)

    def with_headers(self, headers: dict[str, str]) -> "Client":
        """Get a new client matching this one with additional headers"""
        if self._client is not None:
            self._client.headers.update(headers)
        if self._async_client is not None:
            self._async_client.headers.update(headers)
        return evolve(self, headers={**self._headers, **headers})

    def with_cookies(self, cookies: dict[str, str]) -> "Client":
        """Get a new client matching this one with additional cookies"""
        if self._client is not None:
            self._client.cookies.update(cookies)
        if self._async_client is not None:
            self._async_client.cookies.update(cookies)
        return evolve(self, cookies={**self._cookies, **cookies})

    def with_timeout(self, timeout: httpx.Timeout) -> "Client":
        """Get a new client matching this one with a new timeout configuration"""
        if self._client is not None:
            self._client.timeout = timeout
        if self._async_client is not None:
            self._async_client.timeout = timeout
        return evolve(self, timeout=timeout)

    def set_httpx_client(self, client: httpx.Client) -> "Client":
        """Manually set the underlying httpx.Client

        **NOTE**: This will override any other settings on the client, including cookies, headers, and timeout.
        """
        self._client = client
        return self

    def get_httpx_client(self) -> httpx.Client:
        """Get the underlying httpx.Client, constructing a new one if not previously set"""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._base_url,
                cookies=self._cookies,
                headers=self._headers,
                timeout=self._timeout,
                verify=self._verify_ssl,
                follow_redirects=self._follow_redirects,
                **self._off_origin_httpx_args(self._drop_credentials_off_origin),
            )
        return self._client

    def __enter__(self) -> "Client":
        """Enter a context manager for self.client—you cannot enter twice (see httpx docs)"""
        self.get_httpx_client().__enter__()
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit a context manager for internal httpx.Client (see httpx docs)"""
        self.get_httpx_client().__exit__(*args, **kwargs)

    def set_async_httpx_client(self, async_client: httpx.AsyncClient) -> "Client":
        """Manually set the underlying httpx.AsyncClient

        **NOTE**: This will override any other settings on the client, including cookies, headers, and timeout.
        """
        self._async_client = async_client
        return self

    def get_async_httpx_client(self) -> httpx.AsyncClient:
        """Get the underlying httpx.AsyncClient, constructing a new one if not previously set"""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url,
                cookies=self._cookies,
                headers=self._headers,
                timeout=self._timeout,
                verify=self._verify_ssl,
                follow_redirects=self._follow_redirects,
                **self._off_origin_httpx_args(self._drop_credentials_off_origin_async),
            )
        return self._async_client

    async def __aenter__(self) -> "Client":
        """Enter a context manager for underlying httpx.AsyncClient—you cannot enter twice (see httpx docs)"""
        await self.get_async_httpx_client().__aenter__()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit a context manager for underlying httpx.AsyncClient (see httpx docs)"""
        await self.get_async_httpx_client().__aexit__(*args, **kwargs)


@define
class AuthenticatedClient:
    """A Client which has been authenticated for use on secured endpoints

    The following are accepted as keyword arguments and will be used to construct httpx Clients internally:

        ``base_url``: The base URL for the API, all requests are made to a relative path to this URL

        ``cookies``: A dictionary of cookies to be sent with every request

        ``headers``: A dictionary of headers to be sent with every request

        ``timeout``: The maximum amount of a time a request can take. API functions will raise
        httpx.TimeoutException if this is exceeded.

        ``verify_ssl``: Whether or not to verify the SSL certificate of the API server. This should be True in production,
        but can be set to False for testing purposes.

        ``follow_redirects``: Whether or not to follow redirects. Default value is False.

        ``httpx_args``: A dictionary of additional arguments to be passed to the ``httpx.Client`` and ``httpx.AsyncClient`` constructor.


    Attributes:
        raise_on_unexpected_status: Whether or not to raise an errors.UnexpectedStatus if the API returns a
            status code that was not documented in the source OpenAPI document. Can also be provided as a keyword
            argument to the constructor.
        token: The token to use for authentication
        prefix: The prefix to use for the Authorization header
        auth_header_name: The name of the Authorization header
    """

    raise_on_unexpected_status: bool = field(default=False, kw_only=True)
    _base_url: str = field(alias="base_url")
    _cookies: dict[str, str] = field(factory=dict, kw_only=True, alias="cookies")
    _headers: dict[str, str] = field(factory=dict, kw_only=True, alias="headers")
    _timeout: httpx.Timeout | None = field(default=None, kw_only=True, alias="timeout")
    _verify_ssl: str | bool | ssl.SSLContext = field(
        default=True, kw_only=True, alias="verify_ssl"
    )
    _follow_redirects: bool = field(
        default=False, kw_only=True, alias="follow_redirects"
    )
    _httpx_args: dict[str, Any] = field(factory=dict, kw_only=True, alias="httpx_args")
    _client: httpx.Client | None = field(default=None, init=False)
    _async_client: httpx.AsyncClient | None = field(default=None, init=False)

    token: str
    prefix: str = "Bearer"
    auth_header_name: str = "Authorization"

    def _token_httpx_args(self, direct: type, hook: Any) -> dict[str, Any]:
        """The caller's ``httpx_args`` with ``hook`` run after the caller's own request ``event_hooks``; with no
        transport, proxy or mounts of the caller's, plain http goes direct with the environment's proxy variables off,
        as the SDK's own clients send it (``fi._core.proxy_routing``)"""
        hooks = dict(self._httpx_args.get("event_hooks") or {})
        hooks["request"] = [*hooks.get("request", ()), hook]
        httpx_args = {**self._httpx_args, "event_hooks": hooks}
        if any(httpx_args.get(name) for name in ("transport", "proxy", "mounts")):
            return httpx_args
        return {**httpx_args, "mounts": {"http://": direct()}}

    def _drop_token_off_origin(self, request: httpx.Request) -> None:
        """Remove the token header, ``Authorization``, ``Cookie``, ``X-Api-Key`` and ``X-Secret-Key`` from a request to
        an origin other than ``base_url``'s (scheme, host or port differ), such as the target of a followed redirect:
        httpx removes only ``Authorization`` there, and sends the cookies of ``cookies=`` to any host"""
        ports = {"http": 80, "https": 443}
        base, url = httpx.URL(self._base_url), request.url
        if (url.scheme, url.host, url.port or ports.get(url.scheme)) != (
            base.scheme,
            base.host,
            base.port or ports.get(base.scheme),
        ):
            for name in {self.auth_header_name, "Authorization", "Cookie", "X-Api-Key", "X-Secret-Key"}:
                request.headers.pop(name, None)

    def _headers_without_token(self, headers: Any) -> dict[Any, Any]:
        """``headers`` less each credential header: a header named ``auth_header_name``, ``Authorization``, ``Cookie``,
        ``X-Api-Key`` or ``X-Secret-Key`` in any case, by a ``str`` name or a ``bytes`` name (read as latin-1, as httpx
        reads it). httpx sends both of two names that differ in case only, so headers copied from another client (its
        httpx ``headers``, or a dict of them or of their ``.raw`` pairs) would send that client's token, cookie or keys
        next to this client's own token"""
        names = {self.auth_header_name.lower(), "authorization", "cookie", "x-api-key", "x-secret-key"}
        return {
            name: value
            for name, value in headers.items()
            if (name.decode("latin-1") if isinstance(name, bytes) else name).lower() not in names
        }

    async def _drop_token_off_origin_async(self, request: httpx.Request) -> None:
        """The request event hook of the ``httpx.AsyncClient``; see ``_drop_token_off_origin``"""
        self._drop_token_off_origin(request)

    def _refuse_plain_http_token(self, client: httpx.Client | httpx.AsyncClient) -> None:
        """Refuse the token over plain http the way the rest of the SDK does (``fi._core.http_security``): a client
        built here sends it to loopback direct, a proxy of the caller's transport, proxy or mounts is refused, and so
        is a remote host the environment's proxy variables route"""
        built = httpx_client_sdk_built(client, self._base_url)
        require_secure_credentials_url(
            self._base_url,
            setting="base_url",
            caller_proxied=not built and httpx_client_proxied(client, self._base_url),
        )

    def with_headers(self, headers: dict[str, str]) -> "AuthenticatedClient":
        """Get a new client matching this one with additional headers"""
        if self._client is not None:
            self._client.headers.update(self._headers_without_token(headers))
        if self._async_client is not None:
            self._async_client.headers.update(self._headers_without_token(headers))
        return evolve(self, headers={**self._headers, **headers})

    def with_cookies(self, cookies: dict[str, str]) -> "AuthenticatedClient":
        """Get a new client matching this one with additional cookies"""
        if self._client is not None:
            self._client.cookies.update(cookies)
        if self._async_client is not None:
            self._async_client.cookies.update(cookies)
        return evolve(self, cookies={**self._cookies, **cookies})

    def with_timeout(self, timeout: httpx.Timeout) -> "AuthenticatedClient":
        """Get a new client matching this one with a new timeout configuration"""
        if self._client is not None:
            self._client.timeout = timeout
        if self._async_client is not None:
            self._async_client.timeout = timeout
        return evolve(self, timeout=timeout)

    def set_httpx_client(self, client: httpx.Client) -> "AuthenticatedClient":
        """Manually set the underlying httpx.Client

        **NOTE**: This will override any other settings on the client, including cookies, headers, and timeout.
        """
        self._client = client
        return self

    def get_httpx_client(self) -> httpx.Client:
        """Get the underlying httpx.Client, constructing a new one if not previously set"""
        if self._client is None:
            httpx_args = self._token_httpx_args(SdkDirectTransport, self._drop_token_off_origin)
            headers = {
                **self._headers_without_token(self._headers),
                self.auth_header_name: (
                    f"{self.prefix} {self.token}" if self.prefix else self.token
                ),
            }
            client = httpx.Client(
                base_url=self._base_url,
                cookies=self._cookies,
                headers=headers,
                timeout=self._timeout,
                verify=self._verify_ssl,
                follow_redirects=self._follow_redirects,
                **httpx_args,
            )
            self._refuse_plain_http_token(client)
            self._client = client
        return self._client

    def __enter__(self) -> "AuthenticatedClient":
        """Enter a context manager for self.client—you cannot enter twice (see httpx docs)"""
        self.get_httpx_client().__enter__()
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit a context manager for internal httpx.Client (see httpx docs)"""
        self.get_httpx_client().__exit__(*args, **kwargs)

    def set_async_httpx_client(
        self, async_client: httpx.AsyncClient
    ) -> "AuthenticatedClient":
        """Manually set the underlying httpx.AsyncClient

        **NOTE**: This will override any other settings on the client, including cookies, headers, and timeout.
        """
        self._async_client = async_client
        return self

    def get_async_httpx_client(self) -> httpx.AsyncClient:
        """Get the underlying httpx.AsyncClient, constructing a new one if not previously set"""
        if self._async_client is None:
            httpx_args = self._token_httpx_args(SdkDirectAsyncTransport, self._drop_token_off_origin_async)
            headers = {
                **self._headers_without_token(self._headers),
                self.auth_header_name: (
                    f"{self.prefix} {self.token}" if self.prefix else self.token
                ),
            }
            client = httpx.AsyncClient(
                base_url=self._base_url,
                cookies=self._cookies,
                headers=headers,
                timeout=self._timeout,
                verify=self._verify_ssl,
                follow_redirects=self._follow_redirects,
                **httpx_args,
            )
            self._refuse_plain_http_token(client)
            self._async_client = client
        return self._async_client

    async def __aenter__(self) -> "AuthenticatedClient":
        """Enter a context manager for underlying httpx.AsyncClient—you cannot enter twice (see httpx docs)"""
        await self.get_async_httpx_client().__aenter__()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit a context manager for underlying httpx.AsyncClient (see httpx docs)"""
        await self.get_async_httpx_client().__aexit__(*args, **kwargs)
