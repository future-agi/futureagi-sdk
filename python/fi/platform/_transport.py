"""The one HTTP layer every resource uses: auth, retries, envelope unwrap, errors."""

from __future__ import annotations

import asyncio
import functools
import random
import time
import warnings
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import TypeAdapter, ValidationError

from ._errors import (
    APIConnectionError,
    ResponseShapeWarning,
    ResponseValidationError,
    error_from_response,
)
from ._pagination import AsyncPager, SyncPager, _get

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
    strict_responses: bool = False

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


def _clean(params: Any) -> Any:
    """Drop unset (None) fields; a non-dict body (e.g. a list) is sent as is."""
    if not isinstance(params, dict):
        return params
    return {k: v for k, v in params.items() if v is not None}


def _decode(op: Operation, response: httpx.Response) -> Any:
    if response.status_code == 204 or not response.content:
        return None
    data = response.json()
    if op.unwrap and isinstance(data, dict) and op.unwrap in data:
        return data[op.unwrap]
    # The backend wraps most successes in {status, result}, but the contract often leaves
    # the envelope out, so unwrap it whenever it is exactly that shape.
    if isinstance(data, dict) and data.keys() == {"status", "result"} and data["status"] is True:
        return data["result"]
    return data


@functools.lru_cache(maxsize=None)
def _adapter(model: Any) -> TypeAdapter:
    return TypeAdapter(model)


def _parse(op: Operation, model: Any, data: Any, strict: bool) -> Any:
    """Validate into the generated model (or `List[model]`); untyped responses pass through.

    A response that does not match the contract never breaks a call by default: the
    caller gets the raw JSON and a ResponseShapeWarning. Tests run strict to catch drift.
    """
    if model is None or data is None:
        return data
    try:
        return _adapter(model).validate_python(data)
    except ValidationError as exc:
        if strict:
            raise ResponseValidationError(op.id, exc, data) from exc
        warnings.warn(f"{op.id}: response does not match the contract; returning raw JSON", ResponseShapeWarning, stacklevel=4)
        return data


def _check_page(op: Operation, data: Any, strict: bool) -> Any:
    """A page without its items list means the contract's page shape is wrong; never
    let that look like an empty result."""
    if isinstance(_get(data, op.pagination["items"]), list):
        return data
    message = f"{op.id}: page has no {op.pagination['items']!r} list"
    if strict:
        raise ResponseValidationError(op.id, ValueError(message), data)
    warnings.warn(message, ResponseShapeWarning, stacklevel=4)
    return data


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
        return _parse(op, model, self.request(op, path=path, query=query, body=body), self.config.strict_responses)

    def paginate(self, op: Operation, *, path=None, query=None, model=None) -> SyncPager:
        spec = op.pagination

        def fetch(page: int) -> Any:
            data = self.request(op, path=path, query={**(query or {}), spec["page_param"]: page})
            return _check_page(op, data, self.config.strict_responses)

        return SyncPager(fetch, spec, lambda item: _parse(op, model, item, self.config.strict_responses))

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
        return _parse(op, model, await self.request(op, path=path, query=query, body=body), self.config.strict_responses)

    def apaginate(self, op: Operation, *, path=None, query=None, model=None) -> AsyncPager:
        spec = op.pagination

        async def fetch(page: int) -> Any:
            data = await self.request(op, path=path, query={**(query or {}), spec["page_param"]: page})
            return _check_page(op, data, self.config.strict_responses)

        return AsyncPager(fetch, spec, lambda item: _parse(op, model, item, self.config.strict_responses))

    async def aclose(self) -> None:
        await self._http.aclose()
