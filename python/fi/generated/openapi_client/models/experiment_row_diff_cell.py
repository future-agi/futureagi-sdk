from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_row_diff_cell_cell_diff_value import (
        ExperimentRowDiffCellCellDiffValue,
    )
    from ..models.experiment_row_diff_cell_cell_value import (
        ExperimentRowDiffCellCellValue,
    )
    from ..models.experiment_row_diff_cell_value_infos import (
        ExperimentRowDiffCellValueInfos,
    )


T = TypeVar("T", bound="ExperimentRowDiffCell")


@_attrs_define
class ExperimentRowDiffCell:
    """
    Attributes:
        cell_value (ExperimentRowDiffCellCellValue | Unset):
        cell_diff_value (ExperimentRowDiffCellCellDiffValue | Unset):
        status (str | Unset):
        value_infos (ExperimentRowDiffCellValueInfos | Unset):
    """

    cell_value: ExperimentRowDiffCellCellValue | Unset = UNSET
    cell_diff_value: ExperimentRowDiffCellCellDiffValue | Unset = UNSET
    status: str | Unset = UNSET
    value_infos: ExperimentRowDiffCellValueInfos | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cell_value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cell_value, Unset):
            cell_value = self.cell_value.to_dict()

        cell_diff_value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cell_diff_value, Unset):
            cell_diff_value = self.cell_diff_value.to_dict()

        status = self.status

        value_infos: dict[str, Any] | Unset = UNSET
        if not isinstance(self.value_infos, Unset):
            value_infos = self.value_infos.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cell_value is not UNSET:
            field_dict["cell_value"] = cell_value
        if cell_diff_value is not UNSET:
            field_dict["cell_diff_value"] = cell_diff_value
        if status is not UNSET:
            field_dict["status"] = status
        if value_infos is not UNSET:
            field_dict["value_infos"] = value_infos

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_row_diff_cell_cell_diff_value import (
            ExperimentRowDiffCellCellDiffValue,
        )
        from ..models.experiment_row_diff_cell_cell_value import (
            ExperimentRowDiffCellCellValue,
        )
        from ..models.experiment_row_diff_cell_value_infos import (
            ExperimentRowDiffCellValueInfos,
        )

        d = dict(src_dict)
        _cell_value = d.pop("cell_value", UNSET)
        cell_value: ExperimentRowDiffCellCellValue | Unset
        if isinstance(_cell_value, Unset):
            cell_value = UNSET
        else:
            cell_value = ExperimentRowDiffCellCellValue.from_dict(_cell_value)

        _cell_diff_value = d.pop("cell_diff_value", UNSET)
        cell_diff_value: ExperimentRowDiffCellCellDiffValue | Unset
        if isinstance(_cell_diff_value, Unset):
            cell_diff_value = UNSET
        else:
            cell_diff_value = ExperimentRowDiffCellCellDiffValue.from_dict(
                _cell_diff_value
            )

        status = d.pop("status", UNSET)

        _value_infos = d.pop("value_infos", UNSET)
        value_infos: ExperimentRowDiffCellValueInfos | Unset
        if isinstance(_value_infos, Unset):
            value_infos = UNSET
        else:
            value_infos = ExperimentRowDiffCellValueInfos.from_dict(_value_infos)

        experiment_row_diff_cell = cls(
            cell_value=cell_value,
            cell_diff_value=cell_diff_value,
            status=status,
            value_infos=value_infos,
        )

        experiment_row_diff_cell.additional_properties = d
        return experiment_row_diff_cell

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
