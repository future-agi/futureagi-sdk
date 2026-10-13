from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AddRowsFromFileRequest")


@_attrs_define
class AddRowsFromFileRequest:
    """
    Attributes:
        dataset_id (UUID):
        file (str | Unset):
        model_type (str | Unset):
    """

    dataset_id: UUID
    file: str | Unset = UNSET
    model_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = str(self.dataset_id)

        file = self.file

        model_type = self.model_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
            }
        )
        if file is not UNSET:
            field_dict["file"] = file
        if model_type is not UNSET:
            field_dict["model_type"] = model_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataset_id = UUID(d.pop("dataset_id"))

        file = d.pop("file", UNSET)

        model_type = d.pop("model_type", UNSET)

        add_rows_from_file_request = cls(
            dataset_id=dataset_id,
            file=file,
            model_type=model_type,
        )

        add_rows_from_file_request.additional_properties = d
        return add_rows_from_file_request

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
