from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.feed_update_body_severity import FeedUpdateBodySeverity
from ..models.feed_update_body_status import FeedUpdateBodyStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="FeedUpdateBody")


@_attrs_define
class FeedUpdateBody:
    """
    Attributes:
        project_id (UUID | Unset):
        status (FeedUpdateBodyStatus | Unset):
        severity (FeedUpdateBodySeverity | Unset):
        assignee (None | str | Unset):
    """

    project_id: UUID | Unset = UNSET
    status: FeedUpdateBodyStatus | Unset = UNSET
    severity: FeedUpdateBodySeverity | Unset = UNSET
    assignee: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_id: str | Unset = UNSET
        if not isinstance(self.project_id, Unset):
            project_id = str(self.project_id)

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        severity: str | Unset = UNSET
        if not isinstance(self.severity, Unset):
            severity = self.severity.value

        assignee: None | str | Unset
        if isinstance(self.assignee, Unset):
            assignee = UNSET
        else:
            assignee = self.assignee

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if status is not UNSET:
            field_dict["status"] = status
        if severity is not UNSET:
            field_dict["severity"] = severity
        if assignee is not UNSET:
            field_dict["assignee"] = assignee

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

        _status = d.pop("status", UNSET)
        status: FeedUpdateBodyStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = FeedUpdateBodyStatus(_status)

        _severity = d.pop("severity", UNSET)
        severity: FeedUpdateBodySeverity | Unset
        if isinstance(_severity, Unset):
            severity = UNSET
        else:
            severity = FeedUpdateBodySeverity(_severity)

        def _parse_assignee(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        assignee = _parse_assignee(d.pop("assignee", UNSET))

        feed_update_body = cls(
            project_id=project_id,
            status=status,
            severity=severity,
            assignee=assignee,
        )

        feed_update_body.additional_properties = d
        return feed_update_body

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
