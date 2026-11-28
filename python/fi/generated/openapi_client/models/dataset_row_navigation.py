from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetRowNavigation")


@_attrs_define
class DatasetRowNavigation:
    """
    Attributes:
        row_id (list[UUID] | Unset):
    """

    row_id: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        row_id: list[str] | Unset = UNSET
        if not isinstance(self.row_id, Unset):
            row_id = []
            for row_id_item_data in self.row_id:
                row_id_item = str(row_id_item_data)
                row_id.append(row_id_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if row_id is not UNSET:
            field_dict["row_id"] = row_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _row_id = d.pop("row_id", UNSET)
        row_id: list[UUID] | Unset = UNSET
        if _row_id is not UNSET:
            row_id = []
            for row_id_item_data in _row_id:
                row_id_item = UUID(row_id_item_data)

                row_id.append(row_id_item)

        dataset_row_navigation = cls(
            row_id=row_id,
        )

        dataset_row_navigation.additional_properties = d
        return dataset_row_navigation

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
