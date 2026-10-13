from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.hugging_face_dataset_list_item import HuggingFaceDatasetListItem


T = TypeVar("T", bound="HuggingFaceDatasetListResponseResult")


@_attrs_define
class HuggingFaceDatasetListResponseResult:
    """
    Attributes:
        message (str):
        total_datasets (int):
        datasets (list[HuggingFaceDatasetListItem]):
    """

    message: str
    total_datasets: int
    datasets: list[HuggingFaceDatasetListItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        total_datasets = self.total_datasets

        datasets = []
        for datasets_item_data in self.datasets:
            datasets_item = datasets_item_data.to_dict()
            datasets.append(datasets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "total_datasets": total_datasets,
                "datasets": datasets,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hugging_face_dataset_list_item import HuggingFaceDatasetListItem

        d = dict(src_dict)
        message = d.pop("message")

        total_datasets = d.pop("total_datasets")

        datasets = []
        _datasets = d.pop("datasets")
        for datasets_item_data in _datasets:
            datasets_item = HuggingFaceDatasetListItem.from_dict(datasets_item_data)

            datasets.append(datasets_item)

        hugging_face_dataset_list_response_result = cls(
            message=message,
            total_datasets=total_datasets,
            datasets=datasets,
        )

        hugging_face_dataset_list_response_result.additional_properties = d
        return hugging_face_dataset_list_response_result

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
