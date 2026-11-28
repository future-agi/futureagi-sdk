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

# Share the lane's graded HTTP policy and its one-notice-per-origin budget.
from fi._core.http_security import (
    check_http_security,
    httpx_client_proxied,
    httpx_client_sdk_built,
)
from fi._core.proxy_routing import SdkDirectAsyncTransport, SdkDirectTransport
from fi.errors import KeyedRedirectRefusedError

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
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
MAX_REDIRECTS = 5  # 0.8.1: a sixth redirect in a row raises APIConnectionError


class NotGiven:
    """The type of `NOT_GIVEN`: an argument the caller did not pass.

    Generated methods default every optional argument to `NOT_GIVEN`, so that an explicit
    `None` can be told apart from an omitted one: `None` is sent as JSON `null` (which is how
    a nullable field is cleared), `NOT_GIVEN` is left out of the request.
    """

    _instance: "NotGiven | None" = None

    def __new__(cls) -> "NotGiven":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN = NotGiven()


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
    decode: str = "json"  # json | text | auto (json when the response says so, else text)
    # The contract leaves the {status, result} envelope out of many responses, so by default one
    # is removed whenever present even when `unwrap` names no key. `client.request(unwrap=None)`
    # turns that off: the caller gets the body exactly as sent.
    auto_unwrap: bool = True


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
        if value is None or value is NOT_GIVEN:
            continue
        for item in value if isinstance(value, list) else [value]:
            out.append((field, _file_tuple(item)))
    return out or None


def _form(body: Any) -> Any:
    """Form fields are strings; booleans and numbers are rendered the way DRF parses them."""
    if not isinstance(body, dict):
        return body
    return {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in body.items() if v is not None and v is not NOT_GIVEN}


def _merge_headers(*layers: Mapping[str, str] | None) -> dict[str, str]:
    """Later layers replace earlier ones whatever the letter case: `x-workspace-id` set per call
    replaces the client's `X-Workspace-Id` instead of being sent next to it (header names are
    case-insensitive, and a server given both may combine or reject them)."""
    by_name: dict[str, tuple[str, str]] = {}
    for layer in layers:
        for key, value in (layer or {}).items():
            by_name[key.lower()] = (key, value)
    return {key: value for key, value in by_name.values()}


def _refuse_redirect(response: httpx.Response) -> None:
    """Raise ``KeyedRedirectRefusedError`` for a 3xx answer that is not followed (see :func:`_follow_redirect`): a 300,
    a redirect status without a ``Location``, or any other 3xx with one."""
    status = response.status_code
    if status in REDIRECT_STATUSES or (300 <= status < 400 and response.headers.get("location")):
        raise KeyedRedirectRefusedError(status_code=status)


def _origin(url: str) -> str:
    u = httpx.URL(url)
    return f"{u.scheme}://{u.host}:{u.port or (443 if u.scheme == 'https' else 80)}".lower()


def _follow_redirect(base_url: str, response: httpx.Response, method: str) -> tuple[str, str]:
    """(url, method) to follow a 301, 302, 303, 307 or 308 with, as 0.8.1 follows it. Only a target on the client's own
    origin (scheme, host and port of ``base_url``) is followed, and only from a request sent to that origin: the keys
    travel in custom headers (``X-Api-Key``, ``X-Secret-Key``) that httpx does not strip on a redirect. A target on any
    other origin (another scheme, such as https to http on the same host, another host or another port) raises
    ``KeyedRedirectRefusedError`` and nothing is sent to it; so does a chain that leaves the origin, at its first hop
    off it. The caller judges the target before it is sent, as any request."""
    try:
        target = str(response.request.url.join(response.headers["location"]))
        same_origin = _origin(target) == _origin(base_url) == _origin(str(response.request.url))
    except (httpx.InvalidURL, ValueError, TypeError, UnicodeError):
        same_origin = False
    if not same_origin:
        raise KeyedRedirectRefusedError(status_code=response.status_code)
    if response.status_code == 303 or (response.status_code in (301, 302) and method == "POST"):
        method = "GET"  # the way browsers and httpx re-issue these
    return target, method


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
    allow_insecure_http: bool | None = None

    def headers(self, options: RequestOptions | None = None) -> dict[str, str]:
        headers = {
            "X-Api-Key": self.api_key,
            "X-Secret-Key": self.secret_key,
            "User-Agent": "futureagi-python",
        }
        if self.workspace_id:
            headers["X-Workspace-Id"] = self.workspace_id
        return _merge_headers(headers, self.default_headers, options.headers if options else None)

    def timeout_for(self, options: RequestOptions | None) -> float:
        return options.timeout if options and options.timeout is not None else self.timeout

    def retries_for(self, options: RequestOptions | None) -> int:
        return options.max_retries if options and options.max_retries is not None else self.max_retries


