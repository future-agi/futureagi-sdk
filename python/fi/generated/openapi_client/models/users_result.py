from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.users_result_table_item import UsersResultTableItem


T = TypeVar("T", bound="UsersResult")


@_attrs_define
class UsersResult:
    """
    Attributes:
        table (list[UsersResultTableItem]):
        total_count (int):
        total_pages (int):
    """

    table: list[UsersResultTableItem]
    total_count: int
    total_pages: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        table = []
        for table_item_data in self.table:
            table_item = table_item_data.to_dict()
            table.append(table_item)

        total_count = self.total_count

        total_pages = self.total_pages

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "table": table,
                "total_count": total_count,
                "total_pages": total_pages,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.users_result_table_item import UsersResultTableItem

        d = dict(src_dict)
        table = []
        _table = d.pop("table")
        for table_item_data in _table:
            table_item = UsersResultTableItem.from_dict(table_item_data)

            table.append(table_item)

        total_count = d.pop("total_count")

        total_pages = d.pop("total_pages")

        users_result = cls(
            table=table,
            total_count=total_count,
            total_pages=total_pages,
        )

        users_result.additional_properties = d
        return users_result

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
