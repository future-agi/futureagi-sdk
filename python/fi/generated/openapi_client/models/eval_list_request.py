from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eval_list_request_owner_filter import EvalListRequestOwnerFilter
from ..models.eval_list_request_sort_by import EvalListRequestSortBy
from ..models.eval_list_request_sort_order import EvalListRequestSortOrder
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_list_filters import EvalListFilters


T = TypeVar("T", bound="EvalListRequest")


@_attrs_define
class EvalListRequest:
    """
    Attributes:
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 25.
        search (None | str | Unset):
        owner_filter (EvalListRequestOwnerFilter | Unset):  Default: EvalListRequestOwnerFilter.ALL.
        filters (EvalListFilters | Unset):
        sort_by (EvalListRequestSortBy | Unset):  Default: EvalListRequestSortBy.UPDATED_AT.
        sort_order (EvalListRequestSortOrder | Unset):  Default: EvalListRequestSortOrder.DESC.
    """

    page: int | Unset = 0
    page_size: int | Unset = 25
    search: None | str | Unset = UNSET
    owner_filter: EvalListRequestOwnerFilter | Unset = EvalListRequestOwnerFilter.ALL
    filters: EvalListFilters | Unset = UNSET
    sort_by: EvalListRequestSortBy | Unset = EvalListRequestSortBy.UPDATED_AT
    sort_order: EvalListRequestSortOrder | Unset = EvalListRequestSortOrder.DESC
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        page = self.page

        page_size = self.page_size

        search: None | str | Unset
        if isinstance(self.search, Unset):
            search = UNSET
        else:
            search = self.search

        owner_filter: str | Unset = UNSET
        if not isinstance(self.owner_filter, Unset):
            owner_filter = self.owner_filter.value

        filters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = self.filters.to_dict()

        sort_by: str | Unset = UNSET
        if not isinstance(self.sort_by, Unset):
            sort_by = self.sort_by.value

        sort_order: str | Unset = UNSET
        if not isinstance(self.sort_order, Unset):
            sort_order = self.sort_order.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if page is not UNSET:
            field_dict["page"] = page
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if search is not UNSET:
            field_dict["search"] = search
        if owner_filter is not UNSET:
            field_dict["owner_filter"] = owner_filter
        if filters is not UNSET:
            field_dict["filters"] = filters
        if sort_by is not UNSET:
            field_dict["sort_by"] = sort_by
        if sort_order is not UNSET:
            field_dict["sort_order"] = sort_order

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_list_filters import EvalListFilters

        d = dict(src_dict)
        page = d.pop("page", UNSET)

        page_size = d.pop("page_size", UNSET)

        def _parse_search(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        search = _parse_search(d.pop("search", UNSET))

        _owner_filter = d.pop("owner_filter", UNSET)
        owner_filter: EvalListRequestOwnerFilter | Unset
        if isinstance(_owner_filter, Unset):
            owner_filter = UNSET
        else:
            owner_filter = EvalListRequestOwnerFilter(_owner_filter)

        _filters = d.pop("filters", UNSET)
        filters: EvalListFilters | Unset
        if isinstance(_filters, Unset):
            filters = UNSET
        else:
            filters = EvalListFilters.from_dict(_filters)

        _sort_by = d.pop("sort_by", UNSET)
        sort_by: EvalListRequestSortBy | Unset
        if isinstance(_sort_by, Unset):
            sort_by = UNSET
        else:
            sort_by = EvalListRequestSortBy(_sort_by)

        _sort_order = d.pop("sort_order", UNSET)
        sort_order: EvalListRequestSortOrder | Unset
        if isinstance(_sort_order, Unset):
            sort_order = UNSET
        else:
            sort_order = EvalListRequestSortOrder(_sort_order)

        eval_list_request = cls(
            page=page,
            page_size=page_size,
            search=search,
            owner_filter=owner_filter,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        eval_list_request.additional_properties = d
        return eval_list_request

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
