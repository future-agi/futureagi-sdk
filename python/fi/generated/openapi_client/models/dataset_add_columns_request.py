from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dataset_add_columns_request_new_columns_data_item import (
        DatasetAddColumnsRequestNewColumnsDataItem,
    )


T = TypeVar("T", bound="DatasetAddColumnsRequest")


@_attrs_define
class DatasetAddColumnsRequest:
    """
    Attributes:
        new_columns_data (list[DatasetAddColumnsRequestNewColumnsDataItem]):
    """

    new_columns_data: list[DatasetAddColumnsRequestNewColumnsDataItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        new_columns_data = []
        for new_columns_data_item_data in self.new_columns_data:
            new_columns_data_item = new_columns_data_item_data.to_dict()
            new_columns_data.append(new_columns_data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "new_columns_data": new_columns_data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_add_columns_request_new_columns_data_item import (
            DatasetAddColumnsRequestNewColumnsDataItem,
        )

        d = dict(src_dict)
        new_columns_data = []
        _new_columns_data = d.pop("new_columns_data")
        for new_columns_data_item_data in _new_columns_data:
            new_columns_data_item = (
                DatasetAddColumnsRequestNewColumnsDataItem.from_dict(
                    new_columns_data_item_data
                )
            )

            new_columns_data.append(new_columns_data_item)

        dataset_add_columns_request = cls(
            new_columns_data=new_columns_data,
        )

        dataset_add_columns_request.additional_properties = d
        return dataset_add_columns_request

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
