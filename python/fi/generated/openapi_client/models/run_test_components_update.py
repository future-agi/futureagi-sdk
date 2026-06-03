from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RunTestComponentsUpdate")


@_attrs_define
class RunTestComponentsUpdate:
    """
    Attributes:
        agent_definition_id (UUID | Unset):
        version (UUID | Unset):
        simulator_agent_id (UUID | Unset):
        scenarios (list[UUID] | Unset):
        enable_tool_evaluation (bool | Unset):
    """

    agent_definition_id: UUID | Unset = UNSET
    version: UUID | Unset = UNSET
    simulator_agent_id: UUID | Unset = UNSET
    scenarios: list[UUID] | Unset = UNSET
    enable_tool_evaluation: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        agent_definition_id: str | Unset = UNSET
        if not isinstance(self.agent_definition_id, Unset):
            agent_definition_id = str(self.agent_definition_id)

        version: str | Unset = UNSET
        if not isinstance(self.version, Unset):
            version = str(self.version)

        simulator_agent_id: str | Unset = UNSET
        if not isinstance(self.simulator_agent_id, Unset):
            simulator_agent_id = str(self.simulator_agent_id)

        scenarios: list[str] | Unset = UNSET
        if not isinstance(self.scenarios, Unset):
            scenarios = []
            for scenarios_item_data in self.scenarios:
                scenarios_item = str(scenarios_item_data)
                scenarios.append(scenarios_item)

        enable_tool_evaluation = self.enable_tool_evaluation

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if agent_definition_id is not UNSET:
            field_dict["agent_definition_id"] = agent_definition_id
        if version is not UNSET:
            field_dict["version"] = version
        if simulator_agent_id is not UNSET:
            field_dict["simulator_agent_id"] = simulator_agent_id
        if scenarios is not UNSET:
            field_dict["scenarios"] = scenarios
        if enable_tool_evaluation is not UNSET:
            field_dict["enable_tool_evaluation"] = enable_tool_evaluation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _agent_definition_id = d.pop("agent_definition_id", UNSET)
        agent_definition_id: UUID | Unset
        if isinstance(_agent_definition_id, Unset):
            agent_definition_id = UNSET
        else:
            agent_definition_id = UUID(_agent_definition_id)

        _version = d.pop("version", UNSET)
        version: UUID | Unset
        if isinstance(_version, Unset):
            version = UNSET
        else:
            version = UUID(_version)

        _simulator_agent_id = d.pop("simulator_agent_id", UNSET)
        simulator_agent_id: UUID | Unset
        if isinstance(_simulator_agent_id, Unset):
            simulator_agent_id = UNSET
        else:
            simulator_agent_id = UUID(_simulator_agent_id)

        _scenarios = d.pop("scenarios", UNSET)
        scenarios: list[UUID] | Unset = UNSET
        if _scenarios is not UNSET:
            scenarios = []
            for scenarios_item_data in _scenarios:
                scenarios_item = UUID(scenarios_item_data)

                scenarios.append(scenarios_item)

        enable_tool_evaluation = d.pop("enable_tool_evaluation", UNSET)

        run_test_components_update = cls(
            agent_definition_id=agent_definition_id,
            version=version,
            simulator_agent_id=simulator_agent_id,
            scenarios=scenarios,
            enable_tool_evaluation=enable_tool_evaluation,
        )

        run_test_components_update.additional_properties = d
        return run_test_components_update

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
