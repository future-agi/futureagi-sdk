from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.scenario_prompt_item_role import ScenarioPromptItemRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="ScenarioPromptItem")


@_attrs_define
class ScenarioPromptItem:
    """
    Attributes:
        role (ScenarioPromptItemRole | Unset):
        content (str | Unset):
    """

    role: ScenarioPromptItemRole | Unset = UNSET
    content: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        role: str | Unset = UNSET
        if not isinstance(self.role, Unset):
            role = self.role.value

        content = self.content

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if role is not UNSET:
            field_dict["role"] = role
        if content is not UNSET:
            field_dict["content"] = content

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _role = d.pop("role", UNSET)
        role: ScenarioPromptItemRole | Unset
        if isinstance(_role, Unset):
            role = UNSET
        else:
            role = ScenarioPromptItemRole(_role)

        content = d.pop("content", UNSET)

        scenario_prompt_item = cls(
            role=role,
            content=content,
        )

        scenario_prompt_item.additional_properties = d
        return scenario_prompt_item

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
