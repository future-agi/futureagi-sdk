"""The one HTTP layer every resource uses: auth, retries, envelope unwrap, errors."""

from __future__ import annotations

import asyncio
import functools
import os
import random
import time
import warnings
from dataclasses import dataclass
from typing import IO, Any, Dict, List, Mapping, Optional, Tuple, Union
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
    multipart: bool = False  # body fields go as form data, file params as uploads


@dataclass(frozen=True)
class RequestOptions:
    """Per-call overrides, accepted by every generated method as `options=`."""

    headers: Optional[Mapping[str, str]] = None  # added to (and overriding) the client's headers
    timeout: Optional[float] = None
    max_retries: Optional[int] = None


# What a caller may pass for a file parameter: a path, raw bytes, an open binary
# file, or an explicit (filename, bytes-or-file) pair.
FileInput = Union[str, "os.PathLike[str]", bytes, IO[bytes], Tuple[str, Union[bytes, IO[bytes]]]]


def _file_tuple(value: FileInput) -> Tuple[str, bytes]:
    """Read a file input into (filename, bytes) so a retried request can resend it."""
    if isinstance(value, tuple):
        name, data = value
        return name, data if isinstance(data, bytes) else data.read()
    if isinstance(value, bytes):
        return "upload", value
    if isinstance(value, (str, os.PathLike)):
        with open(value, "rb") as fh:
            return os.path.basename(os.fspath(value)), fh.read()
    name = getattr(value, "name", None)
    return (os.path.basename(str(name)) if name else "upload"), value.read()


def _files(files: Dict[str, Any] | None) -> List[Tuple[str, Tuple[str, bytes]]] | None:
    """{field: FileInput | [FileInput]} -> httpx `files` list; unset (None) fields are dropped."""
    if not files:
        return None
    out: List[Tuple[str, Tuple[str, bytes]]] = []
    for field, value in files.items():
        if value is None:
            continue
        for item in value if isinstance(value, list) else [value]:
            out.append((field, _file_tuple(item)))
    return out or None


def _form(body: Any) -> Any:
    """Form fields are strings; booleans and numbers are rendered the way DRF parses them."""
    if not isinstance(body, dict):
        return body
    return {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in body.items() if v is not None}


@dataclass
class Config:
    api_key: str
    secret_key: str
    base_url: str
    timeout: float
    max_retries: int
    workspace_id: str | None = None
    strict_responses: bool = False
    default_headers: Optional[Mapping[str, str]] = None

    def headers(self, options: RequestOptions | None = None) -> dict[str, str]:
        headers = {
            "X-Api-Key": self.api_key,
            "X-Secret-Key": self.secret_key,
            "User-Agent": "futureagi-python",
        }
        if self.workspace_id:
            headers["X-Workspace-Id"] = self.workspace_id
        headers.update(self.default_headers or {})
        if options and options.headers:
            headers.update(options.headers)
        return headers

    def timeout_for(self, options: RequestOptions | None) -> float:
        return options.timeout if options and options.timeout is not None else self.timeout

    def retries_for(self, options: RequestOptions | None) -> int:
        return options.max_retries if options and options.max_retries is not None else self.max_retries


def raw_operation(method: str, path: str, *, unwrap: str | None = "result", multipart: bool = False) -> Operation:
    """An ad-hoc operation for an endpoint the catalog does not describe (`client.request`)."""
    if not path.startswith("/"):
        raise ValueError(f"path must start with '/', got {path!r}")
    return Operation(id=f"raw:{method.upper()} {path}", method=method.upper(), path=path, unwrap=unwrap, pagination=None, multipart=multipart)


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


