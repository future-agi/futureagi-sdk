"""`Client` / `AsyncClient`: one config, every resource hangs off it.

Extending the client
    - Add methods to a resource in `fi/platform/resources/<name>.py` (hand-written, not regenerated).
    - Swap or add a resource class: `class MyClient(Client): _resources = {**Client._resources, "datasets": MyDatasets}`.
    - Call an endpoint the catalog lacks: `client.request("GET", "/some/path/", query={...})`.
    - Per call: `client.datasets.get(id, options=RequestOptions(timeout=5, headers={...}))`.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping

import httpx

from fi._core.http_security import _written_host, future_agi_connect_host
from fi._credentials import MissingAuthError
from fi._credentials import resolve as resolve_credentials
from fi.errors import ConfigurationError, InsecureHttpRefusedError
from fi.utils.constants import get_base_url

from ._transport import AsyncTransport, Config, FileInput, RequestOptions, SyncTransport
from .resources import AsyncResources, Resources


def _key_pair(api_key: str | None, secret_key: str | None, base_url: str) -> tuple[str, str]:
    """The key pair for `base_url`, resolved as one unit by `fi._credentials`.

    Both keys come from the arguments, or (when neither argument is given) both from
    `FI_API_KEY` / `FI_SECRET_KEY`, then the saved login bound to `base_url`. A pair with a
    missing or empty key raises `fi.errors.MissingAuthError` before any request.
    """
    creds = resolve_credentials(api_key, secret_key, base_url)
    if not creds.complete:
        raise MissingAuthError(
            creds.api_key or None,
            creds.secret_key or None,
            base_url=creds.base_url,
            login_skipped=creds.login_skipped,
        )
    return str(creds.api_key), str(creds.secret_key)


def _check_written_base_url(base_url: str) -> None:
    """Refuse a plain ``http://`` base URL with a backslash anywhere in it, or a host written with an ideographic,
    fullwidth or halfwidth full stop, before any credential is read: ``InsecureHttpRefusedError`` for a Future AGI
    host, else ``ConfigurationError`` (code ``insecure_http_origin``), with or without ``FI_ALLOW_INSECURE_HTTP=1``."""
    if not base_url.strip().lower().startswith("http://"):
        return
    written_host = _written_host(base_url)
    if "\\" not in base_url and not any(dot in written_host for dot in "。．｡"):
        return
    if host := future_agi_connect_host(base_url):
        raise InsecureHttpRefusedError(host)
    raise ConfigurationError(
        "A plain http:// platform base URL must write its host with ASCII dots and hold no backslash "
        "(insecure_http_origin)",
        code="insecure_http_origin",
    )


def _config(
    api_key, secret_key, base_url, timeout, max_retries, workspace_id, strict_responses, default_headers,
    allow_insecure_http: bool | None,
) -> Config:
    base_url = (base_url or get_base_url()).rstrip("/")
    _check_written_base_url(base_url)
    api_key, secret_key = _key_pair(api_key, secret_key, base_url)
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")
    return Config(
        api_key=api_key,
        secret_key=secret_key,
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        workspace_id=workspace_id or os.environ.get("FI_WORKSPACE_ID"),
        strict_responses=strict_responses,
        default_headers=dict(default_headers) if default_headers else None,
        allow_insecure_http=None if allow_insecure_http is None else allow_insecure_http is True,
    )


class Client(Resources):
    """Future AGI platform client.

        from fi.platform import Client
        client = Client()                      # FI_API_KEY / FI_SECRET_KEY / FI_BASE_URL
        for ds in client.datasets.list():
            print(ds.name)

    The key pair comes from one place: `api_key=` and `secret_key=` together, or, when neither
    is given, `FI_API_KEY` and `FI_SECRET_KEY` together. One key given without the other (or as
    an empty string), or no pair at all, raises `fi.errors.MissingAuthError` before any request. A plain
    `http://` base URL with a backslash, or with a host written with a non-ASCII full stop, is refused first,
    before the key pair is read.

    `allow_insecure_http=True` opts in to direct plain HTTP for eligible non-loopback hosts outside the
    Future AGI zone. `False` disables the opt-in, and `None` uses `FI_ALLOW_INSECURE_HTTP`.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        secret_key: str | None = None,
        base_url: str | None = None,
        workspace_id: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        strict_responses: bool = False,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
        allow_insecure_http: bool | None = None,
    ) -> None:
        self._transport = SyncTransport(
            _config(
                api_key, secret_key, base_url, timeout, max_retries, workspace_id,
                strict_responses, default_headers, allow_insecure_http,
            ),
            http_client,
        )
        self._init_resources(self._transport)

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Dict[str, Any] | None = None,
        body: Any = None,
        files: Dict[str, FileInput | list] | None = None,
        unwrap: str | None = "result",
        multipart: bool = False,
        decode: str = "json",
        options: RequestOptions | None = None,
    ) -> Any:
        """Call any endpoint under the base URL with the client's auth, retries and errors.

        For endpoints the catalog does not describe yet. Returns the decoded JSON with the
        `unwrap` key (the backend's `{status, result}` envelope) removed when present, or the
        whole body as sent with `unwrap=None`;
        `decode="text"` returns the body as text, `"auto"` does so unless the response is JSON.
        """
        return self._transport.raw(method, path, query=query, body=body, files=files, unwrap=unwrap, multipart=multipart, decode=decode, options=options)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class AsyncClient(AsyncResources):
    """Same API as `Client`, with `await` / `async for`."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        secret_key: str | None = None,
        base_url: str | None = None,
        workspace_id: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        strict_responses: bool = False,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
        allow_insecure_http: bool | None = None,
    ) -> None:
        self._transport = AsyncTransport(
            _config(
                api_key, secret_key, base_url, timeout, max_retries, workspace_id,
                strict_responses, default_headers, allow_insecure_http,
            ),
            http_client,
        )
        self._init_resources(self._transport)

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Dict[str, Any] | None = None,
        body: Any = None,
        files: Dict[str, FileInput | list] | None = None,
        unwrap: str | None = "result",
        multipart: bool = False,
        decode: str = "json",
        options: RequestOptions | None = None,
    ) -> Any:
        """See `Client.request`."""
        return await self._transport.raw(method, path, query=query, body=body, files=files, unwrap=unwrap, multipart=multipart, decode=decode, options=options)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()
