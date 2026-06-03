from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DuplicateRowsResult")


@_attrs_define
class DuplicateRowsResult:
    """
    Attributes:
        message (str):
        source_rows (int):
        copies_per_row (int):
        total_new_rows (int):
        new_row_ids (list[UUID]):
    """

    message: str
    source_rows: int
    copies_per_row: int
    total_new_rows: int
    new_row_ids: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        source_rows = self.source_rows

        copies_per_row = self.copies_per_row

        total_new_rows = self.total_new_rows

        new_row_ids = []
        for new_row_ids_item_data in self.new_row_ids:
            new_row_ids_item = str(new_row_ids_item_data)
            new_row_ids.append(new_row_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "source_rows": source_rows,
                "copies_per_row": copies_per_row,
                "total_new_rows": total_new_rows,
                "new_row_ids": new_row_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        source_rows = d.pop("source_rows")

        copies_per_row = d.pop("copies_per_row")

        total_new_rows = d.pop("total_new_rows")

        new_row_ids = []
        _new_row_ids = d.pop("new_row_ids")
        for new_row_ids_item_data in _new_row_ids:
            new_row_ids_item = UUID(new_row_ids_item_data)

            new_row_ids.append(new_row_ids_item)

        duplicate_rows_result = cls(
            message=message,
            source_rows=source_rows,
            copies_per_row=copies_per_row,
            total_new_rows=total_new_rows,
            new_row_ids=new_row_ids,
        )

        duplicate_rows_result.additional_properties = d
        return duplicate_rows_result

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