def raw_operation(method: str, path: str, *, unwrap: str | None = "result", multipart: bool = False, decode: str = "json") -> Operation:
    """An ad-hoc operation for an endpoint the catalog does not describe (`client.request`)."""
    if not path.startswith("/"):
        raise ValueError(f"path must start with '/', got {path!r}")
    if decode not in ("json", "text", "auto"):
        raise ValueError(f"decode must be 'json', 'text' or 'auto', got {decode!r}")
    return Operation(
        id=f"raw:{method.upper()} {path}", method=method.upper(), path=path, unwrap=unwrap, pagination=None, multipart=multipart, decode=decode,
        auto_unwrap=unwrap is not None,  # unwrap=None is an explicit "give me the whole body"
    )


def _url(op: Operation, path: dict | None) -> str:
    url = op.path
    for name, value in (path or {}).items():
        url = url.replace("{" + name + "}", quote(str(value), safe=""))
    return url


def _clean(params: Any, *, keep_none: bool = False) -> Any:
    """Drop the fields the caller did not pass (`NOT_GIVEN`). A JSON body keeps an explicit
    `None` as `null` (that is how a nullable field is cleared); a query string has no null, so
    there `None` is dropped too. A non-dict body (e.g. a list) is sent as is."""
    if not isinstance(params, dict):
        return params
    return {k: v for k, v in params.items() if v is not NOT_GIVEN and (keep_none or v is not None)}


def _payload(op: Operation, body: Any, files: Dict[str, Any] | None) -> Dict[str, Any]:
    """httpx keyword arguments for the request body: JSON, or form fields plus uploads."""
    if op.multipart:
        return {"data": _form(body), "files": _files(files)}
    if files:
        raise TypeError(f"{op.id}: files are only accepted by multipart operations")
    return {"json": _clean(body, keep_none=True)}


def _decode(op: Operation, response: httpx.Response) -> Any:
    if response.status_code == 204 or not response.content:
        return None
    content_type = response.headers.get("content-type", "")
    if op.decode == "text" or (op.decode == "auto" and "json" not in content_type):
        return response.text  # e.g. a CSV export: the body is the result
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
    if op.auto_unwrap and isinstance(data, dict) and data.keys() == {"status", "result"} and data["status"] is True:
        return data["result"]
    return data


@functools.lru_cache(maxsize=None)
def _adapter(model: Any) -> TypeAdapter:
    return TypeAdapter(model)


def _parse(op: Operation, model: Any, data: Any, strict: bool) -> Any:
    """Validate into the generated model (or `List[model]`); untyped responses pass through.

    A response that does not match the contract does not break a call by default: the
    caller gets the raw JSON and a ResponseShapeWarning. Tests run strict to catch drift,
    which then also holds the response to the contract's required fields.
    """
    if model is None or data is None:
        return data
    try:
        # strict: the generated models also check the contract's required fields (see models._Model)
        return _adapter(model).validate_python(data, context={"strict": strict})
    except ValidationError as exc:
        if strict:
            raise ResponseValidationError(op.id, exc, data) from exc
        warnings.warn(f"{op.id}: response does not match the contract; returning raw JSON", ResponseShapeWarning, stacklevel=4)
        return data


