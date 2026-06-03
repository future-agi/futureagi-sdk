from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HuggingFaceDatasetCreateRequest")


@_attrs_define
class HuggingFaceDatasetCreateRequest:
    """
    Attributes:
        huggingface_dataset_name (str):
        huggingface_dataset_split (str):
        name (str | Unset):  Default: ''.
        model_type (str | Unset):  Default: ''.
        num_rows (int | Unset):
        huggingface_dataset_config (str | Unset):
    """

    huggingface_dataset_name: str
    huggingface_dataset_split: str
    name: str | Unset = ""
    model_type: str | Unset = ""
    num_rows: int | Unset = UNSET
    huggingface_dataset_config: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        huggingface_dataset_name = self.huggingface_dataset_name

        huggingface_dataset_split = self.huggingface_dataset_split

        name = self.name

        model_type = self.model_type

        num_rows = self.num_rows

        huggingface_dataset_config = self.huggingface_dataset_config

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "huggingface_dataset_name": huggingface_dataset_name,
                "huggingface_dataset_split": huggingface_dataset_split,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if model_type is not UNSET:
            field_dict["model_type"] = model_type
        if num_rows is not UNSET:
            field_dict["num_rows"] = num_rows
        if huggingface_dataset_config is not UNSET:
            field_dict["huggingface_dataset_config"] = huggingface_dataset_config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        huggingface_dataset_name = d.pop("huggingface_dataset_name")

        huggingface_dataset_split = d.pop("huggingface_dataset_split")

        name = d.pop("name", UNSET)

        model_type = d.pop("model_type", UNSET)

        num_rows = d.pop("num_rows", UNSET)

        huggingface_dataset_config = d.pop("huggingface_dataset_config", UNSET)

        hugging_face_dataset_create_request = cls(
            huggingface_dataset_name=huggingface_dataset_name,
            huggingface_dataset_split=huggingface_dataset_split,
            name=name,
            model_type=model_type,
            num_rows=num_rows,
            huggingface_dataset_config=huggingface_dataset_config,
        )

        hugging_face_dataset_create_request.additional_properties = d
        return hugging_face_dataset_create_request

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
