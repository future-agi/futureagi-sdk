from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_version_response import AgentVersionResponse
    from ..models.agent_version_restore_response_agent import (
        AgentVersionRestoreResponseAgent,
    )


T = TypeVar("T", bound="AgentVersionRestoreResponse")


@_attrs_define
class AgentVersionRestoreResponse:
    """
    Attributes:
        message (str | Unset):
        agent (AgentVersionRestoreResponseAgent | Unset):
        version (AgentVersionResponse | Unset):
    """

    message: str | Unset = UNSET
    agent: AgentVersionRestoreResponseAgent | Unset = UNSET
    version: AgentVersionResponse | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        agent: dict[str, Any] | Unset = UNSET
        if not isinstance(self.agent, Unset):
            agent = self.agent.to_dict()

        version: dict[str, Any] | Unset = UNSET
        if not isinstance(self.version, Unset):
            version = self.version.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if agent is not UNSET:
            field_dict["agent"] = agent
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_version_response import AgentVersionResponse
        from ..models.agent_version_restore_response_agent import (
            AgentVersionRestoreResponseAgent,
        )

        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _agent = d.pop("agent", UNSET)
        agent: AgentVersionRestoreResponseAgent | Unset
        if isinstance(_agent, Unset):
            agent = UNSET
        else:
            agent = AgentVersionRestoreResponseAgent.from_dict(_agent)

        _version = d.pop("version", UNSET)
        version: AgentVersionResponse | Unset
        if isinstance(_version, Unset):
            version = UNSET
        else:
            version = AgentVersionResponse.from_dict(_version)

        agent_version_restore_response = cls(
            message=message,
            agent=agent,
            version=version,
        )

        agent_version_restore_response.additional_properties = d
        return agent_version_restore_response

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
