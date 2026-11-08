"""The platform request executor: one logical call by SDK operation name.

One HTTP client per mode uses ``RetryingTransport`` (``fi._http``), the operation's retry class in
``request.extensions["fi.retry"]``, ``httpx.Timeout(30, connect=10)`` and ``follow_redirects=False``.
``fi._core.origins`` resolves keys or Bearer on the first platform call; a bad ``FI_PLATFORM_BASE_URL``
never breaks a core namespace. An attempt recorder tracks whether earlier sends may have applied.

- ``FI_EXTRA_HEADERS`` / ``extra_headers=`` apply only under ``base_url``, are read on every call,
  never overwrite an existing header, fail before sending if malformed, and are scrubbed from errors.
- One idempotency key is minted for all attempts (``fi._core.idempotency``).
- A 409 ``idempotency_key_in_progress`` waits ``Retry-After`` (else 1 s) and resends the same key,
  up to ``IN_PROGRESS_BUDGET_S``; a ``not_found_means_applied`` 404 succeeds after a possibly-applied attempt.
- A 3xx raises ``UnexpectedRedirectError`` with the target host only, never following the redirect.
- Other statuses use ``fi._core.errors.api_error`` with redacted bodies and scrubbed text; failures
  without a response become ``APIConnectionError`` / ``APITimeoutError``.

``PlatformCore`` and ``fi._core.platform_async.AsyncPlatformCore`` share the status-error path.
``with_settings`` / ``client.with_options`` change defaults but share the connection pool; HTTP clients,
the attempt recorder and shared state live in ``fi._core.transport``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping, Optional

import httpx

from fi._core import idempotency as idem
from fi._core.errors import api_error, connection_error
from fi._core.http_security import check_http_security
from fi._core.origins import PlatformOrigin, display_host
from fi._core.platform_errors import platform_status_error
from fi._core.policy import OperationSpec
from fi._core.raw import CallMeta, meta_from, record
from fi._core.redact import redact_value, request_secret_values, scrub_value
from fi._core.request import build_body, build_path, build_query, query_string
from fi._core.transport import (
    ATTEMPTS_EXTENSION,
    IN_PROGRESS_BUDGET_S,
    MAX_ERROR_BODY,
    PlatformShared,
    Settings,
    TimeoutArg,
    as_timeout,
    possibly_applied,
    user_agent,
)
from fi.errors import (
    APIConnectionError,
    ConfigurationError,
    FutureAGIAPIError,
    UnexpectedRedirectError,
)


# A namespace interprets decoded data while the request's scrub set is still local.
# Credentials never become part of public response metadata.
ResponseMapper = Callable[[Any, list[str], CallMeta], Any]


@dataclass
class Prepared:
    op: OperationSpec
    origin: PlatformOrigin
    request: httpx.Request
    key: Optional[str]
    scrub: list[str]


@dataclass
class Opened:
    """An opened stream: the live response (body unread; close it) and its meta."""

    response: httpx.Response
    meta: CallMeta


class _Base:
    def __init__(self, shared: PlatformShared, settings: Optional[Settings] = None) -> None:
        self.shared = shared
        self.settings = settings or Settings()

    def with_settings(self, *, timeout: TimeoutArg = None, retries: Optional[int] = None) -> Any:
        """A copy with other defaults that shares the origin and the connection pool."""
        new = self.settings
        if timeout is not None:
            new = replace(new, timeout=as_timeout(timeout))
        if retries is not None:
            new = replace(new, retries=int(retries))
        return type(self)(self.shared, new)

    def operation(self, name: str) -> OperationSpec:
        return self.shared.operation(name)

    def _prepare(
        self,
        http: Any,
        name: str,
        path: Any,
        query: Any,
        body: Any,
        key: Optional[str],
        headers: Optional[Mapping[str, str]],
        timeout: TimeoutArg,
        retries: Optional[int],
        stream: bool,
        idle: Optional[float],
    ) -> Prepared:
        op = self.shared.operation(name)
        if op.human_only:
            raise ConfigurationError(
                f"{name} is a decision only a person makes, in the Future AGI app",
                code="human_only_verb",
                operation=name,
            )
        if stream and op.stream is None:
            raise ConfigurationError(f"{name} is not a streaming operation", code="not_a_stream", operation=name)
        if not stream and op.stream is not None:
            raise ConfigurationError(
                f"{name} streams: open it with a stream method", code="is_a_stream", operation=name
            )
        origin = self.shared.origin()
        if origin.mode == "keys":
            check_http_security(origin.url, "keys")
        url = origin.base + build_path(op, path) + query_string(build_query(op, query))
        encoded = build_body(op, body)
        key = idem.resolve_idempotency_key(op, key)
        out = {
            "User-Agent": user_agent(),
            "Accept": "text/event-stream" if stream else "application/json",
            **origin.headers,
        }
        allowed = set(op.headers) | (
            {"last-event-id"} if op.stream is not None and op.stream.resume == "last-event-id" else set()
        )
        for header, value in (headers or {}).items():
            if header.lower() not in allowed:
                raise ConfigurationError(
                    f"{name} does not declare the header {header.lower()}, so it is not sent",
                    code="undeclared_header",
                    operation=name,
                )
            out[header] = value
        if encoded.content_type is not None:
            out["Content-Type"] = encoded.content_type
        if key is not None:
            out[idem.IDEMPOTENCY_HEADER] = key
        t = as_timeout(timeout, self.settings.timeout)
        if stream:  # a stream's read timeout is its idle timeout, not the request timeout
            read = self.settings.stream_idle_timeout if idle is None else idle
            t = httpx.Timeout(connect=t.connect, read=read, write=t.write, pool=t.pool)
        retry: dict[str, Any] = {"class": op.retry_class}
        count = retries if retries is not None else self.settings.retries
        if count is not None:
            retry["retries"] = int(count)
        if stream:
            retry["retries"] = 0  # the resumable helpers reconnect themselves; exec is never repeated
        request = http.build_request(
            op.method,
            url,
            headers=out,
            content=encoded.content,
            extensions={"fi.retry": retry, "timeout": t.as_dict(), ATTEMPTS_EXTENSION: []},
        )
        # FI_EXTRA_HEADERS / extra_headers=, as on the core namespaces: read now, only under the client's
        # base_url, and never over a header already set (the SDK's own, a declared per-call one)
        extra = {} if self.shared.extra_headers is None else self.shared.extra_headers.for_url(request.url)
        for header, value in extra.items():
            request.headers.setdefault(header, value)
        return Prepared(op, origin, request, key, [*origin.secrets, *_values(extra), *request_secret_values(body, op.secret_fields)])

    def _no_response(self, prep: Prepared, exc: httpx.TransportError) -> APIConnectionError:
        err = connection_error(
            exc,
            operation=prep.op.name,
            idempotency_key=prep.key,
            base_url=prep.origin.base,
            setting="FI_PLATFORM_BASE_URL",
        )
        err.possibly_applied = any(possibly_applied(o) for o in prep.request.extensions[ATTEMPTS_EXTENSION])
        return err

    def _redirect(self, prep: Prepared, response: httpx.Response) -> UnexpectedRedirectError:
        location = response.headers.get("location")
        host = None
        if location:
            try:
                host = display_host(prep.request.url.join(location))
            except Exception:
                host = None
        return UnexpectedRedirectError(
            f"{prep.op.name}: the server answered {response.status_code} and platform calls never follow a redirect "
            f"(target host: {host or 'unknown'})",
            status_code=response.status_code,
            target_host=host,
            request_id=response.headers.get("x-request-id"),
            operation=prep.op.name,
        )

    def _applied(self, prep: Prepared, response: httpx.Response) -> bool:
        log = prep.request.extensions[ATTEMPTS_EXTENSION]
        return (
            response.status_code == 404
            and prep.op.not_found_means_applied
            and any(possibly_applied(o) for o in log[:-1])
        )

    def _status_error(self, prep: Prepared, response: httpx.Response, raw: bytes, *, complete: bool) -> FutureAGIAPIError:
        if response.status_code == 403:
            text = raw[:MAX_ERROR_BODY].decode("utf-8", "replace")
            regional = False
            try:
                # Preserve raw authority before scrubbing; False prevents a scrubber from promoting an error.
                decoded = json.loads(text) if text.strip() else None
                regional = isinstance(decoded, dict) and decoded.get("error") == "wrong_region"
                body = {"error": "wrong_region"} if regional else (self.shared.error_scrubber or scrub_value)(decoded, prep.scrub)
            except ValueError:
                body = None
            return api_error(
                response.status_code, redact_value(body), response.headers,
                operation=prep.op.name, family=prep.op.family, idempotency_key=prep.key,
                body=body, regional=regional,
            )
        return platform_status_error(
            prep.op, prep.origin, response, raw,
            complete=complete,
            secrets=prep.scrub,
            idempotency_key=prep.key,
            error_scrubber=self.shared.error_scrubber,
        )

    def _meta(self, prep: Prepared, response: httpx.Response, earlier: int, applied: bool = False) -> CallMeta:
        attempts = len(prep.request.extensions[ATTEMPTS_EXTENSION]) + earlier
        meta = meta_from(
            response,
            prep.op.name,
            idempotency_key=prep.key,
            attempts=max(1, attempts),
            replay=idem.is_replay(response.headers),
            applied=applied,
        )
        record(meta)
        return meta

    @staticmethod
    def _json(prep: Prepared, raw: bytes) -> Any:
        if not raw.strip():
            return None
        try:
            return json.loads(raw)
        except ValueError:
            raise FutureAGIAPIError(
                200,
                None,
                code="invalid_json",
                operation=prep.op.name,
                message=f"{prep.op.name}: the server's response was not JSON",
            ) from None


class PlatformCore(_Base):
    """The sync executor."""

    def call(
        self,
        name: str,
        *,
        path: Any = None,
        query: Any = None,
        body: Any = None,
        idempotency_key: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: TimeoutArg = None,
        retries: Optional[int] = None,
    ) -> Any:
        """Call a JSON operation and return its parsed body (never validated: a newer server's
        fields are kept). A not-found-means-applied 404 returns None."""
        return self.call_with_meta(
            name,
            path=path,
            query=query,
            body=body,
            idempotency_key=idempotency_key,
            headers=headers,
            timeout=timeout,
            retries=retries,
        )[0]

    def call_with_meta(self, name: str, *, map_response: Optional[ResponseMapper] = None, **kw: Any) -> tuple[Any, CallMeta]:
        opened, data = self._execute(name, stream=False, map_response=map_response, **kw)
        return data, opened.meta

    def open_stream(
        self,
        name: str,
        *,
        path: Any = None,
        query: Any = None,
        body: Any = None,
        idempotency_key: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: TimeoutArg = None,
        idle_timeout: Optional[float] = None,
    ) -> Opened:
        """Open a streaming operation; the caller reads ``.response`` and must close it."""
        return self._execute(
            name,
            stream=True,
            path=path,
            query=query,
            body=body,
            idempotency_key=idempotency_key,
            headers=headers,
            timeout=timeout,
            idle=idle_timeout,
        )[0]

    def _execute(
        self,
        name: str,
        *,
        stream: bool,
        path: Any = None,
        query: Any = None,
        body: Any = None,
        idempotency_key: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: TimeoutArg = None,
        retries: Optional[int] = None,
        idle: Optional[float] = None,
        map_response: Optional[ResponseMapper] = None,
    ) -> tuple[Opened, Any]:
        http = self.shared.http()
        prep = self._prepare(http, name, path, query, body, idempotency_key, headers, timeout, retries, stream, idle)
        sleep = self.shared.sleep or time.sleep
        deadline, earlier = time.monotonic() + IN_PROGRESS_BUDGET_S, 0
        while True:
            try:
                response = http.send(prep.request, stream=True, auth=None, follow_redirects=False)
            except httpx.TransportError as exc:
                raise self._no_response(prep, exc) from exc
            if response.is_success:
                if stream:
                    return Opened(response, self._meta(prep, response, earlier)), None
                try:
                    raw = response.read()
                except httpx.TransportError as exc:
                    raise self._no_response(prep, exc) from exc
                finally:
                    response.close()
                meta = self._meta(prep, response, earlier)
                data = self._json(prep, raw)
                if map_response is not None:
                    data = map_response(data, prep.scrub, meta)
                return Opened(response, meta), data
            try:
                raw, complete = (b"", False) if response.is_redirect else _read_capped(response)
            finally:
                response.close()
            if response.is_redirect:
                raise self._redirect(prep, response)
            if self._applied(prep, response):
                return Opened(response, self._meta(prep, response, earlier, applied=True)), None
            err = self._status_error(prep, response, raw, complete=complete)
            wait = idem.in_progress_wait(prep.op, response.status_code, err.code, err.retry_after)
            if wait is None or time.monotonic() + wait > deadline:
                raise err
            sleep(wait)
            earlier += len(prep.request.extensions[ATTEMPTS_EXTENSION])  # attempts before this resend
            prep.request.extensions[ATTEMPTS_EXTENSION] = []


def _values(headers: Mapping[str, str]) -> list[str]:
    """Extra header values, and the token after an auth scheme, to scrub from a reflected error text
    (8 characters or more, as ``fi._extra_headers.secret_values``, so a short value garbles nothing)."""
    out = [part for value in headers.values() for part in (value, value.partition(" ")[2].strip())]
    return [value for value in out if len(value) >= 8]


def _read_capped(response: httpx.Response) -> tuple[bytes, bool]:
    chunks, size, complete = [], 0, False
    try:
        for chunk in response.iter_bytes():
            chunks.append(chunk)
            size += len(chunk)
            if size >= MAX_ERROR_BODY:
                break
        else:
            complete = True
    except httpx.HTTPError:
        pass  # a capped or interrupted body cannot prove the absence of an EE envelope
    return b"".join(chunks), complete
