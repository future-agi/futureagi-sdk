from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExecutePromptSimulationRequest")


@_attrs_define
class ExecutePromptSimulationRequest:
    """
    Attributes:
        scenario_ids (list[UUID] | Unset):
        select_all (bool | Unset):  Default: False.
    """

    scenario_ids: list[UUID] | Unset = UNSET
    select_all: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        scenario_ids: list[str] | Unset = UNSET
        if not isinstance(self.scenario_ids, Unset):
            scenario_ids = []
            for scenario_ids_item_data in self.scenario_ids:
                scenario_ids_item = str(scenario_ids_item_data)
                scenario_ids.append(scenario_ids_item)

        select_all = self.select_all

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if scenario_ids is not UNSET:
            field_dict["scenario_ids"] = scenario_ids
        if select_all is not UNSET:
            field_dict["select_all"] = select_all

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _scenario_ids = d.pop("scenario_ids", UNSET)
        scenario_ids: list[UUID] | Unset = UNSET
        if _scenario_ids is not UNSET:
            scenario_ids = []
            for scenario_ids_item_data in _scenario_ids:
                scenario_ids_item = UUID(scenario_ids_item_data)

                scenario_ids.append(scenario_ids_item)

        select_all = d.pop("select_all", UNSET)

        execute_prompt_simulation_request = cls(
            scenario_ids=scenario_ids,
            select_all=select_all,
        )

        execute_prompt_simulation_request.additional_properties = d
        return execute_prompt_simulation_request

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
