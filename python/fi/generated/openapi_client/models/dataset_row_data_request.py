from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_row_data_request_filters_item import (
        DatasetRowDataRequestFiltersItem,
    )
    from ..models.dataset_row_data_request_sort_item import (
        DatasetRowDataRequestSortItem,
    )


T = TypeVar("T", bound="DatasetRowDataRequest")


@_attrs_define
class DatasetRowDataRequest:
    """
    Attributes:
        row_id (UUID):
        filters (list[DatasetRowDataRequestFiltersItem] | Unset):
        sort (list[DatasetRowDataRequestSortItem] | Unset):
    """

    row_id: UUID
    filters: list[DatasetRowDataRequestFiltersItem] | Unset = UNSET
    sort: list[DatasetRowDataRequestSortItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        row_id = str(self.row_id)

        filters: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = []
            for filters_item_data in self.filters:
                filters_item = filters_item_data.to_dict()
                filters.append(filters_item)

        sort: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.sort, Unset):
            sort = []
            for sort_item_data in self.sort:
                sort_item = sort_item_data.to_dict()
                sort.append(sort_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "row_id": row_id,
            }
        )
        if filters is not UNSET:
            field_dict["filters"] = filters
        if sort is not UNSET:
            field_dict["sort"] = sort

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_row_data_request_filters_item import (
            DatasetRowDataRequestFiltersItem,
        )
        from ..models.dataset_row_data_request_sort_item import (
            DatasetRowDataRequestSortItem,
        )

        d = dict(src_dict)
        row_id = UUID(d.pop("row_id"))

        _filters = d.pop("filters", UNSET)
        filters: list[DatasetRowDataRequestFiltersItem] | Unset = UNSET
        if _filters is not UNSET:
            filters = []
            for filters_item_data in _filters:
                filters_item = DatasetRowDataRequestFiltersItem.from_dict(
                    filters_item_data
                )

                filters.append(filters_item)

        _sort = d.pop("sort", UNSET)
        sort: list[DatasetRowDataRequestSortItem] | Unset = UNSET
        if _sort is not UNSET:
            sort = []
            for sort_item_data in _sort:
                sort_item = DatasetRowDataRequestSortItem.from_dict(sort_item_data)

                sort.append(sort_item)

        dataset_row_data_request = cls(
            row_id=row_id,
            filters=filters,
            sort=sort,
        )

        dataset_row_data_request.additional_properties = d
        return dataset_row_data_request

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
