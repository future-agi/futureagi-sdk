from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceVoiceCallListQuery")


@_attrs_define
class TraceVoiceCallListQuery:
    """
    Attributes:
        project_id (UUID):
        filters (str | Unset): JSON-encoded canonical filter list. Default: '[]'.
        attribute_keys (str | Unset): JSON-encoded list of custom attribute keys to include as CSV columns. Comma-
            separated simple keys remain supported.
        page (int | Unset): One-based numbered page. Pages whose required ordered work exceeds the finite read contract
            return HTTP 422 with code page_depth_exceeded; request an earlier page, use the additive continuation cursor, or
            narrow the time range. Default: 1.
        page_size (int | Unset):  Default: 30.
        remove_simulation_calls (bool | Unset):  Default: False.
        cursor (str | Unset): Opaque continuation token returned by the previous page. When supplied, do not also send
            the numbered-page parameter.
        cursor_mode (bool | Unset):  Default: False.
        allow_sampled (bool | Unset): Omit for backward-compatible complete bounded pages, which may label count as a
            lower bound. Send false to require an exact total. Send true to opt in explicitly to lower-bound totals and, on
            the first page, a clearly labelled bounded partial result when the full ordered prefix cannot be proven inside
            the read budget.
    """

    project_id: UUID
    filters: str | Unset = "[]"
    attribute_keys: str | Unset = UNSET
    page: int | Unset = 1
    page_size: int | Unset = 30
    remove_simulation_calls: bool | Unset = False
    cursor: str | Unset = UNSET
    cursor_mode: bool | Unset = False
    allow_sampled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_id = str(self.project_id)

        filters = self.filters

        attribute_keys = self.attribute_keys

        page = self.page

        page_size = self.page_size

        remove_simulation_calls = self.remove_simulation_calls

        cursor = self.cursor

        cursor_mode = self.cursor_mode

        allow_sampled = self.allow_sampled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project_id": project_id,
            }
        )
        if filters is not UNSET:
            field_dict["filters"] = filters
        if attribute_keys is not UNSET:
            field_dict["attribute_keys"] = attribute_keys
        if page is not UNSET:
            field_dict["page"] = page
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if remove_simulation_calls is not UNSET:
            field_dict["remove_simulation_calls"] = remove_simulation_calls
        if cursor is not UNSET:
            field_dict["cursor"] = cursor
        if cursor_mode is not UNSET:
            field_dict["cursor_mode"] = cursor_mode
        if allow_sampled is not UNSET:
            field_dict["allow_sampled"] = allow_sampled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        project_id = UUID(d.pop("project_id"))

        filters = d.pop("filters", UNSET)

        attribute_keys = d.pop("attribute_keys", UNSET)

        page = d.pop("page", UNSET)

        page_size = d.pop("page_size", UNSET)

        remove_simulation_calls = d.pop("remove_simulation_calls", UNSET)

        cursor = d.pop("cursor", UNSET)

        cursor_mode = d.pop("cursor_mode", UNSET)

        allow_sampled = d.pop("allow_sampled", UNSET)

        trace_voice_call_list_query = cls(
            project_id=project_id,
            filters=filters,
            attribute_keys=attribute_keys,
            page=page,
            page_size=page_size,
            remove_simulation_calls=remove_simulation_calls,
            cursor=cursor,
            cursor_mode=cursor_mode,
            allow_sampled=allow_sampled,
        )

        trace_voice_call_list_query.additional_properties = d
        return trace_voice_call_list_query

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
