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
    APIError,
    ResponseShapeWarning,
    ResponseValidationError,
    error_from_response,
)
from ._pagination import AsyncPager, SyncPager, _get

# 429 means the server did not process the request, so any method may retry it. A
# timeout, a 5xx or a dropped connection may have happened after a write was applied,
# so those are retried only for methods that are safe to repeat.
RETRY_ANY_METHOD = {429}
RETRY_IDEMPOTENT = {408, 500, 502, 503, 504}
IDEMPOTENT_METHODS = {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}


def _can_retry(op: "Operation", status: int | None, attempt: int, max_retries: int) -> bool:
    if attempt >= max_retries:
        return False
    if status is None:  # transport error: the request may have reached the server
        return op.method in IDEMPOTENT_METHODS
    return status in RETRY_ANY_METHOD or (status in RETRY_IDEMPOTENT and op.method in IDEMPOTENT_METHODS)


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
    try:
        data = response.json()
    except ValueError:
        content_type = response.headers.get("content-type", "unknown")
        raise APIError(
            f"{response.status_code} non-JSON response ({content_type})", response=response, body=response.text
        ) from None
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
        # A caller's client is used as given (absolute URLs, per-request timeout) and never
        # closed here; only a client we created is ours to configure and close.
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(follow_redirects=True)

    def request(self, op: Operation, *, path=None, query=None, body=None) -> Any:
        url = self.config.base_url + _url(op, path)
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self._http.request(
                    op.method, url, params=_clean(query), json=_clean(body),
                    headers=self.config.headers(), timeout=self.config.timeout,
                )
            except httpx.TransportError as exc:
                if _can_retry(op, None, attempt, self.config.max_retries):
                    time.sleep(_backoff(attempt, None))
                    continue
                raise APIConnectionError(str(exc)) from exc
            if _can_retry(op, response.status_code, attempt, self.config.max_retries):
                time.sleep(_backoff(attempt, response))
                continue
            if response.status_code >= 300:  # a redirect we did not follow is not a result
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
        if self._owns_http:
            self._http.close()


class AsyncTransport:
    def __init__(self, config: Config, http_client: httpx.AsyncClient | None = None) -> None:
        self.config = config
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(follow_redirects=True)

    async def request(self, op: Operation, *, path=None, query=None, body=None) -> Any:
        url = self.config.base_url + _url(op, path)
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._http.request(
                    op.method, url, params=_clean(query), json=_clean(body),
                    headers=self.config.headers(), timeout=self.config.timeout,
                )
            except httpx.TransportError as exc:
                if _can_retry(op, None, attempt, self.config.max_retries):
                    await asyncio.sleep(_backoff(attempt, None))
                    continue
                raise APIConnectionError(str(exc)) from exc
            if _can_retry(op, response.status_code, attempt, self.config.max_retries):
                await asyncio.sleep(_backoff(attempt, response))
                continue
            if response.status_code >= 300:
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
        if self._owns_http:
            await self._http.aclose()
