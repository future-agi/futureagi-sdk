from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateDatasetFromLocalFileRequest")


@_attrs_define
class CreateDatasetFromLocalFileRequest:
    """
    Attributes:
        file (str | Unset):
        new_dataset_name (str | Unset):
        model_type (str | Unset):
        source (str | Unset):
    """

    file: str | Unset = UNSET
    new_dataset_name: str | Unset = UNSET
    model_type: str | Unset = UNSET
    source: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        new_dataset_name = self.new_dataset_name

        model_type = self.model_type

        source = self.source

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file is not UNSET:
            field_dict["file"] = file
        if new_dataset_name is not UNSET:
            field_dict["new_dataset_name"] = new_dataset_name
        if model_type is not UNSET:
            field_dict["model_type"] = model_type
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = d.pop("file", UNSET)

        new_dataset_name = d.pop("new_dataset_name", UNSET)

        model_type = d.pop("model_type", UNSET)

        source = d.pop("source", UNSET)

        create_dataset_from_local_file_request = cls(
            file=file,
            new_dataset_name=new_dataset_name,
            model_type=model_type,
            source=source,
        )

        create_dataset_from_local_file_request.additional_properties = d
        return create_dataset_from_local_file_request

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
