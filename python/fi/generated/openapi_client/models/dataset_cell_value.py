from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dataset_cell_value_cell_value import DatasetCellValueCellValue
    from ..models.dataset_cell_value_feedback_info import DatasetCellValueFeedbackInfo
    from ..models.dataset_cell_value_value_infos import DatasetCellValueValueInfos


T = TypeVar("T", bound="DatasetCellValue")


@_attrs_define
class DatasetCellValue:
    """
    Attributes:
        cell_value (DatasetCellValueCellValue | Unset):
        status (None | str | Unset):
        value_infos (DatasetCellValueValueInfos | Unset):
        feedback_info (DatasetCellValueFeedbackInfo | Unset):
    """

    cell_value: DatasetCellValueCellValue | Unset = UNSET
    status: None | str | Unset = UNSET
    value_infos: DatasetCellValueValueInfos | Unset = UNSET
    feedback_info: DatasetCellValueFeedbackInfo | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cell_value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cell_value, Unset):
            cell_value = self.cell_value.to_dict()

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        value_infos: dict[str, Any] | Unset = UNSET
        if not isinstance(self.value_infos, Unset):
            value_infos = self.value_infos.to_dict()

        feedback_info: dict[str, Any] | Unset = UNSET
        if not isinstance(self.feedback_info, Unset):
            feedback_info = self.feedback_info.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cell_value is not UNSET:
            field_dict["cell_value"] = cell_value
        if status is not UNSET:
            field_dict["status"] = status
        if value_infos is not UNSET:
            field_dict["value_infos"] = value_infos
        if feedback_info is not UNSET:
            field_dict["feedback_info"] = feedback_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_cell_value_cell_value import DatasetCellValueCellValue
        from ..models.dataset_cell_value_feedback_info import (
            DatasetCellValueFeedbackInfo,
        )
        from ..models.dataset_cell_value_value_infos import DatasetCellValueValueInfos

        d = dict(src_dict)
        _cell_value = d.pop("cell_value", UNSET)
        cell_value: DatasetCellValueCellValue | Unset
        if isinstance(_cell_value, Unset):
            cell_value = UNSET
        else:
            cell_value = DatasetCellValueCellValue.from_dict(_cell_value)

        def _parse_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        _value_infos = d.pop("value_infos", UNSET)
        value_infos: DatasetCellValueValueInfos | Unset
        if isinstance(_value_infos, Unset):
            value_infos = UNSET
        else:
            value_infos = DatasetCellValueValueInfos.from_dict(_value_infos)

        _feedback_info = d.pop("feedback_info", UNSET)
        feedback_info: DatasetCellValueFeedbackInfo | Unset
        if isinstance(_feedback_info, Unset):
            feedback_info = UNSET
        else:
            feedback_info = DatasetCellValueFeedbackInfo.from_dict(_feedback_info)

        dataset_cell_value = cls(
            cell_value=cell_value,
            status=status,
            value_infos=value_infos,
            feedback_info=feedback_info,
        )

        dataset_cell_value.additional_properties = d
        return dataset_cell_value

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
