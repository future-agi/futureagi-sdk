from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PromptSimulationUpdateRequest")


@_attrs_define
class PromptSimulationUpdateRequest:
    """
    Attributes:
        prompt_version_id (str | Unset):
        scenario_ids (list[UUID] | Unset):
        name (str | Unset):
        description (str | Unset):
        enable_tool_evaluation (bool | Unset):
    """

    prompt_version_id: str | Unset = UNSET
    scenario_ids: list[UUID] | Unset = UNSET
    name: str | Unset = UNSET
    description: str | Unset = UNSET
    enable_tool_evaluation: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        prompt_version_id = self.prompt_version_id

        scenario_ids: list[str] | Unset = UNSET
        if not isinstance(self.scenario_ids, Unset):
            scenario_ids = []
            for scenario_ids_item_data in self.scenario_ids:
                scenario_ids_item = str(scenario_ids_item_data)
                scenario_ids.append(scenario_ids_item)

        name = self.name

        description = self.description

        enable_tool_evaluation = self.enable_tool_evaluation

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if prompt_version_id is not UNSET:
            field_dict["prompt_version_id"] = prompt_version_id
        if scenario_ids is not UNSET:
            field_dict["scenario_ids"] = scenario_ids
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if enable_tool_evaluation is not UNSET:
            field_dict["enable_tool_evaluation"] = enable_tool_evaluation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        prompt_version_id = d.pop("prompt_version_id", UNSET)

        _scenario_ids = d.pop("scenario_ids", UNSET)
        scenario_ids: list[UUID] | Unset = UNSET
        if _scenario_ids is not UNSET:
            scenario_ids = []
            for scenario_ids_item_data in _scenario_ids:
                scenario_ids_item = UUID(scenario_ids_item_data)

                scenario_ids.append(scenario_ids_item)

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        enable_tool_evaluation = d.pop("enable_tool_evaluation", UNSET)

        prompt_simulation_update_request = cls(
            prompt_version_id=prompt_version_id,
            scenario_ids=scenario_ids,
            name=name,
            description=description,
            enable_tool_evaluation=enable_tool_evaluation,
        )

        prompt_simulation_update_request.additional_properties = d
        return prompt_simulation_update_request

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
