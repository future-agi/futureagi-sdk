from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_config_definition import EvalConfigDefinition


T = TypeVar("T", bound="CreatePromptSimulationRequest")


@_attrs_define
class CreatePromptSimulationRequest:
    """
    Attributes:
        name (str):
        prompt_version_id (str): Prompt version ID (UUID) or template_version string
        scenario_ids (list[UUID]):
        description (str | Unset):
        dataset_row_ids (list[str] | Unset):
        evaluations_config (list[EvalConfigDefinition] | Unset): Evaluation configurations to create
        enable_tool_evaluation (bool | Unset): Enable automatic tool evaluation for this simulation run Default: False.
    """

    name: str
    prompt_version_id: str
    scenario_ids: list[UUID]
    description: str | Unset = UNSET
    dataset_row_ids: list[str] | Unset = UNSET
    evaluations_config: list[EvalConfigDefinition] | Unset = UNSET
    enable_tool_evaluation: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        prompt_version_id = self.prompt_version_id

        scenario_ids = []
        for scenario_ids_item_data in self.scenario_ids:
            scenario_ids_item = str(scenario_ids_item_data)
            scenario_ids.append(scenario_ids_item)

        description = self.description

        dataset_row_ids: list[str] | Unset = UNSET
        if not isinstance(self.dataset_row_ids, Unset):
            dataset_row_ids = self.dataset_row_ids

        evaluations_config: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.evaluations_config, Unset):
            evaluations_config = []
            for evaluations_config_item_data in self.evaluations_config:
                evaluations_config_item = evaluations_config_item_data.to_dict()
                evaluations_config.append(evaluations_config_item)

        enable_tool_evaluation = self.enable_tool_evaluation

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "prompt_version_id": prompt_version_id,
                "scenario_ids": scenario_ids,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if dataset_row_ids is not UNSET:
            field_dict["dataset_row_ids"] = dataset_row_ids
        if evaluations_config is not UNSET:
            field_dict["evaluations_config"] = evaluations_config
        if enable_tool_evaluation is not UNSET:
            field_dict["enable_tool_evaluation"] = enable_tool_evaluation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_config_definition import EvalConfigDefinition

        d = dict(src_dict)
        name = d.pop("name")

        prompt_version_id = d.pop("prompt_version_id")

        scenario_ids = []
        _scenario_ids = d.pop("scenario_ids")
        for scenario_ids_item_data in _scenario_ids:
            scenario_ids_item = UUID(scenario_ids_item_data)

            scenario_ids.append(scenario_ids_item)

        description = d.pop("description", UNSET)

        dataset_row_ids = cast(list[str], d.pop("dataset_row_ids", UNSET))

        _evaluations_config = d.pop("evaluations_config", UNSET)
        evaluations_config: list[EvalConfigDefinition] | Unset = UNSET
        if _evaluations_config is not UNSET:
            evaluations_config = []
            for evaluations_config_item_data in _evaluations_config:
                evaluations_config_item = EvalConfigDefinition.from_dict(
                    evaluations_config_item_data
                )

                evaluations_config.append(evaluations_config_item)

        enable_tool_evaluation = d.pop("enable_tool_evaluation", UNSET)

        create_prompt_simulation_request = cls(
            name=name,
            prompt_version_id=prompt_version_id,
            scenario_ids=scenario_ids,
            description=description,
            dataset_row_ids=dataset_row_ids,
            evaluations_config=evaluations_config,
            enable_tool_evaluation=enable_tool_evaluation,
        )

        create_prompt_simulation_request.additional_properties = d
        return create_prompt_simulation_request

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
