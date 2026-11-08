from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dataset_list_item import DatasetListItem


T = TypeVar("T", bound="DatasetListResult")


@_attrs_define
class DatasetListResult:
    """
    Attributes:
        datasets (list[DatasetListItem]):
        total_pages (int):
        total_count (int):
    """

    datasets: list[DatasetListItem]
    total_pages: int
    total_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        datasets = []
        for datasets_item_data in self.datasets:
            datasets_item = datasets_item_data.to_dict()
            datasets.append(datasets_item)

        total_pages = self.total_pages

        total_count = self.total_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "datasets": datasets,
                "total_pages": total_pages,
                "total_count": total_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_list_item import DatasetListItem

        d = dict(src_dict)
        datasets = []
        _datasets = d.pop("datasets")
        for datasets_item_data in _datasets:
            datasets_item = DatasetListItem.from_dict(datasets_item_data)

            datasets.append(datasets_item)

        total_pages = d.pop("total_pages")

        total_count = d.pop("total_count")

        dataset_list_result = cls(
            datasets=datasets,
            total_pages=total_pages,
            total_count=total_count,
        )

        dataset_list_result.additional_properties = d
        return dataset_list_result

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
