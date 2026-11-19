"""FA catalog adapters over the root client's existing HTTP pool and error tree.

Paths and envelope/pagination metadata come only from generated operations. A DRF
next link contributes a page number, never an origin or URL to follow.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit

from fi._core.core_http import check_redirect, invalid_json
from fi._core.errors import api_error
from fi._core.pagination import AsyncPage, Page, dig
from fi._core.policy import PaginationSpec
from fi._core.request import build_body, build_path, build_query
from fi._credentials import resolve as resolve_credentials
from fi.errors import BadRequestError, FutureAGIAPIError, NotFoundError


def _headers(client: Any) -> dict[str, str]:
    options = client._options
    credentials = resolve_credentials(options.api_key, options.secret_key, client.base_url,
        workspace_id=options.workspace_id, organization_id=options.organization_id)
    return {name: value for name, value in (
        ("X-Workspace-Id", credentials.workspace_id),
        ("X-Organization-Id", credentials.organization_id),
    ) if value is not None}


def _payload(response: Any, unwrap: str | None) -> Any:
    check_redirect(response, "catalog")
    try:
        value = response.json() if response.content else None
    except ValueError:
        if response.status_code < 400:
            raise invalid_json(response) from None
        value = None
    if response.status_code >= 400:
        raise api_error(response.status_code, value, response.headers)
    if unwrap is not None and isinstance(value, Mapping) and unwrap in value:
        return value[unwrap]
    return value


def _arguments(operation: Any, path: Any, query: Any, body: Any) -> dict[str, Any]:
    spec, _, pagination = operation
    query = dict(query)
    if pagination:
        query.setdefault(pagination["page_param"], pagination["first_page"])
    encoded = build_body(spec, body)
    # Free-form paging kwargs belong to FA's query serializer. Never translate
    # bases or mask its typed 400 with an SDK ConfigurationError. Non-paging
    # undeclared parameters retain the existing fail-closed policy.
    paging = {"page", "limit", "page_size", "page_number", "offset", "cursor",
              "cursor_mode", "current_page_index", "page_token"}
    wire_spec = replace(spec, query=tuple(dict.fromkeys((*spec.query, *(k for k in query if k in paging)))))
    return {
        "method": spec.method,
        "url": build_path(spec, path),
        "params": build_query(wire_spec, query),
        "content": encoded.content,
        "headers": {"Content-Type": encoded.content_type} if encoded.content_type else {},
        "extensions": {"fi.retry": {"class": spec.retry_class}},
    }


def _page(raw: Any, pagination: Any, query: Mapping[str, Any], *, page_size: int | None = None) -> dict[str, Any]:
    items = dig(raw, pagination["items"])
    if not isinstance(items, list):
        raise FutureAGIAPIError(200, None, code="invalid_page", message="The response is missing its declared page items")
    requested = query.get(pagination["page_param"], pagination["first_page"])
    # DRF resolves "last" server-side. A short final page cannot reveal the page
    # size, so never infer a continuation from its count or probe beyond it.
    if requested == "last":
        return {"items": items, "next": None, "response": raw, "guess": False}
    resolved = dig(raw, pagination.get("current_page"))
    current = resolved if type(resolved) is int and resolved >= pagination["first_page"] else int(requested)
    following = None
    link = dig(raw, pagination.get("next"))
    if link:
        # Never fetch a supplied URL. Even a foreign next link can only select the
        # next numbered page of this same declared operation.
        values = parse_qs(urlsplit(str(link)).query).get(pagination["page_param"], [])
        if values:
            try:
                candidate = int(values[0])
                if candidate > current:
                    following = str(candidate)
            except ValueError:
                pass
    total = dig(raw, pagination.get("total_items"))
    guess = False
    if isinstance(total, int) and items:
        # On entry (including a resumed page), the requested limit may exceed
        # the server cap. Learn the effective size before deciding continuation;
        # later short pages must still use that same size to count prior rows.
        size = len(items) if page_size is None else page_size
        consumed = (current - pagination["first_page"]) * size + len(items)
        if size > 0 and consumed < total:
            following = str(current + 1)
            # A resumed first page shorter than the size asked for is either the last
            # page or a server-capped one; only the next page can tell.
            resumed = page_size is None and current > pagination["first_page"]
            guess = resumed and _short(items, query, pagination)
    return {"items": items, "next": following if items else None, "response": raw, "guess": guess}


def _short(items: list[Any], query: Mapping[str, Any], pagination: Any) -> bool:
    try:
        return len(items) < int(query[pagination["size_param"]])
    except (KeyError, TypeError, ValueError):
        return True


# The end of a walk whose guessed next page does not exist. FA's dataset optimization
# list answers a page past the end with 400 (its list view turns the paginator's
# not-found into a bad request); a plain paginated view answers 404.
_PAST_END = (BadRequestError, NotFoundError)


def _end() -> dict[str, Any]:
    return {"items": [], "next": None, "response": None, "guess": False}


_PAGE = PaginationSpec("cursor", "items", cursor_param="page", next_cursor_field="next")


class _CatalogPage(Page[Any]):
    def __init__(self, value: Any, fetch: Any, seen: frozenset[str] = frozenset()) -> None:
        super().__init__(value, _PAGE, fetch, seen=seen)
        self.raw = value["response"]

    def next_page(self) -> Any:
        if not self.has_more or self.next_cursor is None:
            return None
        return _CatalogPage(self._fetch(self.next_cursor), self._fetch, self._seen)


class _AsyncCatalogPage(AsyncPage[Any]):
    def __init__(self, value: Any, fetch: Any, seen: frozenset[str] = frozenset()) -> None:
        super().__init__(value, _PAGE, fetch, seen=seen)
        self.raw = value["response"]

    async def next_page(self) -> Any:
        if not self.has_more or self.next_cursor is None:
            return None
        return _AsyncCatalogPage(await self._fetch(self.next_cursor), self._fetch, self._seen)


class Resource:
    """A namespace sharing the root's generated client, credentials and connection pool."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def _call(self, operation: Any, *, path: Any, query: Any, body: Any) -> Any:
        _, unwrap, pagination = operation

        def request(q: Any) -> Any:
            arguments = _arguments(operation, path, q, body)
            arguments["headers"].update(_headers(self._client))
            response = self._client.generated_client.get_httpx_client().request(**arguments)
            return _payload(response, unwrap)

        raw = request(query)
        if pagination is None:
            return raw

        query = dict(query)
        first = _page(raw, pagination, query)
        page_size = len(first["items"])
        probe = first["next"] if first["guess"] else None
        # Keep the wire limit stable: a resumed final page may be shorter than
        # the cap. Changing the limit would change offsets and duplicate rows.

        def fetch(cursor: str) -> Any:
            q = {**query, pagination["page_param"]: int(cursor)}
            try:
                return _page(request(q), pagination, q, page_size=page_size)
            except _PAST_END:
                if cursor != probe:
                    raise
                return _end()

        return _CatalogPage(first, fetch)


class AsyncResource:
    """Async namespace using the same root client's async HTTP pool."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def _call(self, operation: Any, *, path: Any, query: Any, body: Any) -> Any:
        _, unwrap, pagination = operation

        async def request(q: Any) -> Any:
            arguments = _arguments(operation, path, q, body)
            arguments["headers"].update(_headers(self._client))
            response = await self._client.generated_client.get_async_httpx_client().request(**arguments)
            return _payload(response, unwrap)

        raw = await request(query)
        if pagination is None:
            return raw

        query = dict(query)
        first = _page(raw, pagination, query)
        page_size = len(first["items"])
        probe = first["next"] if first["guess"] else None
        # Keep the wire limit stable: a resumed final page may be shorter than
        # the cap. Changing the limit would change offsets and duplicate rows.

        async def fetch(cursor: str) -> Any:
            q = {**query, pagination["page_param"]: int(cursor)}
            try:
                return _page(await request(q), pagination, q, page_size=page_size)
            except _PAST_END:
                if cursor != probe:
                    raise
                return _end()

        return _AsyncCatalogPage(first, fetch)
