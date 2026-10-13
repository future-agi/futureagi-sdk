from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateRunTest")


@_attrs_define
class UpdateRunTest:
    """
    Attributes:
        name (str | Unset):
        description (str | Unset):
        agent_definition_id (UUID | Unset):
        scenario_ids (list[UUID] | Unset):
        dataset_row_ids (list[str] | Unset):
        eval_config_ids (list[UUID] | Unset):
    """

    name: str | Unset = UNSET
    description: str | Unset = UNSET
    agent_definition_id: UUID | Unset = UNSET
    scenario_ids: list[UUID] | Unset = UNSET
    dataset_row_ids: list[str] | Unset = UNSET
    eval_config_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        agent_definition_id: str | Unset = UNSET
        if not isinstance(self.agent_definition_id, Unset):
            agent_definition_id = str(self.agent_definition_id)

        scenario_ids: list[str] | Unset = UNSET
        if not isinstance(self.scenario_ids, Unset):
            scenario_ids = []
            for scenario_ids_item_data in self.scenario_ids:
                scenario_ids_item = str(scenario_ids_item_data)
                scenario_ids.append(scenario_ids_item)

        dataset_row_ids: list[str] | Unset = UNSET
        if not isinstance(self.dataset_row_ids, Unset):
            dataset_row_ids = self.dataset_row_ids

        eval_config_ids: list[str] | Unset = UNSET
        if not isinstance(self.eval_config_ids, Unset):
            eval_config_ids = []
            for eval_config_ids_item_data in self.eval_config_ids:
                eval_config_ids_item = str(eval_config_ids_item_data)
                eval_config_ids.append(eval_config_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if agent_definition_id is not UNSET:
            field_dict["agent_definition_id"] = agent_definition_id
        if scenario_ids is not UNSET:
            field_dict["scenario_ids"] = scenario_ids
        if dataset_row_ids is not UNSET:
            field_dict["dataset_row_ids"] = dataset_row_ids
        if eval_config_ids is not UNSET:
            field_dict["eval_config_ids"] = eval_config_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        _agent_definition_id = d.pop("agent_definition_id", UNSET)
        agent_definition_id: UUID | Unset
        if isinstance(_agent_definition_id, Unset):
            agent_definition_id = UNSET
        else:
            agent_definition_id = UUID(_agent_definition_id)

        _scenario_ids = d.pop("scenario_ids", UNSET)
        scenario_ids: list[UUID] | Unset = UNSET
        if _scenario_ids is not UNSET:
            scenario_ids = []
            for scenario_ids_item_data in _scenario_ids:
                scenario_ids_item = UUID(scenario_ids_item_data)

                scenario_ids.append(scenario_ids_item)

        dataset_row_ids = cast(list[str], d.pop("dataset_row_ids", UNSET))

        _eval_config_ids = d.pop("eval_config_ids", UNSET)
        eval_config_ids: list[UUID] | Unset = UNSET
        if _eval_config_ids is not UNSET:
            eval_config_ids = []
            for eval_config_ids_item_data in _eval_config_ids:
                eval_config_ids_item = UUID(eval_config_ids_item_data)

                eval_config_ids.append(eval_config_ids_item)

        update_run_test = cls(
            name=name,
            description=description,
            agent_definition_id=agent_definition_id,
            scenario_ids=scenario_ids,
            dataset_row_ids=dataset_row_ids,
            eval_config_ids=eval_config_ids,
        )

        update_run_test.additional_properties = d
        return update_run_test

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
