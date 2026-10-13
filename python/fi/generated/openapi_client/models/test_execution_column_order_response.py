from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.column_order import ColumnOrder


T = TypeVar("T", bound="TestExecutionColumnOrderResponse")


@_attrs_define
class TestExecutionColumnOrderResponse:
    """
    Attributes:
        message (str | Unset):
        column_order (list[ColumnOrder] | Unset):
    """

    message: str | Unset = UNSET
    column_order: list[ColumnOrder] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        column_order: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.column_order, Unset):
            column_order = []
            for column_order_item_data in self.column_order:
                column_order_item = column_order_item_data.to_dict()
                column_order.append(column_order_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if column_order is not UNSET:
            field_dict["column_order"] = column_order

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.column_order import ColumnOrder

        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _column_order = d.pop("column_order", UNSET)
        column_order: list[ColumnOrder] | Unset = UNSET
        if _column_order is not UNSET:
            column_order = []
            for column_order_item_data in _column_order:
                column_order_item = ColumnOrder.from_dict(column_order_item_data)

                column_order.append(column_order_item)

        test_execution_column_order_response = cls(
            message=message,
            column_order=column_order,
        )

        test_execution_column_order_response.additional_properties = d
        return test_execution_column_order_response

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
