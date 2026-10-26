"""`Client` / `AsyncClient`: one config, every resource hangs off it.

Extending the client
    - Add methods to a resource in `fi/platform/resources/<name>.py` (hand-written, never regenerated).
    - Swap or add a resource class: `class MyClient(Client): _resources = {**Client._resources, "datasets": MyDatasets}`.
    - Call an endpoint the catalog lacks: `client.request("GET", "/some/path/", query={...})`.
    - Per call: `client.datasets.get(id, options=RequestOptions(timeout=5, headers={...}))`.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping

import httpx

from fi.utils.constants import API_KEY_ENVVAR_NAME, SECRET_KEY_ENVVAR_NAME, get_base_url

from ._transport import AsyncTransport, Config, FileInput, RequestOptions, SyncTransport
from .resources import AsyncResources, Resources


def _config(api_key, secret_key, base_url, timeout, max_retries, workspace_id, strict_responses, default_headers) -> Config:
    api_key = api_key or os.environ.get(API_KEY_ENVVAR_NAME)
    secret_key = secret_key or os.environ.get(SECRET_KEY_ENVVAR_NAME)
    if not api_key or not secret_key:
        raise ValueError(f"pass api_key= and secret_key=, or set {API_KEY_ENVVAR_NAME} and {SECRET_KEY_ENVVAR_NAME}")
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")
    return Config(
        api_key=api_key,
        secret_key=secret_key,
        base_url=(base_url or get_base_url()).rstrip("/"),
        timeout=timeout,
        max_retries=max_retries,
        workspace_id=workspace_id or os.environ.get("FI_WORKSPACE_ID"),
        strict_responses=strict_responses,
        default_headers=dict(default_headers) if default_headers else None,
    )


class Client(Resources):
    """Future AGI platform client.

        from fi.platform import Client
        client = Client()                      # FI_API_KEY / FI_SECRET_KEY / FI_BASE_URL
        for ds in client.datasets.list():
            print(ds.name)
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
    ) -> None:
        self._transport = SyncTransport(
            _config(api_key, secret_key, base_url, timeout, max_retries, workspace_id, strict_responses, default_headers), http_client
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
        options: RequestOptions | None = None,
    ) -> Any:
        """Call any endpoint under the base URL with the client's auth, retries and errors.

        For endpoints the catalog does not describe yet. Returns the decoded JSON with the
        `unwrap` key (the backend's `{status, result}` envelope) removed when present.
        """
        return self._transport.raw(method, path, query=query, body=body, files=files, unwrap=unwrap, multipart=multipart, options=options)

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
    ) -> None:
        self._transport = AsyncTransport(
            _config(api_key, secret_key, base_url, timeout, max_retries, workspace_id, strict_responses, default_headers), http_client
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
        options: RequestOptions | None = None,
    ) -> Any:
        """See `Client.request`."""
        return await self._transport.raw(method, path, query=query, body=body, files=files, unwrap=unwrap, multipart=multipart, options=options)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()
