from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_version_response import AgentVersionResponse


T = TypeVar("T", bound="AgentVersionActivateResponse")


@_attrs_define
class AgentVersionActivateResponse:
    """
    Attributes:
        message (str | Unset):
        version (AgentVersionResponse | Unset):
    """

    message: str | Unset = UNSET
    version: AgentVersionResponse | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        version: dict[str, Any] | Unset = UNSET
        if not isinstance(self.version, Unset):
            version = self.version.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_version_response import AgentVersionResponse

        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _version = d.pop("version", UNSET)
        version: AgentVersionResponse | Unset
        if isinstance(_version, Unset):
            version = UNSET
        else:
            version = AgentVersionResponse.from_dict(_version)

        agent_version_activate_response = cls(
            message=message,
            version=version,
        )

        agent_version_activate_response.additional_properties = d
        return agent_version_activate_response

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
