from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.preview_dataset_operation_result_item import (
        PreviewDatasetOperationResultItem,
    )


T = TypeVar("T", bound="PreviewDatasetOperationResult")


@_attrs_define
class PreviewDatasetOperationResult:
    """
    Attributes:
        message (str):
        preview_results (list[PreviewDatasetOperationResultItem]):
        sample_size (int):
    """

    message: str
    preview_results: list[PreviewDatasetOperationResultItem]
    sample_size: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        preview_results = []
        for preview_results_item_data in self.preview_results:
            preview_results_item = preview_results_item_data.to_dict()
            preview_results.append(preview_results_item)

        sample_size = self.sample_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "preview_results": preview_results,
                "sample_size": sample_size,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.preview_dataset_operation_result_item import (
            PreviewDatasetOperationResultItem,
        )

        d = dict(src_dict)
        message = d.pop("message")

        preview_results = []
        _preview_results = d.pop("preview_results")
        for preview_results_item_data in _preview_results:
            preview_results_item = PreviewDatasetOperationResultItem.from_dict(
                preview_results_item_data
            )

            preview_results.append(preview_results_item)

        sample_size = d.pop("sample_size")

        preview_dataset_operation_result = cls(
            message=message,
            preview_results=preview_results,
            sample_size=sample_size,
        )

        preview_dataset_operation_result.additional_properties = d
        return preview_dataset_operation_result

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
