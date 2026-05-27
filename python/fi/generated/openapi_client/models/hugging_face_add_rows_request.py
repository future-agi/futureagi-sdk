from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HuggingFaceAddRowsRequest")


@_attrs_define
class HuggingFaceAddRowsRequest:
    """
    Attributes:
        huggingface_dataset_name (str):
        huggingface_dataset_config (str):
        huggingface_dataset_split (str):
        num_rows (int | Unset):
    """

    huggingface_dataset_name: str
    huggingface_dataset_config: str
    huggingface_dataset_split: str
    num_rows: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        huggingface_dataset_name = self.huggingface_dataset_name

        huggingface_dataset_config = self.huggingface_dataset_config

        huggingface_dataset_split = self.huggingface_dataset_split

        num_rows = self.num_rows

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "huggingface_dataset_name": huggingface_dataset_name,
                "huggingface_dataset_config": huggingface_dataset_config,
                "huggingface_dataset_split": huggingface_dataset_split,
            }
        )
        if num_rows is not UNSET:
            field_dict["num_rows"] = num_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        huggingface_dataset_name = d.pop("huggingface_dataset_name")

        huggingface_dataset_config = d.pop("huggingface_dataset_config")

        huggingface_dataset_split = d.pop("huggingface_dataset_split")

        num_rows = d.pop("num_rows", UNSET)

        hugging_face_add_rows_request = cls(
            huggingface_dataset_name=huggingface_dataset_name,
            huggingface_dataset_config=huggingface_dataset_config,
            huggingface_dataset_split=huggingface_dataset_split,
            num_rows=num_rows,
        )

        hugging_face_add_rows_request.additional_properties = d
        return hugging_face_add_rows_request

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
