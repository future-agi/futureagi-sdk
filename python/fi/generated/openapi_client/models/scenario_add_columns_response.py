from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ScenarioAddColumnsResponse")


@_attrs_define
class ScenarioAddColumnsResponse:
    """
    Attributes:
        message (str | Unset):
        scenario_id (UUID | Unset):
        dataset_id (UUID | Unset):
        columns (list[str] | Unset):
    """

    message: str | Unset = UNSET
    scenario_id: UUID | Unset = UNSET
    dataset_id: UUID | Unset = UNSET
    columns: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        scenario_id: str | Unset = UNSET
        if not isinstance(self.scenario_id, Unset):
            scenario_id = str(self.scenario_id)

        dataset_id: str | Unset = UNSET
        if not isinstance(self.dataset_id, Unset):
            dataset_id = str(self.dataset_id)

        columns: list[str] | Unset = UNSET
        if not isinstance(self.columns, Unset):
            columns = self.columns

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if scenario_id is not UNSET:
            field_dict["scenario_id"] = scenario_id
        if dataset_id is not UNSET:
            field_dict["dataset_id"] = dataset_id
        if columns is not UNSET:
            field_dict["columns"] = columns

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _scenario_id = d.pop("scenario_id", UNSET)
        scenario_id: UUID | Unset
        if isinstance(_scenario_id, Unset):
            scenario_id = UNSET
        else:
            scenario_id = UUID(_scenario_id)

        _dataset_id = d.pop("dataset_id", UNSET)
        dataset_id: UUID | Unset
        if isinstance(_dataset_id, Unset):
            dataset_id = UNSET
        else:
            dataset_id = UUID(_dataset_id)

        columns = cast(list[str], d.pop("columns", UNSET))

        scenario_add_columns_response = cls(
            message=message,
            scenario_id=scenario_id,
            dataset_id=dataset_id,
            columns=columns,
        )

        scenario_add_columns_response.additional_properties = d
        return scenario_add_columns_response

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
