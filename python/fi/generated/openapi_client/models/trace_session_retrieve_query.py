from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceSessionRetrieveQuery")


@_attrs_define
class TraceSessionRetrieveQuery:
    """
    Attributes:
        navigation_context (str | Unset): JSON-encoded object.
        user_id (str | Unset):
        filters (str | Unset): JSON-encoded canonical filter list. Default: '[]'.
        sort_params (str | Unset): JSON-encoded list of sort params. Default: '[]'.
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
    """

    navigation_context: str | Unset = UNSET
    user_id: str | Unset = UNSET
    filters: str | Unset = "[]"
    sort_params: str | Unset = "[]"
    page_number: int | Unset = 0
    page_size: int | Unset = 30
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        navigation_context = self.navigation_context

        user_id = self.user_id

        filters = self.filters

        sort_params = self.sort_params

        page_number = self.page_number

        page_size = self.page_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if navigation_context is not UNSET:
            field_dict["navigation_context"] = navigation_context
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if filters is not UNSET:
            field_dict["filters"] = filters
        if sort_params is not UNSET:
            field_dict["sort_params"] = sort_params
        if page_number is not UNSET:
            field_dict["page_number"] = page_number
        if page_size is not UNSET:
            field_dict["page_size"] = page_size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        navigation_context = d.pop("navigation_context", UNSET)

        user_id = d.pop("user_id", UNSET)

        filters = d.pop("filters", UNSET)

        sort_params = d.pop("sort_params", UNSET)

        page_number = d.pop("page_number", UNSET)

        page_size = d.pop("page_size", UNSET)

        trace_session_retrieve_query = cls(
            navigation_context=navigation_context,
            user_id=user_id,
            filters=filters,
            sort_params=sort_params,
            page_number=page_number,
            page_size=page_size,
        )

        trace_session_retrieve_query.additional_properties = d
        return trace_session_retrieve_query

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
