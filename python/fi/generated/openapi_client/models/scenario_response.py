from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.scenario_response_scenario_type import ScenarioResponseScenarioType
from ..models.scenario_response_source_type import ScenarioResponseSourceType
from ..models.scenario_response_status import ScenarioResponseStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="ScenarioResponse")


@_attrs_define
class ScenarioResponse:
    """
    Attributes:
        name (str): Name of the scenario
        source (str): Source content or reference for the scenario
        id (UUID | Unset):
        description (None | str | Unset): Optional description of the scenario
        scenario_type (ScenarioResponseScenarioType | Unset): Type of scenario (graph, script, or dataset)
        scenario_type_display (str | Unset):
        source_type (ScenarioResponseSourceType | Unset): Source type for the scenario: agent_definition or prompt
        source_type_display (str | Unset):
        organization (UUID | Unset): Organization this scenario belongs to
        dataset (None | Unset | UUID): Dataset associated with this scenario (only for dataset type scenarios)
        dataset_rows (str | Unset):
        dataset_column_config (str | Unset):
        graph (str | Unset):
        agent (str | Unset):
        prompt_template (None | Unset | UUID): Prompt template associated with this scenario (only for prompt source
            type)
        prompt_template_detail (str | Unset):
        prompt_version (None | Unset | UUID): Prompt version associated with this scenario (only for prompt source type)
        prompt_version_detail (str | Unset):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        deleted (bool | Unset):
        status (ScenarioResponseStatus | Unset): Status of the scenario
        deleted_at (datetime.datetime | None | Unset):
        agent_type (str | Unset):
    """

    name: str
    source: str
    id: UUID | Unset = UNSET
    description: None | str | Unset = UNSET
    scenario_type: ScenarioResponseScenarioType | Unset = UNSET
    scenario_type_display: str | Unset = UNSET
    source_type: ScenarioResponseSourceType | Unset = UNSET
    source_type_display: str | Unset = UNSET
    organization: UUID | Unset = UNSET
    dataset: None | Unset | UUID = UNSET
    dataset_rows: str | Unset = UNSET
    dataset_column_config: str | Unset = UNSET
    graph: str | Unset = UNSET
    agent: str | Unset = UNSET
    prompt_template: None | Unset | UUID = UNSET
    prompt_template_detail: str | Unset = UNSET
    prompt_version: None | Unset | UUID = UNSET
    prompt_version_detail: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted: bool | Unset = UNSET
    status: ScenarioResponseStatus | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    agent_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        source = self.source

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        scenario_type: str | Unset = UNSET
        if not isinstance(self.scenario_type, Unset):
            scenario_type = self.scenario_type.value

        scenario_type_display = self.scenario_type_display

        source_type: str | Unset = UNSET
        if not isinstance(self.source_type, Unset):
            source_type = self.source_type.value

        source_type_display = self.source_type_display

        organization: str | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = str(self.organization)

        dataset: None | str | Unset
        if isinstance(self.dataset, Unset):
            dataset = UNSET
        elif isinstance(self.dataset, UUID):
            dataset = str(self.dataset)
        else:
            dataset = self.dataset

        dataset_rows = self.dataset_rows

        dataset_column_config = self.dataset_column_config

        graph = self.graph

        agent = self.agent

        prompt_template: None | str | Unset
        if isinstance(self.prompt_template, Unset):
            prompt_template = UNSET
        elif isinstance(self.prompt_template, UUID):
            prompt_template = str(self.prompt_template)
        else:
            prompt_template = self.prompt_template

        prompt_template_detail = self.prompt_template_detail

        prompt_version: None | str | Unset
        if isinstance(self.prompt_version, Unset):
            prompt_version = UNSET
        elif isinstance(self.prompt_version, UUID):
            prompt_version = str(self.prompt_version)
        else:
            prompt_version = self.prompt_version

        prompt_version_detail = self.prompt_version_detail

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted = self.deleted

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        agent_type = self.agent_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "source": source,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if description is not UNSET:
            field_dict["description"] = description
        if scenario_type is not UNSET:
            field_dict["scenario_type"] = scenario_type
        if scenario_type_display is not UNSET:
            field_dict["scenario_type_display"] = scenario_type_display
        if source_type is not UNSET:
            field_dict["source_type"] = source_type
        if source_type_display is not UNSET:
            field_dict["source_type_display"] = source_type_display
        if organization is not UNSET:
            field_dict["organization"] = organization
        if dataset is not UNSET:
            field_dict["dataset"] = dataset
        if dataset_rows is not UNSET:
            field_dict["dataset_rows"] = dataset_rows
        if dataset_column_config is not UNSET:
            field_dict["dataset_column_config"] = dataset_column_config
        if graph is not UNSET:
            field_dict["graph"] = graph
        if agent is not UNSET:
            field_dict["agent"] = agent
        if prompt_template is not UNSET:
            field_dict["prompt_template"] = prompt_template
        if prompt_template_detail is not UNSET:
            field_dict["prompt_template_detail"] = prompt_template_detail
        if prompt_version is not UNSET:
            field_dict["prompt_version"] = prompt_version
        if prompt_version_detail is not UNSET:
            field_dict["prompt_version_detail"] = prompt_version_detail
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if status is not UNSET:
            field_dict["status"] = status
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if agent_type is not UNSET:
            field_dict["agent_type"] = agent_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        source = d.pop("source")

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _scenario_type = d.pop("scenario_type", UNSET)
        scenario_type: ScenarioResponseScenarioType | Unset
        if isinstance(_scenario_type, Unset):
            scenario_type = UNSET
        else:
            scenario_type = ScenarioResponseScenarioType(_scenario_type)

        scenario_type_display = d.pop("scenario_type_display", UNSET)

        _source_type = d.pop("source_type", UNSET)
        source_type: ScenarioResponseSourceType | Unset
        if isinstance(_source_type, Unset):
            source_type = UNSET
        else:
            source_type = ScenarioResponseSourceType(_source_type)

        source_type_display = d.pop("source_type_display", UNSET)

        _organization = d.pop("organization", UNSET)
        organization: UUID | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = UUID(_organization)

        def _parse_dataset(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                dataset_type_0 = UUID(data)

                return dataset_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        dataset = _parse_dataset(d.pop("dataset", UNSET))

        dataset_rows = d.pop("dataset_rows", UNSET)

        dataset_column_config = d.pop("dataset_column_config", UNSET)

        graph = d.pop("graph", UNSET)

        agent = d.pop("agent", UNSET)

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

        prompt_template_detail = d.pop("prompt_template_detail", UNSET)

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

        prompt_version_detail = d.pop("prompt_version_detail", UNSET)

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

        deleted = d.pop("deleted", UNSET)

        _status = d.pop("status", UNSET)
        status: ScenarioResponseStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ScenarioResponseStatus(_status)

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

        agent_type = d.pop("agent_type", UNSET)

        scenario_response = cls(
            name=name,
            source=source,
            id=id,
            description=description,
            scenario_type=scenario_type,
            scenario_type_display=scenario_type_display,
            source_type=source_type,
            source_type_display=source_type_display,
            organization=organization,
            dataset=dataset,
            dataset_rows=dataset_rows,
            dataset_column_config=dataset_column_config,
            graph=graph,
            agent=agent,
            prompt_template=prompt_template,
            prompt_template_detail=prompt_template_detail,
            prompt_version=prompt_version,
            prompt_version_detail=prompt_version_detail,
            created_at=created_at,
            updated_at=updated_at,
            deleted=deleted,
            status=status,
            deleted_at=deleted_at,
            agent_type=agent_type,
        )

        scenario_response.additional_properties = d
        return scenario_response

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
