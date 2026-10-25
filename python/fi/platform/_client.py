"""`Client` / `AsyncClient`: one config, every resource hangs off it."""

from __future__ import annotations

import os

import httpx

from ._generated.resources import AsyncGeneratedResources, GeneratedResources
from ._transport import AsyncTransport, Config, SyncTransport

DEFAULT_BASE_URL = "https://api.futureagi.com"


def _config(api_key, secret_key, base_url, timeout, max_retries, workspace_id, strict_responses) -> Config:
    api_key = api_key or os.environ.get("FI_API_KEY")
    secret_key = secret_key or os.environ.get("FI_SECRET_KEY")
    if not api_key or not secret_key:
        raise ValueError("pass api_key= and secret_key=, or set FI_API_KEY and FI_SECRET_KEY")
    return Config(
        api_key=api_key,
        secret_key=secret_key,
        base_url=(base_url or os.environ.get("FI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/"),
        timeout=timeout,
        max_retries=max_retries,
        workspace_id=workspace_id or os.environ.get("FI_WORKSPACE_ID"),
        strict_responses=strict_responses,
    )


class Client(GeneratedResources):
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
        http_client: httpx.Client | None = None,
    ) -> None:
        self._transport = SyncTransport(
            _config(api_key, secret_key, base_url, timeout, max_retries, workspace_id, strict_responses), http_client
        )
        self._init_resources(self._transport)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class AsyncClient(AsyncGeneratedResources):
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
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._transport = AsyncTransport(
            _config(api_key, secret_key, base_url, timeout, max_retries, workspace_id, strict_responses), http_client
        )
        self._init_resources(self._transport)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()
