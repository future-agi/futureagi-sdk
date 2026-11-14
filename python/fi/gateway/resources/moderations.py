"""Moderations resource."""

from __future__ import annotations

from typing import Any

from fi.gateway._base_client import RequestOptions
from fi.gateway._constants import NOT_GIVEN
from fi.gateway.types.moderation import ModerationResponse


class Moderations:
    """Sync moderations resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        input: str | list[str],
        model: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> ModerationResponse:
        body: dict[str, Any] = {"input": input}
        if model is not NOT_GIVEN:
            body["model"] = model
        if kwargs:
            body.update(kwargs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/moderations",
            body=body,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, ModerationResponse)


class AsyncModerations:
    """Async moderations resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        input: str | list[str],
        model: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> ModerationResponse:
        body: dict[str, Any] = {"input": input}
        if model is not NOT_GIVEN:
            body["model"] = model
        if kwargs:
            body.update(kwargs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/moderations",
            body=body,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, ModerationResponse)
