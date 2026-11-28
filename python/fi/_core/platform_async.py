"""The async platform executor: the same steps as ``fi._core.platform_base.PlatformCore`` (the
module docstring there has them), on ``httpx.AsyncClient``."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Mapping, Optional

import httpx

from fi._core import idempotency as idem
from fi._core.platform_base import MAX_ERROR_BODY, Opened, ResponseMapper, _Base
from fi._core.raw import CallMeta
from fi._core.transport import (
    ATTEMPTS_EXTENSION,
    IN_PROGRESS_BUDGET_S,
    TimeoutArg,
    _async_sleep,
)


class AsyncPlatformCore(_Base):
    """The async executor (the same steps as :class:`PlatformCore`)."""

    async def call(
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
        return (
            await self.call_with_meta(
                name,
                path=path,
                query=query,
                body=body,
                idempotency_key=idempotency_key,
                headers=headers,
                timeout=timeout,
                retries=retries,
            )
        )[0]

    async def call_with_meta(self, name: str, *, map_response: Optional[ResponseMapper] = None, **kw: Any) -> tuple[Any, CallMeta]:
        opened, data = await self._execute(name, stream=False, map_response=map_response, **kw)
        return data, opened.meta

    async def open_stream(
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
        return (
            await self._execute(
                name,
                stream=True,
                path=path,
                query=query,
                body=body,
                idempotency_key=idempotency_key,
                headers=headers,
                timeout=timeout,
                idle=idle_timeout,
            )
        )[0]

    async def _execute(
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
        http = self.shared.ahttp()
        prep = self._prepare(http, name, path, query, body, idempotency_key, headers, timeout, retries, stream, idle)
        sleep = _async_sleep(self.shared.sleep) if self.shared.sleep else asyncio.sleep
        deadline, earlier = time.monotonic() + IN_PROGRESS_BUDGET_S, 0
        while True:
            try:
                response = await http.send(prep.request, stream=True, auth=None, follow_redirects=False)
            except httpx.TransportError as exc:
                raise self._no_response(prep, exc) from exc
            if response.is_success:
                if stream:
                    return Opened(response, self._meta(prep, response, earlier)), None
                try:
                    raw = await response.aread()
                except httpx.TransportError as exc:
                    raise self._no_response(prep, exc) from exc
                finally:
                    await response.aclose()
                meta = self._meta(prep, response, earlier)
                data = self._json(prep, raw)
                if map_response is not None:
                    data = map_response(data, prep.scrub, meta)
                return Opened(response, meta), data
            try:
                raw, complete = (b"", False) if response.is_redirect else await _aread_capped(response)
            finally:
                await response.aclose()
            if response.is_redirect:
                raise self._redirect(prep, response)
            if self._applied(prep, response):
                return Opened(response, self._meta(prep, response, earlier, applied=True)), None
            err = self._status_error(prep, response, raw, complete=complete)
            wait = idem.in_progress_wait(prep.op, response.status_code, err.code, err.retry_after)
            if wait is None or time.monotonic() + wait > deadline:
                raise err
            await sleep(wait)
            earlier += len(prep.request.extensions[ATTEMPTS_EXTENSION])  # attempts before this resend
            prep.request.extensions[ATTEMPTS_EXTENSION] = []


async def _aread_capped(response: httpx.Response) -> tuple[bytes, bool]:
    chunks, size, complete = [], 0, False
    try:
        async for chunk in response.aiter_bytes():
            chunks.append(chunk)
            size += len(chunk)
            if size >= MAX_ERROR_BODY:
                break
        else:
            complete = True
    except httpx.HTTPError:
        pass  # a capped or interrupted body cannot prove the absence of an EE envelope
    return b"".join(chunks), complete
