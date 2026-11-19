"""Pages: the operations with ``x-omega-pagination`` return a :class:`Page`.

- Iterating a page walks every item across pages: ``for item in page`` (sync) or
  ``async for item in page`` (async).
- ``.items`` is the current page, ``.has_more`` / ``.next_cursor`` say whether another follows, and
  ``.next_page()`` fetches it (None at the end). ``.raw`` is the page's whole wire body.
- Cursors are opaque: the SDK never parses or builds one, and sends only the query keys the
  contract declares. A list the server does not page yet returns one page through the same
  interface, so caller code does not change when cursors arrive. A ``window`` list (one page
  bounded by ``limit``) sets ``.truncated`` when more existed.
- A cursor the server repeats ends the walk instead of looping.
"""

from __future__ import annotations

from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    Iterator,
    Mapping,
    Optional,
    TypeVar,
)

from fi._core.policy import PaginationSpec

T = TypeVar("T")


def dig(data: Any, dotted: Optional[str]) -> Any:
    """A dotted field (``page.nextCursor``) of parsed JSON; None when any step is missing."""
    if dotted is None:
        return None
    for part in dotted.split("."):
        if not isinstance(data, Mapping):
            return None
        data = data.get(part)
    return data


class _PageBase(Generic[T]):
    def __init__(
        self, raw: Any, spec: Optional[PaginationSpec], transform: Optional[Callable[[Any], T]], seen: frozenset[str]
    ) -> None:
        self.raw = raw
        items = raw if isinstance(raw, list) else dig(raw, spec.items_field if spec is not None else None)
        values = list(items) if isinstance(items, list) else []
        self.items: list[T] = [transform(v) for v in values] if transform is not None else values
        cursor = dig(raw, spec.next_cursor_field) if spec is not None and spec.style == "cursor" else None
        self.next_cursor: Optional[str] = cursor if isinstance(cursor, str) and cursor and cursor not in seen else None
        flag = dig(raw, spec.has_more_field) if spec is not None else None
        self.has_more: bool = self.next_cursor is not None and (flag is not False)
        self.truncated: bool = (
            bool(dig(raw, spec.truncated_field)) if spec is not None and spec.truncated_field else False
        )
        self._seen = seen | ({self.next_cursor} if self.next_cursor else set())

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(items={len(self.items)}, has_more={self.has_more})"


class Page(_PageBase[T]):
    """One page of a list (sync); iterate it to walk every item across pages."""

    def __init__(
        self,
        raw: Any,
        spec: Optional[PaginationSpec],
        fetch: Callable[[str], Any],
        *,
        transform: Optional[Callable[[Any], T]] = None,
        seen: frozenset[str] = frozenset(),
    ) -> None:
        super().__init__(raw, spec, transform, seen)
        self._spec, self._fetch, self._transform = spec, fetch, transform

    def next_page(self) -> Optional["Page[T]"]:
        """The next page, or None at the end."""
        if not self.has_more or self.next_cursor is None:
            return None
        return Page(self._fetch(self.next_cursor), self._spec, self._fetch, transform=self._transform, seen=self._seen)

    def __iter__(self) -> Iterator[T]:
        page: Optional[Page[T]] = self
        while page is not None:
            yield from page.items
            page = page.next_page()


class AsyncPage(_PageBase[T]):
    """One page of a list (async); ``async for`` walks every item across pages."""

    def __init__(
        self,
        raw: Any,
        spec: Optional[PaginationSpec],
        fetch: Callable[[str], Awaitable[Any]],
        *,
        transform: Optional[Callable[[Any], T]] = None,
        seen: frozenset[str] = frozenset(),
    ) -> None:
        super().__init__(raw, spec, transform, seen)
        self._spec, self._fetch, self._transform = spec, fetch, transform

    async def next_page(self) -> Optional["AsyncPage[T]"]:
        if not self.has_more or self.next_cursor is None:
            return None
        raw = await self._fetch(self.next_cursor)
        return AsyncPage(raw, self._spec, self._fetch, transform=self._transform, seen=self._seen)

    async def __aiter__(self) -> AsyncIterator[T]:
        page: Optional[AsyncPage[T]] = self
        while page is not None:
            for item in page.items:
                yield item
            page = await page.next_page()


def _query(spec: Optional[PaginationSpec], query: Optional[Mapping[str, Any]], cursor: Optional[str]) -> dict[str, Any]:
    out = dict(query or {})
    if cursor is not None:
        if spec is None or spec.cursor_param is None:
            raise ValueError("this list returns a single page; there is no cursor to pass")
        out[spec.cursor_param] = cursor
    return out


def list_page(
    core: Any,
    name: str,
    *,
    path: Any = None,
    query: Optional[Mapping[str, Any]] = None,
    cursor: Optional[str] = None,
    transform: Optional[Callable[[Any], T]] = None,
) -> Page[T]:
    """The first page of a paginated operation (sync), starting at ``cursor`` when given."""
    spec = core.operation(name).pagination

    def fetch(next_cursor: str) -> Any:
        return core.call(name, path=path, query=_query(spec, query, next_cursor))

    return Page(core.call(name, path=path, query=_query(spec, query, cursor)), spec, fetch, transform=transform)


async def alist_page(
    core: Any,
    name: str,
    *,
    path: Any = None,
    query: Optional[Mapping[str, Any]] = None,
    cursor: Optional[str] = None,
    transform: Optional[Callable[[Any], T]] = None,
) -> AsyncPage[T]:
    """The first page of a paginated operation (async)."""
    spec = core.operation(name).pagination

    async def fetch(next_cursor: str) -> Any:
        return await core.call(name, path=path, query=_query(spec, query, next_cursor))

    raw = await core.call(name, path=path, query=_query(spec, query, cursor))
    return AsyncPage(raw, spec, fetch, transform=transform)
