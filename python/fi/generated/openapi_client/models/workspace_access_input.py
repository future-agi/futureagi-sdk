from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.workspace_access_input_level import WorkspaceAccessInputLevel
from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkspaceAccessInput")


@_attrs_define
class WorkspaceAccessInput:
    """List of {"workspace_id": "<uuid>", "level": <int>}.

    Attributes:
        workspace_id (UUID):
        level (WorkspaceAccessInputLevel | Unset):
    """

    workspace_id: UUID
    level: WorkspaceAccessInputLevel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workspace_id = str(self.workspace_id)

        level: int | Unset = UNSET
        if not isinstance(self.level, Unset):
            level = self.level.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workspace_id": workspace_id,
            }
        )
        if level is not UNSET:
            field_dict["level"] = level

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workspace_id = UUID(d.pop("workspace_id"))

        _level = d.pop("level", UNSET)
        level: WorkspaceAccessInputLevel | Unset
        if isinstance(_level, Unset):
            level = UNSET
        else:
            level = WorkspaceAccessInputLevel(_level)

        workspace_access_input = cls(
            workspace_id=workspace_id,
            level=level,
        )

        workspace_access_input.additional_properties = d
        return workspace_access_input

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
