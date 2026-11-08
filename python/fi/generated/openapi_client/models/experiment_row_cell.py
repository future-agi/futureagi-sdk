from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_row_cell_cell_diff_value import (
        ExperimentRowCellCellDiffValue,
    )
    from ..models.experiment_row_cell_cell_value import ExperimentRowCellCellValue
    from ..models.experiment_row_cell_metadata import ExperimentRowCellMetadata
    from ..models.experiment_row_cell_value_infos import ExperimentRowCellValueInfos


T = TypeVar("T", bound="ExperimentRowCell")


@_attrs_define
class ExperimentRowCell:
    """
    Attributes:
        cell_value (ExperimentRowCellCellValue | Unset):
        cell_diff_value (ExperimentRowCellCellDiffValue | Unset):
        status (None | str | Unset):
        metadata (ExperimentRowCellMetadata | Unset):
        value_infos (ExperimentRowCellValueInfos | Unset):
    """

    cell_value: ExperimentRowCellCellValue | Unset = UNSET
    cell_diff_value: ExperimentRowCellCellDiffValue | Unset = UNSET
    status: None | str | Unset = UNSET
    metadata: ExperimentRowCellMetadata | Unset = UNSET
    value_infos: ExperimentRowCellValueInfos | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cell_value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cell_value, Unset):
            cell_value = self.cell_value.to_dict()

        cell_diff_value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cell_diff_value, Unset):
            cell_diff_value = self.cell_diff_value.to_dict()

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

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
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if value_infos is not UNSET:
            field_dict["value_infos"] = value_infos

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_row_cell_cell_diff_value import (
            ExperimentRowCellCellDiffValue,
        )
        from ..models.experiment_row_cell_cell_value import ExperimentRowCellCellValue
        from ..models.experiment_row_cell_metadata import ExperimentRowCellMetadata
        from ..models.experiment_row_cell_value_infos import ExperimentRowCellValueInfos

        d = dict(src_dict)
        _cell_value = d.pop("cell_value", UNSET)
        cell_value: ExperimentRowCellCellValue | Unset
        if isinstance(_cell_value, Unset):
            cell_value = UNSET
        else:
            cell_value = ExperimentRowCellCellValue.from_dict(_cell_value)

        _cell_diff_value = d.pop("cell_diff_value", UNSET)
        cell_diff_value: ExperimentRowCellCellDiffValue | Unset
        if isinstance(_cell_diff_value, Unset):
            cell_diff_value = UNSET
        else:
            cell_diff_value = ExperimentRowCellCellDiffValue.from_dict(_cell_diff_value)

        def _parse_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: ExperimentRowCellMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ExperimentRowCellMetadata.from_dict(_metadata)

        _value_infos = d.pop("value_infos", UNSET)
        value_infos: ExperimentRowCellValueInfos | Unset
        if isinstance(_value_infos, Unset):
            value_infos = UNSET
        else:
            value_infos = ExperimentRowCellValueInfos.from_dict(_value_infos)

        experiment_row_cell = cls(
            cell_value=cell_value,
            cell_diff_value=cell_diff_value,
            status=status,
            metadata=metadata,
            value_infos=value_infos,
        )

        experiment_row_cell.additional_properties = d
        return experiment_row_cell

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