def _check_page(op: Operation, data: Any, strict: bool) -> Any:
    """A page without its items list means the contract's page shape is wrong; it raises
    instead of returning an empty result."""
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


def _check_destination(client: Any, url: str, allow_insecure_http: bool | None) -> None:
    # The URL is judged as written: httpx reads a host written with the ideographic or fullwidth full stop as a dot and
    # sends to 127.0.0.1, so the parsed URL would pass for loopback a host the text names otherwise. A URL httpx cannot
    # read keeps httpx's own error. It is judged again as the client sends it, merged onto the client's own base_url
    # (a base URL of "/" or "//host" takes its scheme and host from there), with the proxy the client picks for it.
    # A caller's client whose transport for the URL is exactly httpx's MockTransport, WSGITransport or ASGITransport
    # answers in the process, makes no connection and is not judged (0.8.1); a subclass of one is judged.
    parsed = httpx.URL(url)
    if type(_transport_for(client, parsed)) in _IN_PROCESS:
        return
    _check_written_destination(client, url, allow_insecure_http)


def _check_built_request(client: Any, url: str, request: httpx.Request, allow_insecure_http: bool | None) -> None:
    # 0.8.1 judges the request as the client built it too: merged onto the client's base_url (a base URL of "/" or "//host"
    # takes its scheme and host from there). Its origin is judged (the path was judged as written), with the proxy the
    # client picks for it; a client that answers in the process makes no connection and is not judged.
    built = request.url
    if built.scheme != "http" or str(built) == url or type(_transport_for(client, built)) in _IN_PROCESS:
        return
    origin = str(built.copy_with(raw_path=b"/", fragment=None))
    check_http_security(
        origin, "keys", allow_insecure_http=allow_insecure_http,
        caller_proxied=httpx_client_proxied(client, built), proxies_disabled=True,
    )


_IN_PROCESS = (httpx.MockTransport, httpx.WSGITransport, httpx.ASGITransport)


def _transport_for(client: Any, url: httpx.URL) -> Any:
    try:
        return client._transport_for_url(url)
    except Exception:  # noqa: BLE001 - a client that cannot answer is judged
        return None


def _check_written_destination(client: Any, url: str, allow_insecure_http: bool | None) -> None:
    if url[:7].lower() != "http://":
        check_http_security(url, "keys", allow_insecure_http=allow_insecure_http)
        return
    # A client the SDK built sends plain HTTP direct (its mount reads no proxy variable). A caller's client is asked
    # which transport it uses for the URL: the proxies it picks for itself (its ``proxy=``, ``mounts=`` and, while
    # ``trust_env`` is on, the environment it read) decide, and a client with ``trust_env=False`` reads no proxy
    # variable, so the environment is not judged for it (0.8.1).
    built = httpx_client_sdk_built(client, url)
    check_http_security(
        url, "keys", allow_insecure_http=allow_insecure_http,
        caller_proxied=not built and httpx_client_proxied(client, url), proxies_disabled=True,
    )


