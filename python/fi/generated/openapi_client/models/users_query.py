from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UsersQuery")


@_attrs_define
class UsersQuery:
    """
    Attributes:
        project_id (UUID | Unset):
        search (str | Unset):
        page_size (int | Unset):
        current_page_index (int | Unset):
        sort_params (str | Unset): JSON-encoded list of sort params. Default: '[]'.
        filters (str | Unset): JSON-encoded canonical filter list. Default: '[]'.
        export (bool | Unset):  Default: False.
        cursor (str | Unset): Opaque continuation token returned by the previous page. When supplied, do not also send
            the numbered-page parameter.
        cursor_mode (bool | Unset):  Default: False.
        requested_columns (str | Unset): JSON-encoded list of visible Users-table fields. Raw-derived metrics are
            hydrated only when explicitly requested.
        attribute_keys (str | Unset): JSON-encoded list of visible custom user attribute keys. Only these keys (plus
            keys required by filters) are hydrated.
    """

    project_id: UUID | Unset = UNSET
    search: str | Unset = UNSET
    page_size: int | Unset = UNSET
    current_page_index: int | Unset = UNSET
    sort_params: str | Unset = "[]"
    filters: str | Unset = "[]"
    export: bool | Unset = False
    cursor: str | Unset = UNSET
    cursor_mode: bool | Unset = False
    requested_columns: str | Unset = UNSET
    attribute_keys: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_id: str | Unset = UNSET
        if not isinstance(self.project_id, Unset):
            project_id = str(self.project_id)

        search = self.search

        page_size = self.page_size

        current_page_index = self.current_page_index

        sort_params = self.sort_params

        filters = self.filters

        export = self.export

        cursor = self.cursor

        cursor_mode = self.cursor_mode

        requested_columns = self.requested_columns

        attribute_keys = self.attribute_keys

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if search is not UNSET:
            field_dict["search"] = search
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if current_page_index is not UNSET:
            field_dict["current_page_index"] = current_page_index
        if sort_params is not UNSET:
            field_dict["sort_params"] = sort_params
        if filters is not UNSET:
            field_dict["filters"] = filters
        if export is not UNSET:
            field_dict["export"] = export
        if cursor is not UNSET:
            field_dict["cursor"] = cursor
        if cursor_mode is not UNSET:
            field_dict["cursor_mode"] = cursor_mode
        if requested_columns is not UNSET:
            field_dict["requested_columns"] = requested_columns
        if attribute_keys is not UNSET:
            field_dict["attribute_keys"] = attribute_keys

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

        search = d.pop("search", UNSET)

        page_size = d.pop("page_size", UNSET)

        current_page_index = d.pop("current_page_index", UNSET)

        sort_params = d.pop("sort_params", UNSET)

        filters = d.pop("filters", UNSET)

        export = d.pop("export", UNSET)

        cursor = d.pop("cursor", UNSET)

        cursor_mode = d.pop("cursor_mode", UNSET)

        requested_columns = d.pop("requested_columns", UNSET)

        attribute_keys = d.pop("attribute_keys", UNSET)

        users_query = cls(
            project_id=project_id,
            search=search,
            page_size=page_size,
            current_page_index=current_page_index,
            sort_params=sort_params,
            filters=filters,
            export=export,
            cursor=cursor,
            cursor_mode=cursor_mode,
            requested_columns=requested_columns,
            attribute_keys=attribute_keys,
        )

        users_query.additional_properties = d
        return users_query

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
