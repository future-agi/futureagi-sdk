from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.agent_version_response_status import AgentVersionResponseStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_version_response_configuration_snapshot import (
        AgentVersionResponseConfigurationSnapshot,
    )


T = TypeVar("T", bound="AgentVersionResponse")


@_attrs_define
class AgentVersionResponse:
    """
    Attributes:
        id (UUID | Unset):
        version_number (int | Unset): Version number of the agent
        version_name (None | str | Unset): Human-readable version name (e.g., 'v1.2.3')
        version_name_display (str | Unset):
        status (AgentVersionResponseStatus | Unset): Current status of this version
        status_display (str | Unset):
        score (None | str | Unset): Performance score (0.0 to 10.0)
        test_count (int | Unset): Number of tests run for this version
        pass_rate (None | str | Unset): Test pass rate percentage
        description (str | Unset): Description of changes in this version
        commit_message (None | str | Unset): Commit message for the agent version
        release_notes (None | str | Unset): Detailed release notes for this version
        agent_definition (UUID | Unset): Parent agent definition
        organization (UUID | Unset): Organization this version belongs to
        configuration_snapshot (AgentVersionResponseConfigurationSnapshot | Unset): Snapshot of agent configuration at
            this version
        is_active (str | Unset):
        is_latest (str | Unset):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
    """

    id: UUID | Unset = UNSET
    version_number: int | Unset = UNSET
    version_name: None | str | Unset = UNSET
    version_name_display: str | Unset = UNSET
    status: AgentVersionResponseStatus | Unset = UNSET
    status_display: str | Unset = UNSET
    score: None | str | Unset = UNSET
    test_count: int | Unset = UNSET
    pass_rate: None | str | Unset = UNSET
    description: str | Unset = UNSET
    commit_message: None | str | Unset = UNSET
    release_notes: None | str | Unset = UNSET
    agent_definition: UUID | Unset = UNSET
    organization: UUID | Unset = UNSET
    configuration_snapshot: AgentVersionResponseConfigurationSnapshot | Unset = UNSET
    is_active: str | Unset = UNSET
    is_latest: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        version_number = self.version_number

        version_name: None | str | Unset
        if isinstance(self.version_name, Unset):
            version_name = UNSET
        else:
            version_name = self.version_name

        version_name_display = self.version_name_display

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        status_display = self.status_display

        score: None | str | Unset
        if isinstance(self.score, Unset):
            score = UNSET
        else:
            score = self.score

        test_count = self.test_count

        pass_rate: None | str | Unset
        if isinstance(self.pass_rate, Unset):
            pass_rate = UNSET
        else:
            pass_rate = self.pass_rate

        description = self.description

        commit_message: None | str | Unset
        if isinstance(self.commit_message, Unset):
            commit_message = UNSET
        else:
            commit_message = self.commit_message

        release_notes: None | str | Unset
        if isinstance(self.release_notes, Unset):
            release_notes = UNSET
        else:
            release_notes = self.release_notes

        agent_definition: str | Unset = UNSET
        if not isinstance(self.agent_definition, Unset):
            agent_definition = str(self.agent_definition)

        organization: str | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = str(self.organization)

        configuration_snapshot: dict[str, Any] | Unset = UNSET
        if not isinstance(self.configuration_snapshot, Unset):
            configuration_snapshot = self.configuration_snapshot.to_dict()

        is_active = self.is_active

        is_latest = self.is_latest

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if version_number is not UNSET:
            field_dict["version_number"] = version_number
        if version_name is not UNSET:
            field_dict["version_name"] = version_name
        if version_name_display is not UNSET:
            field_dict["version_name_display"] = version_name_display
        if status is not UNSET:
            field_dict["status"] = status
        if status_display is not UNSET:
            field_dict["status_display"] = status_display
        if score is not UNSET:
            field_dict["score"] = score
        if test_count is not UNSET:
            field_dict["test_count"] = test_count
        if pass_rate is not UNSET:
            field_dict["pass_rate"] = pass_rate
        if description is not UNSET:
            field_dict["description"] = description
        if commit_message is not UNSET:
            field_dict["commit_message"] = commit_message
        if release_notes is not UNSET:
            field_dict["release_notes"] = release_notes
        if agent_definition is not UNSET:
            field_dict["agent_definition"] = agent_definition
        if organization is not UNSET:
            field_dict["organization"] = organization
        if configuration_snapshot is not UNSET:
            field_dict["configuration_snapshot"] = configuration_snapshot
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if is_latest is not UNSET:
            field_dict["is_latest"] = is_latest
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_version_response_configuration_snapshot import (
            AgentVersionResponseConfigurationSnapshot,
        )

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        version_number = d.pop("version_number", UNSET)

        def _parse_version_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        version_name = _parse_version_name(d.pop("version_name", UNSET))

        version_name_display = d.pop("version_name_display", UNSET)

        _status = d.pop("status", UNSET)
        status: AgentVersionResponseStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = AgentVersionResponseStatus(_status)

        status_display = d.pop("status_display", UNSET)

        def _parse_score(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        score = _parse_score(d.pop("score", UNSET))

        test_count = d.pop("test_count", UNSET)

        def _parse_pass_rate(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        pass_rate = _parse_pass_rate(d.pop("pass_rate", UNSET))

        description = d.pop("description", UNSET)

        def _parse_commit_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        commit_message = _parse_commit_message(d.pop("commit_message", UNSET))

        def _parse_release_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        release_notes = _parse_release_notes(d.pop("release_notes", UNSET))

        _agent_definition = d.pop("agent_definition", UNSET)
        agent_definition: UUID | Unset
        if isinstance(_agent_definition, Unset):
            agent_definition = UNSET
        else:
            agent_definition = UUID(_agent_definition)

        _organization = d.pop("organization", UNSET)
        organization: UUID | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = UUID(_organization)

        _configuration_snapshot = d.pop("configuration_snapshot", UNSET)
        configuration_snapshot: AgentVersionResponseConfigurationSnapshot | Unset
        if isinstance(_configuration_snapshot, Unset):
            configuration_snapshot = UNSET
        else:
            configuration_snapshot = (
                AgentVersionResponseConfigurationSnapshot.from_dict(
                    _configuration_snapshot
                )
            )

        is_active = d.pop("is_active", UNSET)

        is_latest = d.pop("is_latest", UNSET)

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

        agent_version_response = cls(
            id=id,
            version_number=version_number,
            version_name=version_name,
            version_name_display=version_name_display,
            status=status,
            status_display=status_display,
            score=score,
            test_count=test_count,
            pass_rate=pass_rate,
            description=description,
            commit_message=commit_message,
            release_notes=release_notes,
            agent_definition=agent_definition,
            organization=organization,
            configuration_snapshot=configuration_snapshot,
            is_active=is_active,
            is_latest=is_latest,
            created_at=created_at,
            updated_at=updated_at,
        )

        agent_version_response.additional_properties = d
        return agent_version_response

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
