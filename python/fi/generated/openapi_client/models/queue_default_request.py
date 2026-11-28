from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueDefaultRequest")


@_attrs_define
class QueueDefaultRequest:
    """
    Attributes:
        project_id (UUID | Unset):
        dataset_id (UUID | Unset):
        agent_definition_id (UUID | Unset):
    """

    project_id: UUID | Unset = UNSET
    dataset_id: UUID | Unset = UNSET
    agent_definition_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_id: str | Unset = UNSET
        if not isinstance(self.project_id, Unset):
            project_id = str(self.project_id)

        dataset_id: str | Unset = UNSET
        if not isinstance(self.dataset_id, Unset):
            dataset_id = str(self.dataset_id)

        agent_definition_id: str | Unset = UNSET
        if not isinstance(self.agent_definition_id, Unset):
            agent_definition_id = str(self.agent_definition_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if dataset_id is not UNSET:
            field_dict["dataset_id"] = dataset_id
        if agent_definition_id is not UNSET:
            field_dict["agent_definition_id"] = agent_definition_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _project_id = d.pop("project_id", UNSET)
        project_id: UUID | Unset
        if isinstance(_project_id, Unset):
            project_id = UNSET
        else:
            project_id = UUID(_project_id)

        _dataset_id = d.pop("dataset_id", UNSET)
        dataset_id: UUID | Unset
        if isinstance(_dataset_id, Unset):
            dataset_id = UNSET
        else:
            dataset_id = UUID(_dataset_id)

        _agent_definition_id = d.pop("agent_definition_id", UNSET)
        agent_definition_id: UUID | Unset
        if isinstance(_agent_definition_id, Unset):
            agent_definition_id = UNSET
        else:
            agent_definition_id = UUID(_agent_definition_id)

        queue_default_request = cls(
            project_id=project_id,
            dataset_id=dataset_id,
            agent_definition_id=agent_definition_id,
        )

        queue_default_request.additional_properties = d
        return queue_default_request

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
