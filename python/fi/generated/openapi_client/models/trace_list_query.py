from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceListQuery")


@_attrs_define
class TraceListQuery:
    """
    Attributes:
        project_version_id (UUID):
        trace_ids (str | Unset):
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
        allow_sampled (bool | Unset): Omit for backward-compatible complete bounded pages, which may label total_rows as
            a lower bound. Send false to require an exact total, or true to opt in explicitly to lower-bound totals.
    """

    project_version_id: UUID
    trace_ids: str | Unset = UNSET
    filters: str | Unset = "[]"
    sort_params: str | Unset = "[]"
    page_number: int | Unset = 0
    page_size: int | Unset = 30
    allow_sampled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_version_id = str(self.project_version_id)

        trace_ids = self.trace_ids

        filters = self.filters

        sort_params = self.sort_params

        page_number = self.page_number

        page_size = self.page_size

        allow_sampled = self.allow_sampled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project_version_id": project_version_id,
            }
        )
        if trace_ids is not UNSET:
            field_dict["trace_ids"] = trace_ids
        if filters is not UNSET:
            field_dict["filters"] = filters
        if sort_params is not UNSET:
            field_dict["sort_params"] = sort_params
        if page_number is not UNSET:
            field_dict["page_number"] = page_number
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if allow_sampled is not UNSET:
            field_dict["allow_sampled"] = allow_sampled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        project_version_id = UUID(d.pop("project_version_id"))

        trace_ids = d.pop("trace_ids", UNSET)

        filters = d.pop("filters", UNSET)

        sort_params = d.pop("sort_params", UNSET)

        page_number = d.pop("page_number", UNSET)

        page_size = d.pop("page_size", UNSET)

        allow_sampled = d.pop("allow_sampled", UNSET)

        trace_list_query = cls(
            project_version_id=project_version_id,
            trace_ids=trace_ids,
            filters=filters,
            sort_params=sort_params,
            page_number=page_number,
            page_size=page_size,
            allow_sampled=allow_sampled,
        )

        trace_list_query.additional_properties = d
        return trace_list_query

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
