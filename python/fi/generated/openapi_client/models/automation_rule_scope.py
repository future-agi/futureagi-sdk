from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AutomationRuleScope")


@_attrs_define
class AutomationRuleScope:
    """
    Attributes:
        dataset_id (UUID | Unset):
        project_id (UUID | Unset):
        is_voice_call (bool | Unset):
        remove_simulation_calls (bool | Unset):
    """

    dataset_id: UUID | Unset = UNSET
    project_id: UUID | Unset = UNSET
    is_voice_call: bool | Unset = UNSET
    remove_simulation_calls: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id: str | Unset = UNSET
        if not isinstance(self.dataset_id, Unset):
            dataset_id = str(self.dataset_id)

        project_id: str | Unset = UNSET
        if not isinstance(self.project_id, Unset):
            project_id = str(self.project_id)

        is_voice_call = self.is_voice_call

        remove_simulation_calls = self.remove_simulation_calls

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if dataset_id is not UNSET:
            field_dict["dataset_id"] = dataset_id
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if is_voice_call is not UNSET:
            field_dict["is_voice_call"] = is_voice_call
        if remove_simulation_calls is not UNSET:
            field_dict["remove_simulation_calls"] = remove_simulation_calls

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _dataset_id = d.pop("dataset_id", UNSET)
        dataset_id: UUID | Unset
        if isinstance(_dataset_id, Unset):
            dataset_id = UNSET
        else:
            dataset_id = UUID(_dataset_id)

        _project_id = d.pop("project_id", UNSET)
        project_id: UUID | Unset
        if isinstance(_project_id, Unset):
            project_id = UNSET
        else:
            project_id = UUID(_project_id)

        is_voice_call = d.pop("is_voice_call", UNSET)

        remove_simulation_calls = d.pop("remove_simulation_calls", UNSET)

        automation_rule_scope = cls(
            dataset_id=dataset_id,
            project_id=project_id,
            is_voice_call=is_voice_call,
            remove_simulation_calls=remove_simulation_calls,
        )

        automation_rule_scope.additional_properties = d
        return automation_rule_scope

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
