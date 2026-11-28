from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetStaticColumnRequest")


@_attrs_define
class DatasetStaticColumnRequest:
    """
    Attributes:
        new_column_name (str):
        column_type (str):
        source (str | Unset):
    """

    new_column_name: str
    column_type: str
    source: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        new_column_name = self.new_column_name

        column_type = self.column_type

        source = self.source

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "new_column_name": new_column_name,
                "column_type": column_type,
            }
        )
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        new_column_name = d.pop("new_column_name")

        column_type = d.pop("column_type")

        source = d.pop("source", UNSET)

        dataset_static_column_request = cls(
            new_column_name=new_column_name,
            column_type=column_type,
            source=source,
        )

        dataset_static_column_request.additional_properties = d
        return dataset_static_column_request

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
