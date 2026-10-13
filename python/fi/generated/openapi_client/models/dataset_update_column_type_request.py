from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetUpdateColumnTypeRequest")


@_attrs_define
class DatasetUpdateColumnTypeRequest:
    """
    Attributes:
        new_column_type (str):
        preview (bool | Unset):  Default: True.
        force_update (bool | Unset):  Default: False.
    """

    new_column_type: str
    preview: bool | Unset = True
    force_update: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        new_column_type = self.new_column_type

        preview = self.preview

        force_update = self.force_update

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "new_column_type": new_column_type,
            }
        )
        if preview is not UNSET:
            field_dict["preview"] = preview
        if force_update is not UNSET:
            field_dict["force_update"] = force_update

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        new_column_type = d.pop("new_column_type")

        preview = d.pop("preview", UNSET)

        force_update = d.pop("force_update", UNSET)

        dataset_update_column_type_request = cls(
            new_column_type=new_column_type,
            preview=preview,
            force_update=force_update,
        )

        dataset_update_column_type_request.additional_properties = d
        return dataset_update_column_type_request

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
