"""Auto-pagination over the backend's several page styles.

Each catalog operation states its style, e.g.
    {page_param: page, size_param: limit, first_page: 1, items: results, next: next}
    {page_param: page_number, size_param: page_size, first_page: 0, items: table, total_pages: metadata.total_pages}
so one pager handles all of them.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")

MAX_PAGES = 10_000  # guard against a server that never says "last page"


def _get(data: Any, dotted: str) -> Any:
    for part in dotted.split("."):
        if not isinstance(data, dict):
            return None
        data = data.get(part)
    return data


@dataclass
class Page(Generic[T]):
    items: list[T]
    number: int
    raw: Any


class _PagerBase(Generic[T]):
    def __init__(self, spec: dict, parse: Callable[[Any], T]) -> None:
        self._spec = spec
        self._parse = parse

    def _items(self, data: Any) -> list[T]:
        return [self._parse(item) for item in (_get(data, self._spec["items"]) or [])]

    def _is_last(self, data: Any, page: int, count: int) -> bool:
        if count == 0:
            return True
        if "next" in self._spec:
            return not _get(data, self._spec["next"])
        total = _get(data, self._spec["total_pages"])
        return total is None or page - self._spec["first_page"] + 1 >= total


class SyncPager(_PagerBase[T]):
    """Iterate to get every item across pages; `.first_page()` for just one page."""

    def __init__(self, fetch: Callable[[int], Any], spec: dict, parse: Callable[[Any], T]) -> None:
        super().__init__(spec, parse)
        self._fetch = fetch

    def first_page(self) -> Page[T]:
        page = self._spec["first_page"]
        data = self._fetch(page)
        return Page(self._items(data), page, data)

    def __iter__(self) -> Iterator[T]:
        page = self._spec["first_page"]
        for _ in range(MAX_PAGES):
            data = self._fetch(page)
            items = self._items(data)
            yield from items
            if self._is_last(data, page, len(items)):
                return
            page += 1

    def to_list(self, limit: int | None = None) -> list[T]:
        out: list[T] = []
        for item in self:
            out.append(item)
            if limit is not None and len(out) >= limit:
                break
        return out


class AsyncPager(_PagerBase[T]):
    """`async for item in client.x.list()`; `await pager.first_page()` for one page."""

    def __init__(self, fetch: Callable[[int], Awaitable[Any]], spec: dict, parse: Callable[[Any], T]) -> None:
        super().__init__(spec, parse)
        self._fetch = fetch

    async def first_page(self) -> Page[T]:
        page = self._spec["first_page"]
        data = await self._fetch(page)
        return Page(self._items(data), page, data)

    async def __aiter__(self) -> AsyncIterator[T]:
        page = self._spec["first_page"]
        for _ in range(MAX_PAGES):
            data = await self._fetch(page)
            items = self._items(data)
            for item in items:
                yield item
            if self._is_last(data, page, len(items)):
                return
            page += 1

    async def to_list(self, limit: int | None = None) -> list[T]:
        out: list[T] = []
        async for item in self:
            out.append(item)
            if limit is not None and len(out) >= limit:
                break
        return out
