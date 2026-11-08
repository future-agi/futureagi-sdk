from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_row_cell_request_value_type_4_type_0 import (
        DatasetRowCellRequestValueType4Type0,
    )


T = TypeVar("T", bound="DatasetRowCellRequest")


@_attrs_define
class DatasetRowCellRequest:
    """
    Attributes:
        column_name (str):
        value (bool | DatasetRowCellRequestValueType4Type0 | float | list[Any] | None | str | Unset): Any valid JSON
            value.
    """

    column_name: str
    value: (
        bool
        | DatasetRowCellRequestValueType4Type0
        | float
        | list[Any]
        | None
        | str
        | Unset
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.dataset_row_cell_request_value_type_4_type_0 import (
            DatasetRowCellRequestValueType4Type0,
        )

        column_name = self.column_name

        value: bool | dict[str, Any] | float | list[Any] | None | str | Unset
        if isinstance(self.value, Unset):
            value = UNSET
        elif isinstance(self.value, list):
            value = self.value

        elif isinstance(self.value, DatasetRowCellRequestValueType4Type0):
            value = self.value.to_dict()
        else:
            value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_name": column_name,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_row_cell_request_value_type_4_type_0 import (
            DatasetRowCellRequestValueType4Type0,
        )

        d = dict(src_dict)
        column_name = d.pop("column_name")

        def _parse_value(
            data: object,
        ) -> (
            bool
            | DatasetRowCellRequestValueType4Type0
            | float
            | list[Any]
            | None
            | str
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                value_type_3 = cast(list[Any], data)

                return value_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                value_type_4_type_0 = DatasetRowCellRequestValueType4Type0.from_dict(
                    data
                )

                return value_type_4_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                bool
                | DatasetRowCellRequestValueType4Type0
                | float
                | list[Any]
                | None
                | str
                | Unset,
                data,
            )

        value = _parse_value(d.pop("value", UNSET))

        dataset_row_cell_request = cls(
            column_name=column_name,
            value=value,
        )

        dataset_row_cell_request.additional_properties = d
        return dataset_row_cell_request

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
