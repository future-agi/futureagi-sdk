from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DynamicColumnCreateResult")


@_attrs_define
class DynamicColumnCreateResult:
    """
    Attributes:
        message (str):
        new_column_id (UUID):
        new_column_name (str):
    """

    message: str
    new_column_id: UUID
    new_column_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        new_column_id = str(self.new_column_id)

        new_column_name = self.new_column_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "new_column_id": new_column_id,
                "new_column_name": new_column_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        new_column_id = UUID(d.pop("new_column_id"))

        new_column_name = d.pop("new_column_name")

        dynamic_column_create_result = cls(
            message=message,
            new_column_id=new_column_id,
            new_column_name=new_column_name,
        )

        dynamic_column_create_result.additional_properties = d
        return dynamic_column_create_result

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
