from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_config_definition import EvalConfigDefinition


T = TypeVar("T", bound="CreateRunTest")


@_attrs_define
class CreateRunTest:
    """
    Attributes:
        name (str):
        agent_definition_id (UUID):
        scenario_ids (list[UUID]):
        description (str | Unset):
        dataset_row_ids (list[str] | Unset):
        eval_config_ids (list[UUID] | Unset):
        evaluations_config (list[EvalConfigDefinition] | Unset): Evaluation configurations to create
        enable_tool_evaluation (bool | Unset): Enable automatic tool evaluation for this test run Default: False.
        replay_session_id (None | Unset | UUID): Optional replay session ID to mark as completed after run test creation
        agent_version (None | Unset | UUID): Optional agent version to bind to this test run
    """

    name: str
    agent_definition_id: UUID
    scenario_ids: list[UUID]
    description: str | Unset = UNSET
    dataset_row_ids: list[str] | Unset = UNSET
    eval_config_ids: list[UUID] | Unset = UNSET
    evaluations_config: list[EvalConfigDefinition] | Unset = UNSET
    enable_tool_evaluation: bool | Unset = False
    replay_session_id: None | Unset | UUID = UNSET
    agent_version: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        agent_definition_id = str(self.agent_definition_id)

        scenario_ids = []
        for scenario_ids_item_data in self.scenario_ids:
            scenario_ids_item = str(scenario_ids_item_data)
            scenario_ids.append(scenario_ids_item)

        description = self.description

        dataset_row_ids: list[str] | Unset = UNSET
        if not isinstance(self.dataset_row_ids, Unset):
            dataset_row_ids = self.dataset_row_ids

        eval_config_ids: list[str] | Unset = UNSET
        if not isinstance(self.eval_config_ids, Unset):
            eval_config_ids = []
            for eval_config_ids_item_data in self.eval_config_ids:
                eval_config_ids_item = str(eval_config_ids_item_data)
                eval_config_ids.append(eval_config_ids_item)

        evaluations_config: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.evaluations_config, Unset):
            evaluations_config = []
            for evaluations_config_item_data in self.evaluations_config:
                evaluations_config_item = evaluations_config_item_data.to_dict()
                evaluations_config.append(evaluations_config_item)

        enable_tool_evaluation = self.enable_tool_evaluation

        replay_session_id: None | str | Unset
        if isinstance(self.replay_session_id, Unset):
            replay_session_id = UNSET
        elif isinstance(self.replay_session_id, UUID):
            replay_session_id = str(self.replay_session_id)
        else:
            replay_session_id = self.replay_session_id

        agent_version: None | str | Unset
        if isinstance(self.agent_version, Unset):
            agent_version = UNSET
        elif isinstance(self.agent_version, UUID):
            agent_version = str(self.agent_version)
        else:
            agent_version = self.agent_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "agent_definition_id": agent_definition_id,
                "scenario_ids": scenario_ids,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if dataset_row_ids is not UNSET:
            field_dict["dataset_row_ids"] = dataset_row_ids
        if eval_config_ids is not UNSET:
            field_dict["eval_config_ids"] = eval_config_ids
        if evaluations_config is not UNSET:
            field_dict["evaluations_config"] = evaluations_config
        if enable_tool_evaluation is not UNSET:
            field_dict["enable_tool_evaluation"] = enable_tool_evaluation
        if replay_session_id is not UNSET:
            field_dict["replay_session_id"] = replay_session_id
        if agent_version is not UNSET:
            field_dict["agent_version"] = agent_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_config_definition import EvalConfigDefinition

        d = dict(src_dict)
        name = d.pop("name")

        agent_definition_id = UUID(d.pop("agent_definition_id"))

        scenario_ids = []
        _scenario_ids = d.pop("scenario_ids")
        for scenario_ids_item_data in _scenario_ids:
            scenario_ids_item = UUID(scenario_ids_item_data)

            scenario_ids.append(scenario_ids_item)

        description = d.pop("description", UNSET)

        dataset_row_ids = cast(list[str], d.pop("dataset_row_ids", UNSET))

        _eval_config_ids = d.pop("eval_config_ids", UNSET)
        eval_config_ids: list[UUID] | Unset = UNSET
        if _eval_config_ids is not UNSET:
            eval_config_ids = []
            for eval_config_ids_item_data in _eval_config_ids:
                eval_config_ids_item = UUID(eval_config_ids_item_data)

                eval_config_ids.append(eval_config_ids_item)

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

        def _parse_replay_session_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                replay_session_id_type_0 = UUID(data)

                return replay_session_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        replay_session_id = _parse_replay_session_id(d.pop("replay_session_id", UNSET))

        def _parse_agent_version(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                agent_version_type_0 = UUID(data)

                return agent_version_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        agent_version = _parse_agent_version(d.pop("agent_version", UNSET))

        create_run_test = cls(
            name=name,
            agent_definition_id=agent_definition_id,
            scenario_ids=scenario_ids,
            description=description,
            dataset_row_ids=dataset_row_ids,
            eval_config_ids=eval_config_ids,
            evaluations_config=evaluations_config,
            enable_tool_evaluation=enable_tool_evaluation,
            replay_session_id=replay_session_id,
            agent_version=agent_version,
        )

        create_run_test.additional_properties = d
        return create_run_test

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
