from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateLinearIssue")


@_attrs_define
class CreateLinearIssue:
    """
    Attributes:
        team_id (str):
        title (str | Unset):
        description (str | Unset):
        priority (int | Unset):  Default: 0.
    """

    team_id: str
    title: str | Unset = UNSET
    description: str | Unset = UNSET
    priority: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        team_id = self.team_id

        title = self.title

        description = self.description

        priority = self.priority

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "team_id": team_id,
            }
        )
        if title is not UNSET:
            field_dict["title"] = title
        if description is not UNSET:
            field_dict["description"] = description
        if priority is not UNSET:
            field_dict["priority"] = priority

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        team_id = d.pop("team_id")

        title = d.pop("title", UNSET)

        description = d.pop("description", UNSET)

        priority = d.pop("priority", UNSET)

        create_linear_issue = cls(
            team_id=team_id,
            title=title,
            description=description,
            priority=priority,
        )

        create_linear_issue.additional_properties = d
        return create_linear_issue

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
