from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetUpdateCellValueRequest")


@_attrs_define
class DatasetUpdateCellValueRequest:
    """
    Attributes:
        row_id (UUID):
        column_id (UUID):
        new_value (None | str | Unset): New cell value. Accepts JSON primitives or multipart file uploads.
    """

    row_id: UUID
    column_id: UUID
    new_value: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        row_id = str(self.row_id)

        column_id = str(self.column_id)

        new_value: None | str | Unset
        if isinstance(self.new_value, Unset):
            new_value = UNSET
        else:
            new_value = self.new_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "row_id": row_id,
                "column_id": column_id,
            }
        )
        if new_value is not UNSET:
            field_dict["new_value"] = new_value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        row_id = UUID(d.pop("row_id"))

        column_id = UUID(d.pop("column_id"))

        def _parse_new_value(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        new_value = _parse_new_value(d.pop("new_value", UNSET))

        dataset_update_cell_value_request = cls(
            row_id=row_id,
            column_id=column_id,
            new_value=new_value,
        )

        dataset_update_cell_value_request.additional_properties = d
        return dataset_update_cell_value_request

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
