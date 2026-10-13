from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.call_branch_deviation_create_response_deviation_data import (
        CallBranchDeviationCreateResponseDeviationData,
    )


T = TypeVar("T", bound="CallBranchDeviationCreateResponse")


@_attrs_define
class CallBranchDeviationCreateResponse:
    """
    Attributes:
        call_execution_id (UUID | Unset):
        scenario_graph_id (UUID | Unset):
        deviation_data (CallBranchDeviationCreateResponseDeviationData | Unset):
        message (str | Unset):
    """

    call_execution_id: UUID | Unset = UNSET
    scenario_graph_id: UUID | Unset = UNSET
    deviation_data: CallBranchDeviationCreateResponseDeviationData | Unset = UNSET
    message: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        call_execution_id: str | Unset = UNSET
        if not isinstance(self.call_execution_id, Unset):
            call_execution_id = str(self.call_execution_id)

        scenario_graph_id: str | Unset = UNSET
        if not isinstance(self.scenario_graph_id, Unset):
            scenario_graph_id = str(self.scenario_graph_id)

        deviation_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.deviation_data, Unset):
            deviation_data = self.deviation_data.to_dict()

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if call_execution_id is not UNSET:
            field_dict["call_execution_id"] = call_execution_id
        if scenario_graph_id is not UNSET:
            field_dict["scenario_graph_id"] = scenario_graph_id
        if deviation_data is not UNSET:
            field_dict["deviation_data"] = deviation_data
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.call_branch_deviation_create_response_deviation_data import (
            CallBranchDeviationCreateResponseDeviationData,
        )

        d = dict(src_dict)
        _call_execution_id = d.pop("call_execution_id", UNSET)
        call_execution_id: UUID | Unset
        if isinstance(_call_execution_id, Unset):
            call_execution_id = UNSET
        else:
            call_execution_id = UUID(_call_execution_id)

        _scenario_graph_id = d.pop("scenario_graph_id", UNSET)
        scenario_graph_id: UUID | Unset
        if isinstance(_scenario_graph_id, Unset):
            scenario_graph_id = UNSET
        else:
            scenario_graph_id = UUID(_scenario_graph_id)

        _deviation_data = d.pop("deviation_data", UNSET)
        deviation_data: CallBranchDeviationCreateResponseDeviationData | Unset
        if isinstance(_deviation_data, Unset):
            deviation_data = UNSET
        else:
            deviation_data = CallBranchDeviationCreateResponseDeviationData.from_dict(
                _deviation_data
            )

        message = d.pop("message", UNSET)

        call_branch_deviation_create_response = cls(
            call_execution_id=call_execution_id,
            scenario_graph_id=scenario_graph_id,
            deviation_data=deviation_data,
            message=message,
        )

        call_branch_deviation_create_response.additional_properties = d
        return call_branch_deviation_create_response

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
