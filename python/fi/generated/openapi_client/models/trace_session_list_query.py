from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceSessionListQuery")


@_attrs_define
class TraceSessionListQuery:
    """
    Attributes:
        project_id (UUID | Unset):
        user_id (str | Unset):
        bookmarked (bool | None | Unset):
        filters (str | Unset): JSON-encoded canonical filter list. On trace, span, session, graph, and eval-task bounded
            reads, created_at/start_time datetime filters support equals, greater_than, greater_than_or_equal, less_than,
            less_than_or_equal, between, not_equals, not_between, is_null, and is_not_null. Missing bounds retain the finite
            default window: 30 days ago for the lower bound and request-time now for the upper bound. Between and
            not_between use half-open [start, end) ranges; not_equals excludes one DateTime64(6) microsecond. Because the
            physical created_at/start_time field is non-null, is_null returns an exact empty result without a ClickHouse
            read and is_not_null preserves the base window. Valid contradictions also return an exact empty result. Default:
            '[]'.
        sort_params (str | Unset): JSON-encoded list of sort params. Default: '[]'.
        page_number (int | Unset): Zero-based numbered page. Pages whose required ordered work exceeds the finite read
            contract return HTTP 422 with code page_depth_exceeded; request an earlier page or narrow the time range.
            Default: 0.
        page_size (int | Unset):  Default: 30.
        cursor (str | Unset): Opaque continuation token returned by the previous page. When supplied, do not also send
            the numbered-page parameter.
        cursor_mode (bool | Unset):  Default: False.
        interval (str | Unset):
        allow_sampled (bool | Unset): Omit for backward-compatible complete bounded pages, which may label total_rows as
            a lower bound. Send false to require an exact total, or true to opt in explicitly to lower-bound totals.
    """

    project_id: UUID | Unset = UNSET
    user_id: str | Unset = UNSET
    bookmarked: bool | None | Unset = UNSET
    filters: str | Unset = "[]"
    sort_params: str | Unset = "[]"
    page_number: int | Unset = 0
    page_size: int | Unset = 30
    cursor: str | Unset = UNSET
    cursor_mode: bool | Unset = False
    interval: str | Unset = UNSET
    allow_sampled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_id: str | Unset = UNSET
        if not isinstance(self.project_id, Unset):
            project_id = str(self.project_id)

        user_id = self.user_id

        bookmarked: bool | None | Unset
        if isinstance(self.bookmarked, Unset):
            bookmarked = UNSET
        else:
            bookmarked = self.bookmarked

        filters = self.filters

        sort_params = self.sort_params

        page_number = self.page_number

        page_size = self.page_size

        cursor = self.cursor

        cursor_mode = self.cursor_mode

        interval = self.interval

        allow_sampled = self.allow_sampled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if bookmarked is not UNSET:
            field_dict["bookmarked"] = bookmarked
        if filters is not UNSET:
            field_dict["filters"] = filters
        if sort_params is not UNSET:
            field_dict["sort_params"] = sort_params
        if page_number is not UNSET:
            field_dict["page_number"] = page_number
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if cursor is not UNSET:
            field_dict["cursor"] = cursor
        if cursor_mode is not UNSET:
            field_dict["cursor_mode"] = cursor_mode
        if interval is not UNSET:
            field_dict["interval"] = interval
        if allow_sampled is not UNSET:
            field_dict["allow_sampled"] = allow_sampled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _project_id = d.pop("project_id", UNSET)
        project_id: UUID | Unset
        if isinstance(_project_id, Unset):
            project_id = UNSET
        else:
            project_id = UUID(_project_id)

        user_id = d.pop("user_id", UNSET)

        def _parse_bookmarked(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        bookmarked = _parse_bookmarked(d.pop("bookmarked", UNSET))

        filters = d.pop("filters", UNSET)

        sort_params = d.pop("sort_params", UNSET)

        page_number = d.pop("page_number", UNSET)

        page_size = d.pop("page_size", UNSET)

        cursor = d.pop("cursor", UNSET)

        cursor_mode = d.pop("cursor_mode", UNSET)

        interval = d.pop("interval", UNSET)

        allow_sampled = d.pop("allow_sampled", UNSET)

        trace_session_list_query = cls(
            project_id=project_id,
            user_id=user_id,
            bookmarked=bookmarked,
            filters=filters,
            sort_params=sort_params,
            page_number=page_number,
            page_size=page_size,
            cursor=cursor,
            cursor_mode=cursor_mode,
            interval=interval,
            allow_sampled=allow_sampled,
        )

        trace_session_list_query.additional_properties = d
        return trace_session_list_query

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
