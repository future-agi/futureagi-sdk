from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.run_test_response_source_type import RunTestResponseSourceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_test_response_agent_definition_detail import (
        RunTestResponseAgentDefinitionDetail,
    )
    from ..models.run_test_response_agent_version import RunTestResponseAgentVersion
    from ..models.run_test_response_prompt_template_detail import (
        RunTestResponsePromptTemplateDetail,
    )
    from ..models.run_test_response_prompt_version_detail import (
        RunTestResponsePromptVersionDetail,
    )
    from ..models.run_test_response_scenarios_detail_item import (
        RunTestResponseScenariosDetailItem,
    )
    from ..models.run_test_response_simulator_agent_detail import (
        RunTestResponseSimulatorAgentDetail,
    )
    from ..models.simulate_eval_config_response import SimulateEvalConfigResponse


T = TypeVar("T", bound="RunTestResponse")


@_attrs_define
class RunTestResponse:
    """
    Attributes:
        id (UUID | Unset):
        name (str | Unset): Name of the test run
        description (None | str | Unset): Description of the test run
        agent_definition (None | Unset | UUID): Agent definition for this test run
        agent_version (RunTestResponseAgentVersion | Unset):
        agent_definition_detail (RunTestResponseAgentDefinitionDetail | Unset):
        source_type (RunTestResponseSourceType | Unset): Source type for the test run: agent_definition or prompt
        source_type_display (None | str | Unset):
        prompt_template (None | Unset | UUID): Prompt template for this test run (only for prompt source type)
        prompt_template_detail (RunTestResponsePromptTemplateDetail | Unset):
        prompt_version (None | Unset | UUID): Prompt version for this test run (only for prompt source type)
        prompt_version_detail (RunTestResponsePromptVersionDetail | Unset):
        scenarios (list[UUID] | Unset): Scenarios to run in this test
        scenarios_detail (list[RunTestResponseScenariosDetailItem] | Unset):
        dataset_row_ids (list[str] | Unset): IDs of dataset rows to run evaluations on
        simulator_agent (None | Unset | UUID): Simulator agent for this test run (derived from scenarios)
        simulator_agent_detail (RunTestResponseSimulatorAgentDetail | Unset):
        simulate_eval_configs (list[UUID] | Unset):
        simulate_eval_configs_detail (list[SimulateEvalConfigResponse] | Unset):
        evals_detail (list[SimulateEvalConfigResponse] | Unset):
        organization (UUID | Unset): Organization this test run belongs to
        enable_tool_evaluation (bool | Unset): Enable automatic tool evaluation for this test run
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        last_run_at (datetime.datetime | None | Unset):
        deleted (bool | Unset):
        deleted_at (datetime.datetime | None | Unset):
    """

    id: UUID | Unset = UNSET
    name: str | Unset = UNSET
    description: None | str | Unset = UNSET
    agent_definition: None | Unset | UUID = UNSET
    agent_version: RunTestResponseAgentVersion | Unset = UNSET
    agent_definition_detail: RunTestResponseAgentDefinitionDetail | Unset = UNSET
    source_type: RunTestResponseSourceType | Unset = UNSET
    source_type_display: None | str | Unset = UNSET
    prompt_template: None | Unset | UUID = UNSET
    prompt_template_detail: RunTestResponsePromptTemplateDetail | Unset = UNSET
    prompt_version: None | Unset | UUID = UNSET
    prompt_version_detail: RunTestResponsePromptVersionDetail | Unset = UNSET
    scenarios: list[UUID] | Unset = UNSET
    scenarios_detail: list[RunTestResponseScenariosDetailItem] | Unset = UNSET
    dataset_row_ids: list[str] | Unset = UNSET
    simulator_agent: None | Unset | UUID = UNSET
    simulator_agent_detail: RunTestResponseSimulatorAgentDetail | Unset = UNSET
    simulate_eval_configs: list[UUID] | Unset = UNSET
    simulate_eval_configs_detail: list[SimulateEvalConfigResponse] | Unset = UNSET
    evals_detail: list[SimulateEvalConfigResponse] | Unset = UNSET
    organization: UUID | Unset = UNSET
    enable_tool_evaluation: bool | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    last_run_at: datetime.datetime | None | Unset = UNSET
    deleted: bool | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        agent_definition: None | str | Unset
        if isinstance(self.agent_definition, Unset):
            agent_definition = UNSET
        elif isinstance(self.agent_definition, UUID):
            agent_definition = str(self.agent_definition)
        else:
            agent_definition = self.agent_definition

        agent_version: dict[str, Any] | Unset = UNSET
        if not isinstance(self.agent_version, Unset):
            agent_version = self.agent_version.to_dict()

        agent_definition_detail: dict[str, Any] | Unset = UNSET
        if not isinstance(self.agent_definition_detail, Unset):
            agent_definition_detail = self.agent_definition_detail.to_dict()

        source_type: str | Unset = UNSET
        if not isinstance(self.source_type, Unset):
            source_type = self.source_type.value

        source_type_display: None | str | Unset
        if isinstance(self.source_type_display, Unset):
            source_type_display = UNSET
        else:
            source_type_display = self.source_type_display

        prompt_template: None | str | Unset
        if isinstance(self.prompt_template, Unset):
            prompt_template = UNSET
        elif isinstance(self.prompt_template, UUID):
            prompt_template = str(self.prompt_template)
        else:
            prompt_template = self.prompt_template

        prompt_template_detail: dict[str, Any] | Unset = UNSET
        if not isinstance(self.prompt_template_detail, Unset):
            prompt_template_detail = self.prompt_template_detail.to_dict()

        prompt_version: None | str | Unset
        if isinstance(self.prompt_version, Unset):
            prompt_version = UNSET
        elif isinstance(self.prompt_version, UUID):
            prompt_version = str(self.prompt_version)
        else:
            prompt_version = self.prompt_version

        prompt_version_detail: dict[str, Any] | Unset = UNSET
        if not isinstance(self.prompt_version_detail, Unset):
            prompt_version_detail = self.prompt_version_detail.to_dict()

        scenarios: list[str] | Unset = UNSET
        if not isinstance(self.scenarios, Unset):
            scenarios = []
            for scenarios_item_data in self.scenarios:
                scenarios_item = str(scenarios_item_data)
                scenarios.append(scenarios_item)

        scenarios_detail: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.scenarios_detail, Unset):
            scenarios_detail = []
            for scenarios_detail_item_data in self.scenarios_detail:
                scenarios_detail_item = scenarios_detail_item_data.to_dict()
                scenarios_detail.append(scenarios_detail_item)

        dataset_row_ids: list[str] | Unset = UNSET
        if not isinstance(self.dataset_row_ids, Unset):
            dataset_row_ids = self.dataset_row_ids

        simulator_agent: None | str | Unset
        if isinstance(self.simulator_agent, Unset):
            simulator_agent = UNSET
        elif isinstance(self.simulator_agent, UUID):
            simulator_agent = str(self.simulator_agent)
        else:
            simulator_agent = self.simulator_agent

        simulator_agent_detail: dict[str, Any] | Unset = UNSET
        if not isinstance(self.simulator_agent_detail, Unset):
            simulator_agent_detail = self.simulator_agent_detail.to_dict()

        simulate_eval_configs: list[str] | Unset = UNSET
        if not isinstance(self.simulate_eval_configs, Unset):
            simulate_eval_configs = []
            for simulate_eval_configs_item_data in self.simulate_eval_configs:
                simulate_eval_configs_item = str(simulate_eval_configs_item_data)
                simulate_eval_configs.append(simulate_eval_configs_item)

        simulate_eval_configs_detail: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.simulate_eval_configs_detail, Unset):
            simulate_eval_configs_detail = []
            for (
                simulate_eval_configs_detail_item_data
            ) in self.simulate_eval_configs_detail:
                simulate_eval_configs_detail_item = (
                    simulate_eval_configs_detail_item_data.to_dict()
                )
                simulate_eval_configs_detail.append(simulate_eval_configs_detail_item)

        evals_detail: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.evals_detail, Unset):
            evals_detail = []
            for evals_detail_item_data in self.evals_detail:
                evals_detail_item = evals_detail_item_data.to_dict()
                evals_detail.append(evals_detail_item)

        organization: str | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = str(self.organization)

        enable_tool_evaluation = self.enable_tool_evaluation

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        last_run_at: None | str | Unset
        if isinstance(self.last_run_at, Unset):
            last_run_at = UNSET
        elif isinstance(self.last_run_at, datetime.datetime):
            last_run_at = self.last_run_at.isoformat()
        else:
            last_run_at = self.last_run_at

        deleted = self.deleted

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if agent_definition is not UNSET:
            field_dict["agent_definition"] = agent_definition
        if agent_version is not UNSET:
            field_dict["agent_version"] = agent_version
        if agent_definition_detail is not UNSET:
            field_dict["agent_definition_detail"] = agent_definition_detail
        if source_type is not UNSET:
            field_dict["source_type"] = source_type
        if source_type_display is not UNSET:
            field_dict["source_type_display"] = source_type_display
        if prompt_template is not UNSET:
            field_dict["prompt_template"] = prompt_template
        if prompt_template_detail is not UNSET:
            field_dict["prompt_template_detail"] = prompt_template_detail
        if prompt_version is not UNSET:
            field_dict["prompt_version"] = prompt_version
        if prompt_version_detail is not UNSET:
            field_dict["prompt_version_detail"] = prompt_version_detail
        if scenarios is not UNSET:
            field_dict["scenarios"] = scenarios
        if scenarios_detail is not UNSET:
            field_dict["scenarios_detail"] = scenarios_detail
        if dataset_row_ids is not UNSET:
            field_dict["dataset_row_ids"] = dataset_row_ids
        if simulator_agent is not UNSET:
            field_dict["simulator_agent"] = simulator_agent
        if simulator_agent_detail is not UNSET:
            field_dict["simulator_agent_detail"] = simulator_agent_detail
        if simulate_eval_configs is not UNSET:
            field_dict["simulate_eval_configs"] = simulate_eval_configs
        if simulate_eval_configs_detail is not UNSET:
            field_dict["simulate_eval_configs_detail"] = simulate_eval_configs_detail
        if evals_detail is not UNSET:
            field_dict["evals_detail"] = evals_detail
        if organization is not UNSET:
            field_dict["organization"] = organization
        if enable_tool_evaluation is not UNSET:
            field_dict["enable_tool_evaluation"] = enable_tool_evaluation
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if last_run_at is not UNSET:
            field_dict["last_run_at"] = last_run_at
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_test_response_agent_definition_detail import (
            RunTestResponseAgentDefinitionDetail,
        )
        from ..models.run_test_response_agent_version import RunTestResponseAgentVersion
        from ..models.run_test_response_prompt_template_detail import (
            RunTestResponsePromptTemplateDetail,
        )
        from ..models.run_test_response_prompt_version_detail import (
            RunTestResponsePromptVersionDetail,
        )
        from ..models.run_test_response_scenarios_detail_item import (
            RunTestResponseScenariosDetailItem,
        )
        from ..models.run_test_response_simulator_agent_detail import (
            RunTestResponseSimulatorAgentDetail,
        )
        from ..models.simulate_eval_config_response import SimulateEvalConfigResponse

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_agent_definition(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                agent_definition_type_0 = UUID(data)

                return agent_definition_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        agent_definition = _parse_agent_definition(d.pop("agent_definition", UNSET))

        _agent_version = d.pop("agent_version", UNSET)
        agent_version: RunTestResponseAgentVersion | Unset
        if isinstance(_agent_version, Unset):
            agent_version = UNSET
        else:
            agent_version = RunTestResponseAgentVersion.from_dict(_agent_version)

        _agent_definition_detail = d.pop("agent_definition_detail", UNSET)
        agent_definition_detail: RunTestResponseAgentDefinitionDetail | Unset
        if isinstance(_agent_definition_detail, Unset):
            agent_definition_detail = UNSET
        else:
            agent_definition_detail = RunTestResponseAgentDefinitionDetail.from_dict(
                _agent_definition_detail
            )

        _source_type = d.pop("source_type", UNSET)
        source_type: RunTestResponseSourceType | Unset
        if isinstance(_source_type, Unset):
            source_type = UNSET
        else:
            source_type = RunTestResponseSourceType(_source_type)

        def _parse_source_type_display(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source_type_display = _parse_source_type_display(
            d.pop("source_type_display", UNSET)
        )

        def _parse_prompt_template(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                prompt_template_type_0 = UUID(data)

                return prompt_template_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        prompt_template = _parse_prompt_template(d.pop("prompt_template", UNSET))

        _prompt_template_detail = d.pop("prompt_template_detail", UNSET)
        prompt_template_detail: RunTestResponsePromptTemplateDetail | Unset
        if isinstance(_prompt_template_detail, Unset):
            prompt_template_detail = UNSET
        else:
            prompt_template_detail = RunTestResponsePromptTemplateDetail.from_dict(
                _prompt_template_detail
            )

        def _parse_prompt_version(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                prompt_version_type_0 = UUID(data)

                return prompt_version_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        prompt_version = _parse_prompt_version(d.pop("prompt_version", UNSET))

        _prompt_version_detail = d.pop("prompt_version_detail", UNSET)
        prompt_version_detail: RunTestResponsePromptVersionDetail | Unset
        if isinstance(_prompt_version_detail, Unset):
            prompt_version_detail = UNSET
        else:
            prompt_version_detail = RunTestResponsePromptVersionDetail.from_dict(
                _prompt_version_detail
            )

        _scenarios = d.pop("scenarios", UNSET)
        scenarios: list[UUID] | Unset = UNSET
        if _scenarios is not UNSET:
            scenarios = []
            for scenarios_item_data in _scenarios:
                scenarios_item = UUID(scenarios_item_data)

                scenarios.append(scenarios_item)

        _scenarios_detail = d.pop("scenarios_detail", UNSET)
        scenarios_detail: list[RunTestResponseScenariosDetailItem] | Unset = UNSET
        if _scenarios_detail is not UNSET:
            scenarios_detail = []
            for scenarios_detail_item_data in _scenarios_detail:
                scenarios_detail_item = RunTestResponseScenariosDetailItem.from_dict(
                    scenarios_detail_item_data
                )

                scenarios_detail.append(scenarios_detail_item)

        dataset_row_ids = cast(list[str], d.pop("dataset_row_ids", UNSET))

        def _parse_simulator_agent(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                simulator_agent_type_0 = UUID(data)

                return simulator_agent_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        simulator_agent = _parse_simulator_agent(d.pop("simulator_agent", UNSET))

        _simulator_agent_detail = d.pop("simulator_agent_detail", UNSET)
        simulator_agent_detail: RunTestResponseSimulatorAgentDetail | Unset
        if isinstance(_simulator_agent_detail, Unset):
            simulator_agent_detail = UNSET
        else:
            simulator_agent_detail = RunTestResponseSimulatorAgentDetail.from_dict(
                _simulator_agent_detail
            )

        _simulate_eval_configs = d.pop("simulate_eval_configs", UNSET)
        simulate_eval_configs: list[UUID] | Unset = UNSET
        if _simulate_eval_configs is not UNSET:
            simulate_eval_configs = []
            for simulate_eval_configs_item_data in _simulate_eval_configs:
                simulate_eval_configs_item = UUID(simulate_eval_configs_item_data)

                simulate_eval_configs.append(simulate_eval_configs_item)

        _simulate_eval_configs_detail = d.pop("simulate_eval_configs_detail", UNSET)
        simulate_eval_configs_detail: list[SimulateEvalConfigResponse] | Unset = UNSET
        if _simulate_eval_configs_detail is not UNSET:
            simulate_eval_configs_detail = []
            for simulate_eval_configs_detail_item_data in _simulate_eval_configs_detail:
                simulate_eval_configs_detail_item = (
                    SimulateEvalConfigResponse.from_dict(
                        simulate_eval_configs_detail_item_data
                    )
                )

                simulate_eval_configs_detail.append(simulate_eval_configs_detail_item)

        _evals_detail = d.pop("evals_detail", UNSET)
        evals_detail: list[SimulateEvalConfigResponse] | Unset = UNSET
        if _evals_detail is not UNSET:
            evals_detail = []
            for evals_detail_item_data in _evals_detail:
                evals_detail_item = SimulateEvalConfigResponse.from_dict(
                    evals_detail_item_data
                )

                evals_detail.append(evals_detail_item)

        _organization = d.pop("organization", UNSET)
        organization: UUID | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = UUID(_organization)

        enable_tool_evaluation = d.pop("enable_tool_evaluation", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_last_run_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_run_at_type_0 = isoparse(data)

                return last_run_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_run_at = _parse_last_run_at(d.pop("last_run_at", UNSET))

        deleted = d.pop("deleted", UNSET)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        run_test_response = cls(
            id=id,
            name=name,
            description=description,
            agent_definition=agent_definition,
            agent_version=agent_version,
            agent_definition_detail=agent_definition_detail,
            source_type=source_type,
            source_type_display=source_type_display,
            prompt_template=prompt_template,
            prompt_template_detail=prompt_template_detail,
            prompt_version=prompt_version,
            prompt_version_detail=prompt_version_detail,
            scenarios=scenarios,
            scenarios_detail=scenarios_detail,
            dataset_row_ids=dataset_row_ids,
            simulator_agent=simulator_agent,
            simulator_agent_detail=simulator_agent_detail,
            simulate_eval_configs=simulate_eval_configs,
            simulate_eval_configs_detail=simulate_eval_configs_detail,
            evals_detail=evals_detail,
            organization=organization,
            enable_tool_evaluation=enable_tool_evaluation,
            created_at=created_at,
            updated_at=updated_at,
            last_run_at=last_run_at,
            deleted=deleted,
            deleted_at=deleted_at,
        )

        run_test_response.additional_properties = d
        return run_test_response

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
