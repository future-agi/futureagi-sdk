"""Images resource."""

from __future__ import annotations

from typing import Any

from fi.gateway._base_client import RequestOptions
from fi.gateway._constants import NOT_GIVEN
from fi.gateway.types.image import ImageResponse


class Images:
    """Sync images resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def generate(
        self,
        *,
        prompt: str,
        model: Any = NOT_GIVEN,
        n: Any = NOT_GIVEN,
        quality: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        size: Any = NOT_GIVEN,
        style: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> ImageResponse:
        body: dict[str, Any] = {"prompt": prompt}
        for key, val in {
            "model": model,
            "n": n,
            "quality": quality,
            "response_format": response_format,
            "size": size,
            "style": style,
            "user": user,
        }.items():
            if val is not NOT_GIVEN:
                body[key] = val
        if extra_body:
            body.update(extra_body)
        if kwargs:
            body.update(kwargs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/images/generations",
            body=body,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, ImageResponse)


class AsyncImages:
    """Async images resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def generate(
        self,
        *,
        prompt: str,
        model: Any = NOT_GIVEN,
        n: Any = NOT_GIVEN,
        quality: Any = NOT_GIVEN,
        response_format: Any = NOT_GIVEN,
        size: Any = NOT_GIVEN,
        style: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> ImageResponse:
        body: dict[str, Any] = {"prompt": prompt}
        for key, val in {
            "model": model,
            "n": n,
            "quality": quality,
            "response_format": response_format,
            "size": size,
            "style": style,
            "user": user,
        }.items():
            if val is not NOT_GIVEN:
                body[key] = val
        if extra_body:
            body.update(extra_body)
        if kwargs:
            body.update(kwargs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/images/generations",
            body=body,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, ImageResponse)