class SyncTransport:
    def __init__(self, config: Config, http_client: httpx.Client | None = None) -> None:
        self.config = config
        # A caller's client is used as given (absolute URLs, per-request timeout) and not
        # closed here; only a client we created is ours to configure and close.
        self._owns_http = http_client is None
        # Redirects are followed here, not by httpx, and only to the client's own origin (see _follow_redirect). Every
        # request says follow_redirects=False itself, because a caller's client may have follow_redirects=True.
        self._http = http_client or httpx.Client(follow_redirects=False, mounts={"http://": SdkDirectTransport()})

    def request(self, op: Operation, *, path=None, query=None, body=None, files=None, options: RequestOptions | None = None) -> Any:
        """One HTTP call for `op`: auth, retries, envelope unwrap, typed errors. Returns decoded JSON."""
        url, method = self.config.base_url + _url(op, path), op.method
        payload = _payload(op, body, files)
        headers, timeout, retries = self.config.headers(options), self.config.timeout_for(options), self.config.retries_for(options)
        attempt = redirects = 0
        while True:
            _check_destination(self._http, url, self.config.allow_insecure_http)
            request = self._http.build_request(method, url, params=_clean(query), headers=headers, timeout=timeout, **payload)
            _check_built_request(self._http, url, request, self.config.allow_insecure_http)
            try:
                response = self._http.send(request, follow_redirects=False)
            except httpx.TransportError as exc:
                if _can_retry(op, None, attempt, retries):
                    time.sleep(_backoff(attempt, None))
                    attempt += 1
                    continue
                raise APIConnectionError(str(exc)) from exc
            if response.status_code in REDIRECT_STATUSES and response.headers.get("location"):
                redirects += 1
                if redirects > MAX_REDIRECTS:
                    raise APIConnectionError(f"{op.id}: more than {MAX_REDIRECTS} redirects")
                url, method = _follow_redirect(self.config.base_url, response, method)
                query = None  # the target URL carries the query it needs
                if method != op.method:
                    payload = {}  # sent again as a GET: no body
                continue
            _refuse_redirect(response)
            if _can_retry(op, response.status_code, attempt, retries):
                time.sleep(_backoff(attempt, response))
                attempt += 1
                continue
            if response.status_code >= 300:  # a redirect without a target is not a result
                raise error_from_response(response)
            return _decode(op, response)

    def raw(self, method: str, path: str, *, query=None, body=None, files=None, unwrap: str | None = "result", multipart: bool = False, decode: str = "json", options: RequestOptions | None = None) -> Any:
        """Call an endpoint the catalog does not describe; the usual auth, retries and errors apply."""
        return self.request(raw_operation(method, path, unwrap=unwrap, multipart=multipart, decode=decode), query=query, body=body, files=files, options=options)

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
        self._http = http_client or httpx.AsyncClient(follow_redirects=False, mounts={"http://": SdkDirectAsyncTransport()})

    async def request(self, op: Operation, *, path=None, query=None, body=None, files=None, options: RequestOptions | None = None) -> Any:
        url, method = self.config.base_url + _url(op, path), op.method
        payload = _payload(op, body, files)
        headers, timeout, retries = self.config.headers(options), self.config.timeout_for(options), self.config.retries_for(options)
        attempt = redirects = 0
        while True:
            _check_destination(self._http, url, self.config.allow_insecure_http)
            request = self._http.build_request(method, url, params=_clean(query), headers=headers, timeout=timeout, **payload)
            _check_built_request(self._http, url, request, self.config.allow_insecure_http)
            try:
                response = await self._http.send(request, follow_redirects=False)
            except httpx.TransportError as exc:
                if _can_retry(op, None, attempt, retries):
                    await asyncio.sleep(_backoff(attempt, None))
                    attempt += 1
                    continue
                raise APIConnectionError(str(exc)) from exc
            if response.status_code in REDIRECT_STATUSES and response.headers.get("location"):
                redirects += 1
                if redirects > MAX_REDIRECTS:
                    raise APIConnectionError(f"{op.id}: more than {MAX_REDIRECTS} redirects")
                url, method = _follow_redirect(self.config.base_url, response, method)
                query = None  # the target URL carries the query it needs
                if method != op.method:
                    payload = {}  # sent again as a GET: no body
                continue
            _refuse_redirect(response)
            if _can_retry(op, response.status_code, attempt, retries):
                await asyncio.sleep(_backoff(attempt, response))
                attempt += 1
                continue
            if response.status_code >= 300:
                raise error_from_response(response)
            return _decode(op, response)

    async def raw(self, method: str, path: str, *, query=None, body=None, files=None, unwrap: str | None = "result", multipart: bool = False, decode: str = "json", options: RequestOptions | None = None) -> Any:
        return await self.request(raw_operation(method, path, unwrap=unwrap, multipart=multipart, decode=decode), query=query, body=body, files=files, options=options)

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
