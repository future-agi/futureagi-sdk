from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateEmptyDatasetRequest")


@_attrs_define
class CreateEmptyDatasetRequest:
    """
    Attributes:
        new_dataset_name (str):
        model_type (str | Unset):
        is_sdk (bool | Unset):  Default: False.
        row (int | Unset):
    """

    new_dataset_name: str
    model_type: str | Unset = UNSET
    is_sdk: bool | Unset = False
    row: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        new_dataset_name = self.new_dataset_name

        model_type = self.model_type

        is_sdk = self.is_sdk

        row = self.row

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "new_dataset_name": new_dataset_name,
            }
        )
        if model_type is not UNSET:
            field_dict["model_type"] = model_type
        if is_sdk is not UNSET:
            field_dict["is_sdk"] = is_sdk
        if row is not UNSET:
            field_dict["row"] = row

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        new_dataset_name = d.pop("new_dataset_name")

        model_type = d.pop("model_type", UNSET)

        is_sdk = d.pop("is_sdk", UNSET)

        row = d.pop("row", UNSET)

        create_empty_dataset_request = cls(
            new_dataset_name=new_dataset_name,
            model_type=model_type,
            is_sdk=is_sdk,
            row=row,
        )

        create_empty_dataset_request.additional_properties = d
        return create_empty_dataset_request

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