def _payload(op: Operation, body: Any, files: Dict[str, Any] | None) -> Dict[str, Any]:
    """httpx keyword arguments for the request body: JSON, or form fields plus uploads."""
    if op.multipart:
        return {"data": _form(body), "files": _files(files)}
    if files:
        raise TypeError(f"{op.id}: files are only accepted by multipart operations")
    return {"json": _clean(body)}


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

    def request(self, op: Operation, *, path=None, query=None, body=None, files=None, options: RequestOptions | None = None) -> Any:
        """One HTTP call for `op`: auth, retries, envelope unwrap, typed errors. Returns decoded JSON."""
        url = self.config.base_url + _url(op, path)
        payload = _payload(op, body, files)
        headers, timeout, retries = self.config.headers(options), self.config.timeout_for(options), self.config.retries_for(options)
        for attempt in range(retries + 1):
            try:
                response = self._http.request(op.method, url, params=_clean(query), headers=headers, timeout=timeout, **payload)
            except httpx.TransportError as exc:
                if _can_retry(op, None, attempt, retries):
                    time.sleep(_backoff(attempt, None))
                    continue
                raise APIConnectionError(str(exc)) from exc
            if _can_retry(op, response.status_code, attempt, retries):
                time.sleep(_backoff(attempt, response))
                continue
            if response.status_code >= 300:  # a redirect we did not follow is not a result
                raise error_from_response(response)
            return _decode(op, response)
        raise AssertionError("unreachable")

    def raw(self, method: str, path: str, *, query=None, body=None, files=None, unwrap: str | None = "result", multipart: bool = False, options: RequestOptions | None = None) -> Any:
        """Call an endpoint the catalog does not describe; the usual auth, retries and errors apply."""
        return self.request(raw_operation(method, path, unwrap=unwrap, multipart=multipart), query=query, body=body, files=files, options=options)

    def call(self, op: Operation, *, path=None, query=None, body=None, files=None, model=None, options: RequestOptions | None = None) -> Any:
        data = self.request(op, path=path, query=query, body=body, files=files, options=options)
        return _parse(op, model, data, self.config.strict_responses)

    def paginate(self, op: Operation, *, path=None, query=None, model=None, options: RequestOptions | None = None) -> SyncPager:
        spec = op.pagination

        def fetch(page: int) -> Any:
            data = self.request(op, path=path, query={**(query or {}), spec["page_param"]: page}, options=options)
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

    async def request(self, op: Operation, *, path=None, query=None, body=None, files=None, options: RequestOptions | None = None) -> Any:
        url = self.config.base_url + _url(op, path)
        payload = _payload(op, body, files)
        headers, timeout, retries = self.config.headers(options), self.config.timeout_for(options), self.config.retries_for(options)
        for attempt in range(retries + 1):
            try:
                response = await self._http.request(op.method, url, params=_clean(query), headers=headers, timeout=timeout, **payload)
            except httpx.TransportError as exc:
                if _can_retry(op, None, attempt, retries):
                    await asyncio.sleep(_backoff(attempt, None))
                    continue
                raise APIConnectionError(str(exc)) from exc
            if _can_retry(op, response.status_code, attempt, retries):
                await asyncio.sleep(_backoff(attempt, response))
                continue
            if response.status_code >= 300:
                raise error_from_response(response)
            return _decode(op, response)
        raise AssertionError("unreachable")

    async def raw(self, method: str, path: str, *, query=None, body=None, files=None, unwrap: str | None = "result", multipart: bool = False, options: RequestOptions | None = None) -> Any:
        return await self.request(raw_operation(method, path, unwrap=unwrap, multipart=multipart), query=query, body=body, files=files, options=options)

    async def acall(self, op: Operation, *, path=None, query=None, body=None, files=None, model=None, options: RequestOptions | None = None) -> Any:
        data = await self.request(op, path=path, query=query, body=body, files=files, options=options)
        return _parse(op, model, data, self.config.strict_responses)

    def apaginate(self, op: Operation, *, path=None, query=None, model=None, options: RequestOptions | None = None) -> AsyncPager:
        spec = op.pagination

        async def fetch(page: int) -> Any:
            data = await self.request(op, path=path, query={**(query or {}), spec["page_param"]: page}, options=options)
            return _check_page(op, data, self.config.strict_responses)

        return AsyncPager(fetch, spec, lambda item: _parse(op, model, item, self.config.strict_responses))

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()
