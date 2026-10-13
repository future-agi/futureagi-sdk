from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.column_definition_data_type import ColumnDefinitionDataType

T = TypeVar("T", bound="ColumnDefinition")


@_attrs_define
class ColumnDefinition:
    """
    Attributes:
        name (str):
        data_type (ColumnDefinitionDataType):
        description (str):
    """

    name: str
    data_type: ColumnDefinitionDataType
    description: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        data_type = self.data_type.value

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "data_type": data_type,
                "description": description,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        data_type = ColumnDefinitionDataType(d.pop("data_type"))

        description = d.pop("description")

        column_definition = cls(
            name=name,
            data_type=data_type,
            description=description,
        )

        column_definition.additional_properties = d
        return column_definition

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
