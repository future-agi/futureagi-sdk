from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.scenario_response import ScenarioResponse


T = TypeVar("T", bound="ScenarioEditResponse")


@_attrs_define
class ScenarioEditResponse:
    """
    Attributes:
        message (str | Unset):
        scenario (ScenarioResponse | Unset):
    """

    message: str | Unset = UNSET
    scenario: ScenarioResponse | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        scenario: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scenario, Unset):
            scenario = self.scenario.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if scenario is not UNSET:
            field_dict["scenario"] = scenario

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.scenario_response import ScenarioResponse

        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _scenario = d.pop("scenario", UNSET)
        scenario: ScenarioResponse | Unset
        if isinstance(_scenario, Unset):
            scenario = UNSET
        else:
            scenario = ScenarioResponse.from_dict(_scenario)

        scenario_edit_response = cls(
            message=message,
            scenario=scenario,
        )

        scenario_edit_response.additional_properties = d
        return scenario_edit_response

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
