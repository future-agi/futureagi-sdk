from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueExportColumnMapping")


@_attrs_define
class QueueExportColumnMapping:
    """
    Attributes:
        field (str | Unset):
        id (str | Unset):
        column (str | Unset):
        enabled (bool | Unset):  Default: True.
    """

    field: str | Unset = UNSET
    id: str | Unset = UNSET
    column: str | Unset = UNSET
    enabled: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field = self.field

        id = self.id

        column = self.column

        enabled = self.enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if field is not UNSET:
            field_dict["field"] = field
        if id is not UNSET:
            field_dict["id"] = id
        if column is not UNSET:
            field_dict["column"] = column
        if enabled is not UNSET:
            field_dict["enabled"] = enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        field = d.pop("field", UNSET)

        id = d.pop("id", UNSET)

        column = d.pop("column", UNSET)

        enabled = d.pop("enabled", UNSET)

        queue_export_column_mapping = cls(
            field=field,
            id=id,
            column=column,
            enabled=enabled,
        )

        queue_export_column_mapping.additional_properties = d
        return queue_export_column_mapping

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
