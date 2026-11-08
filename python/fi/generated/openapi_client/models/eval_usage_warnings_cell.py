from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_usage_warnings_cell_cell_value_type_0_item import (
        EvalUsageWarningsCellCellValueType0Item,
    )


T = TypeVar("T", bound="EvalUsageWarningsCell")


@_attrs_define
class EvalUsageWarningsCell:
    """
    Attributes:
        cell_value (list[EvalUsageWarningsCellCellValueType0Item] | None | Unset):
    """

    cell_value: list[EvalUsageWarningsCellCellValueType0Item] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cell_value: list[dict[str, Any]] | None | Unset
        if isinstance(self.cell_value, Unset):
            cell_value = UNSET
        elif isinstance(self.cell_value, list):
            cell_value = []
            for cell_value_type_0_item_data in self.cell_value:
                cell_value_type_0_item = cell_value_type_0_item_data.to_dict()
                cell_value.append(cell_value_type_0_item)

        else:
            cell_value = self.cell_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cell_value is not UNSET:
            field_dict["cell_value"] = cell_value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_usage_warnings_cell_cell_value_type_0_item import (
            EvalUsageWarningsCellCellValueType0Item,
        )

        d = dict(src_dict)

        def _parse_cell_value(
            data: object,
        ) -> list[EvalUsageWarningsCellCellValueType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                cell_value_type_0 = []
                _cell_value_type_0 = data
                for cell_value_type_0_item_data in _cell_value_type_0:
                    cell_value_type_0_item = (
                        EvalUsageWarningsCellCellValueType0Item.from_dict(
                            cell_value_type_0_item_data
                        )
                    )

                    cell_value_type_0.append(cell_value_type_0_item)

                return cell_value_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[EvalUsageWarningsCellCellValueType0Item] | None | Unset, data
            )

        cell_value = _parse_cell_value(d.pop("cell_value", UNSET))

        eval_usage_warnings_cell = cls(
            cell_value=cell_value,
        )

        eval_usage_warnings_cell.additional_properties = d
        return eval_usage_warnings_cell

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
