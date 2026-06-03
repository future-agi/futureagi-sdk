from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.column_order import ColumnOrder


T = TypeVar("T", bound="TestExecutionColumnOrder")


@_attrs_define
class TestExecutionColumnOrder:
    """
    Attributes:
        column_order (list[ColumnOrder]):
    """

    column_order: list[ColumnOrder]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_order = []
        for column_order_item_data in self.column_order:
            column_order_item = column_order_item_data.to_dict()
            column_order.append(column_order_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_order": column_order,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.column_order import ColumnOrder

        d = dict(src_dict)
        column_order = []
        _column_order = d.pop("column_order")
        for column_order_item_data in _column_order:
            column_order_item = ColumnOrder.from_dict(column_order_item_data)

            column_order.append(column_order_item)

        test_execution_column_order = cls(
            column_order=column_order,
        )

        test_execution_column_order.additional_properties = d
        return test_execution_column_order

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
