from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DuplicateRowsRequest")


@_attrs_define
class DuplicateRowsRequest:
    """
    Attributes:
        row_ids (list[UUID] | Unset):
        selected_all_rows (bool | Unset):  Default: False.
        num_copies (int | Unset):  Default: 1.
    """

    row_ids: list[UUID] | Unset = UNSET
    selected_all_rows: bool | Unset = False
    num_copies: int | Unset = 1
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        row_ids: list[str] | Unset = UNSET
        if not isinstance(self.row_ids, Unset):
            row_ids = []
            for row_ids_item_data in self.row_ids:
                row_ids_item = str(row_ids_item_data)
                row_ids.append(row_ids_item)

        selected_all_rows = self.selected_all_rows

        num_copies = self.num_copies

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if row_ids is not UNSET:
            field_dict["row_ids"] = row_ids
        if selected_all_rows is not UNSET:
            field_dict["selected_all_rows"] = selected_all_rows
        if num_copies is not UNSET:
            field_dict["num_copies"] = num_copies

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _row_ids = d.pop("row_ids", UNSET)
        row_ids: list[UUID] | Unset = UNSET
        if _row_ids is not UNSET:
            row_ids = []
            for row_ids_item_data in _row_ids:
                row_ids_item = UUID(row_ids_item_data)

                row_ids.append(row_ids_item)

        selected_all_rows = d.pop("selected_all_rows", UNSET)

        num_copies = d.pop("num_copies", UNSET)

        duplicate_rows_request = cls(
            row_ids=row_ids,
            selected_all_rows=selected_all_rows,
            num_copies=num_copies,
        )

        duplicate_rows_request.additional_properties = d
        return duplicate_rows_request

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
