from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.scenario_detail_response_scenario_type import (
    ScenarioDetailResponseScenarioType,
)
from ..models.scenario_detail_response_status import ScenarioDetailResponseStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.scenario_detail_response_graph import ScenarioDetailResponseGraph
    from ..models.scenario_prompt_item import ScenarioPromptItem


T = TypeVar("T", bound="ScenarioDetailResponse")


@_attrs_define
class ScenarioDetailResponse:
    """
    Attributes:
        id (UUID | Unset):
        name (str | Unset):
        description (None | str | Unset):
        source (str | Unset):
        scenario_type (ScenarioDetailResponseScenarioType | Unset):
        dataset_id (None | Unset | UUID):
        organization (UUID | Unset):
        dataset (None | Unset | UUID):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        deleted (bool | Unset):
        deleted_at (datetime.datetime | None | Unset):
        status (ScenarioDetailResponseStatus | Unset):
        agent_type (None | str | Unset):
        graph (ScenarioDetailResponseGraph | Unset):
        prompts (list[ScenarioPromptItem] | Unset):
        dataset_rows (int | Unset):
    """

    id: UUID | Unset = UNSET
    name: str | Unset = UNSET
    description: None | str | Unset = UNSET
    source: str | Unset = UNSET
    scenario_type: ScenarioDetailResponseScenarioType | Unset = UNSET
    dataset_id: None | Unset | UUID = UNSET
    organization: UUID | Unset = UNSET
    dataset: None | Unset | UUID = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted: bool | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    status: ScenarioDetailResponseStatus | Unset = UNSET
    agent_type: None | str | Unset = UNSET
    graph: ScenarioDetailResponseGraph | Unset = UNSET
    prompts: list[ScenarioPromptItem] | Unset = UNSET
    dataset_rows: int | Unset = UNSET
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

        source = self.source

        scenario_type: str | Unset = UNSET
        if not isinstance(self.scenario_type, Unset):
            scenario_type = self.scenario_type.value

        dataset_id: None | str | Unset
        if isinstance(self.dataset_id, Unset):
            dataset_id = UNSET
        elif isinstance(self.dataset_id, UUID):
            dataset_id = str(self.dataset_id)
        else:
            dataset_id = self.dataset_id

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

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted = self.deleted

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        agent_type: None | str | Unset
        if isinstance(self.agent_type, Unset):
            agent_type = UNSET
        else:
            agent_type = self.agent_type

        graph: dict[str, Any] | Unset = UNSET
        if not isinstance(self.graph, Unset):
            graph = self.graph.to_dict()

        prompts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.prompts, Unset):
            prompts = []
            for prompts_item_data in self.prompts:
                prompts_item = prompts_item_data.to_dict()
                prompts.append(prompts_item)

        dataset_rows = self.dataset_rows

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if source is not UNSET:
            field_dict["source"] = source
        if scenario_type is not UNSET:
            field_dict["scenario_type"] = scenario_type
        if dataset_id is not UNSET:
            field_dict["dataset_id"] = dataset_id
        if organization is not UNSET:
            field_dict["organization"] = organization
        if dataset is not UNSET:
            field_dict["dataset"] = dataset
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if status is not UNSET:
            field_dict["status"] = status
        if agent_type is not UNSET:
            field_dict["agent_type"] = agent_type
        if graph is not UNSET:
            field_dict["graph"] = graph
        if prompts is not UNSET:
            field_dict["prompts"] = prompts
        if dataset_rows is not UNSET:
            field_dict["dataset_rows"] = dataset_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.scenario_detail_response_graph import ScenarioDetailResponseGraph
        from ..models.scenario_prompt_item import ScenarioPromptItem

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

        source = d.pop("source", UNSET)

        _scenario_type = d.pop("scenario_type", UNSET)
        scenario_type: ScenarioDetailResponseScenarioType | Unset
        if isinstance(_scenario_type, Unset):
            scenario_type = UNSET
        else:
            scenario_type = ScenarioDetailResponseScenarioType(_scenario_type)

        def _parse_dataset_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                dataset_id_type_0 = UUID(data)

                return dataset_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        dataset_id = _parse_dataset_id(d.pop("dataset_id", UNSET))

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

        _status = d.pop("status", UNSET)
        status: ScenarioDetailResponseStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ScenarioDetailResponseStatus(_status)

        def _parse_agent_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        agent_type = _parse_agent_type(d.pop("agent_type", UNSET))

        _graph = d.pop("graph", UNSET)
        graph: ScenarioDetailResponseGraph | Unset
        if isinstance(_graph, Unset):
            graph = UNSET
        else:
            graph = ScenarioDetailResponseGraph.from_dict(_graph)

        _prompts = d.pop("prompts", UNSET)
        prompts: list[ScenarioPromptItem] | Unset = UNSET
        if _prompts is not UNSET:
            prompts = []
            for prompts_item_data in _prompts:
                prompts_item = ScenarioPromptItem.from_dict(prompts_item_data)

                prompts.append(prompts_item)

        dataset_rows = d.pop("dataset_rows", UNSET)

        scenario_detail_response = cls(
            id=id,
            name=name,
            description=description,
            source=source,
            scenario_type=scenario_type,
            dataset_id=dataset_id,
            organization=organization,
            dataset=dataset,
            created_at=created_at,
            updated_at=updated_at,
            deleted=deleted,
            deleted_at=deleted_at,
            status=status,
            agent_type=agent_type,
            graph=graph,
            prompts=prompts,
            dataset_rows=dataset_rows,
        )

        scenario_detail_response.additional_properties = d
        return scenario_detail_response

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
