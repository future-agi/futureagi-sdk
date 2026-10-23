"""The one HTTP layer every resource uses: auth, retries, envelope unwrap, errors."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from ._errors import APIConnectionError, error_from_response
from ._pagination import AsyncPager, SyncPager

RETRY_STATUSES = {408, 429, 500, 502, 503, 504}


@dataclass(frozen=True)
class Operation:
    """What generated code passes in for each call (emitted from the catalog)."""

    id: str
    method: str
    path: str
    unwrap: str | None
    pagination: dict | None


@dataclass
class Config:
    api_key: str
    secret_key: str
    base_url: str
    timeout: float
    max_retries: int
    workspace_id: str | None = None

    def headers(self) -> dict[str, str]:
        headers = {
            "X-Api-Key": self.api_key,
            "X-Secret-Key": self.secret_key,
            "User-Agent": "futureagi-python/poc",
        }
        if self.workspace_id:
            headers["X-Workspace-Id"] = self.workspace_id
        return headers


def _url(op: Operation, path: dict | None) -> str:
    url = op.path
    for name, value in (path or {}).items():
        url = url.replace("{" + name + "}", quote(str(value), safe=""))
    return url


def _clean(params: dict | None) -> dict | None:
    if params is None:
        return None
    return {k: v for k, v in params.items() if v is not None}


def _decode(op: Operation, response: httpx.Response) -> Any:
    if response.status_code == 204 or not response.content:
        return None
    data = response.json()
    if op.unwrap and isinstance(data, dict) and op.unwrap in data:
        return data[op.unwrap]
    return data


def _parse(model: Any, data: Any) -> Any:
    if model is None or data is None:
        return data
    return model.model_validate(data)


def _backoff(attempt: int, response: httpx.Response | None) -> float:
    retry_after = response.headers.get("retry-after") if response is not None else None
    if retry_after:
        try:
            return min(float(retry_after), 30.0)
        except ValueError:
            pass
    return min(0.5 * 2**attempt, 8.0) * (0.75 + random.random() / 2)


class SyncTransport:
    def __init__(self, config: Config, http_client: httpx.Client | None = None) -> None:
        self.config = config
        self._http = http_client or httpx.Client()
        self._http.base_url = config.base_url
        self._http.timeout = httpx.Timeout(config.timeout)

    def request(self, op: Operation, *, path=None, query=None, body=None) -> Any:
        url = _url(op, path)
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self._http.request(
                    op.method, url, params=_clean(query), json=_clean(body), headers=self.config.headers()
                )
            except httpx.TransportError as exc:
                if attempt < self.config.max_retries:
                    time.sleep(_backoff(attempt, None))
                    continue
                raise APIConnectionError(str(exc)) from exc
            if response.status_code in RETRY_STATUSES and attempt < self.config.max_retries:
                time.sleep(_backoff(attempt, response))
                continue
            if response.status_code >= 400:
                raise error_from_response(response)
            return _decode(op, response)
        raise AssertionError("unreachable")

    def call(self, op: Operation, *, path=None, query=None, body=None, model=None) -> Any:
        return _parse(model, self.request(op, path=path, query=query, body=body))

    def paginate(self, op: Operation, *, path=None, query=None, model=None) -> SyncPager:
        spec = op.pagination

        def fetch(page: int) -> Any:
            return self.request(op, path=path, query={**(query or {}), spec["page_param"]: page})

        return SyncPager(fetch, spec, lambda item: _parse(model, item))

    def close(self) -> None:
        self._http.close()


class AsyncTransport:
    def __init__(self, config: Config, http_client: httpx.AsyncClient | None = None) -> None:
        self.config = config
        self._http = http_client or httpx.AsyncClient()
        self._http.base_url = config.base_url
        self._http.timeout = httpx.Timeout(config.timeout)

    async def request(self, op: Operation, *, path=None, query=None, body=None) -> Any:
        url = _url(op, path)
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._http.request(
                    op.method, url, params=_clean(query), json=_clean(body), headers=self.config.headers()
                )
            except httpx.TransportError as exc:
                if attempt < self.config.max_retries:
                    await asyncio.sleep(_backoff(attempt, None))
                    continue
                raise APIConnectionError(str(exc)) from exc
            if response.status_code in RETRY_STATUSES and attempt < self.config.max_retries:
                await asyncio.sleep(_backoff(attempt, response))
                continue
            if response.status_code >= 400:
                raise error_from_response(response)
            return _decode(op, response)
        raise AssertionError("unreachable")

    async def acall(self, op: Operation, *, path=None, query=None, body=None, model=None) -> Any:
        return _parse(model, await self.request(op, path=path, query=query, body=body))

    def apaginate(self, op: Operation, *, path=None, query=None, model=None) -> AsyncPager:
        spec = op.pagination

        async def fetch(page: int) -> Any:
            return await self.request(op, path=path, query={**(query or {}), spec["page_param"]: page})

        return AsyncPager(fetch, spec, lambda item: _parse(model, item))

    async def aclose(self) -> None:
        await self._http.aclose()
