from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.hugging_face_dataset_config_result_dataset_info import (
        HuggingFaceDatasetConfigResultDatasetInfo,
    )


T = TypeVar("T", bound="HuggingFaceDatasetConfigResult")


@_attrs_define
class HuggingFaceDatasetConfigResult:
    """
    Attributes:
        message (str):
        dataset_info (HuggingFaceDatasetConfigResultDatasetInfo):
    """

    message: str
    dataset_info: HuggingFaceDatasetConfigResultDatasetInfo
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        dataset_info = self.dataset_info.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "dataset_info": dataset_info,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hugging_face_dataset_config_result_dataset_info import (
            HuggingFaceDatasetConfigResultDatasetInfo,
        )

        d = dict(src_dict)
        message = d.pop("message")

        dataset_info = HuggingFaceDatasetConfigResultDatasetInfo.from_dict(
            d.pop("dataset_info")
        )

        hugging_face_dataset_config_result = cls(
            message=message,
            dataset_info=dataset_info,
        )

        hugging_face_dataset_config_result.additional_properties = d
        return hugging_face_dataset_config_result

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
