from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dataset_name_item import DatasetNameItem


T = TypeVar("T", bound="DatasetNamesResult")


@_attrs_define
class DatasetNamesResult:
    """
    Attributes:
        datasets (list[DatasetNameItem]):
    """

    datasets: list[DatasetNameItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        datasets = []
        for datasets_item_data in self.datasets:
            datasets_item = datasets_item_data.to_dict()
            datasets.append(datasets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "datasets": datasets,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_name_item import DatasetNameItem

        d = dict(src_dict)
        datasets = []
        _datasets = d.pop("datasets")
        for datasets_item_data in _datasets:
            datasets_item = DatasetNameItem.from_dict(datasets_item_data)

            datasets.append(datasets_item)

        dataset_names_result = cls(
            datasets=datasets,
        )

        dataset_names_result.additional_properties = d
        return dataset_names_result

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
