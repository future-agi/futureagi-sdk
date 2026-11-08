"""Small connector adapters over the shared platform and FA transports."""
from __future__ import annotations

from typing import Any

from fi._core.pagination import AsyncPage, Page
from fi._core.policy import PaginationSpec
from fi.errors import FutureAGIAPIError


class Resource:
    """A namespace retaining the root, so with_options keeps its own settings."""

    def __init__(self, client: Any) -> None:
        self._client = client


class AsyncResource(Resource):
    """The async namespace's transport is resolved only when a method is called."""


_CHANNELS = PaginationSpec("cursor", "channels", cursor_param="cursor", next_cursor_field="next_cursor")


def _channels(value: Any) -> Any:
    if not isinstance(value, dict) or not isinstance(value.get("channels"), list):
        raise FutureAGIAPIError(200, None, code="invalid_page", message="The response is missing its channel items")
    return value


def cursor_page(resource: Any, operation: Any, *, path: Any, query: Any) -> Page[Any]:
    """Walk Slack's opaque cursor without requesting any supplied provider URL."""
    def fetch(cursor: str | None) -> Any:
        q = {**query, **({"cursor": cursor} if cursor is not None else {})}
        return _channels(resource._call(operation, path=path, query=q, body=None))
    return Page(fetch(None), _CHANNELS, fetch)


async def async_cursor_page(resource: Any, operation: Any, *, path: Any, query: Any) -> AsyncPage[Any]:
    """Async opaque-cursor channel walk using only the declared FA operation."""
    async def fetch(cursor: str | None) -> Any:
        q = {**query, **({"cursor": cursor} if cursor is not None else {})}
        return _channels(await resource._call(operation, path=path, query=q, body=None))
    return AsyncPage(await fetch(None), _CHANNELS, fetch)
