"""Embeddings resource."""

from __future__ import annotations

from typing import Any

from fi.gateway._base_client import RequestOptions
from fi.gateway._constants import NOT_GIVEN
from fi.gateway.types.embedding import EmbeddingResponse


class Embeddings:
    """Sync embeddings resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        input: str | list[str] | list[int] | list[list[int]],
        encoding_format: Any = NOT_GIVEN,
        dimensions: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        body: dict[str, Any] = {"model": model, "input": input}
        if encoding_format is not NOT_GIVEN:
            body["encoding_format"] = encoding_format
        if dimensions is not NOT_GIVEN:
            body["dimensions"] = dimensions
        if user is not NOT_GIVEN:
            body["user"] = user
        if extra_body:
            body.update(extra_body)
        if kwargs:
            body.update(kwargs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/embeddings",
            body=body,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, EmbeddingResponse)


class AsyncEmbeddings:
    """Async embeddings resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        model: str,
        input: str | list[str] | list[int] | list[list[int]],
        encoding_format: Any = NOT_GIVEN,
        dimensions: Any = NOT_GIVEN,
        user: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        body: dict[str, Any] = {"model": model, "input": input}
        if encoding_format is not NOT_GIVEN:
            body["encoding_format"] = encoding_format
        if dimensions is not NOT_GIVEN:
            body["dimensions"] = dimensions
        if user is not NOT_GIVEN:
            body["user"] = user
        if extra_body:
            body.update(extra_body)
        if kwargs:
            body.update(kwargs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/embeddings",
            body=body,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, EmbeddingResponse)
