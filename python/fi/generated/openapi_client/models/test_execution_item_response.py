from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TestExecutionItemResponse")


@_attrs_define
class TestExecutionItemResponse:
    """
    Attributes:
        id (str | Unset):
        status (str | Unset):
        scenarios (str | Unset):
        start_time (None | str | Unset):
        duration (int | Unset):
        error_reason (None | str | Unset):
        success_rate (float | Unset):
        avg_response_time (float | Unset):
        calls (int | Unset):
        calls_attempted (int | Unset):
        connected_calls (int | Unset):
        agent_version (str | Unset):
        agent_definition (str | Unset):
        calls_connected_percentage (float | Unset):
        total_chats (int | Unset):
        agent_type (str | Unset):
        total_number_of_fagi_agent_turns (int | Unset):
        source_type (str | Unset):
    """

    id: str | Unset = UNSET
    status: str | Unset = UNSET
    scenarios: str | Unset = UNSET
    start_time: None | str | Unset = UNSET
    duration: int | Unset = UNSET
    error_reason: None | str | Unset = UNSET
    success_rate: float | Unset = UNSET
    avg_response_time: float | Unset = UNSET
    calls: int | Unset = UNSET
    calls_attempted: int | Unset = UNSET
    connected_calls: int | Unset = UNSET
    agent_version: str | Unset = UNSET
    agent_definition: str | Unset = UNSET
    calls_connected_percentage: float | Unset = UNSET
    total_chats: int | Unset = UNSET
    agent_type: str | Unset = UNSET
    total_number_of_fagi_agent_turns: int | Unset = UNSET
    source_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        status = self.status

        scenarios = self.scenarios

        start_time: None | str | Unset
        if isinstance(self.start_time, Unset):
            start_time = UNSET
        else:
            start_time = self.start_time

        duration = self.duration

        error_reason: None | str | Unset
        if isinstance(self.error_reason, Unset):
            error_reason = UNSET
        else:
            error_reason = self.error_reason

        success_rate = self.success_rate

        avg_response_time = self.avg_response_time

        calls = self.calls

        calls_attempted = self.calls_attempted

        connected_calls = self.connected_calls

        agent_version = self.agent_version

        agent_definition = self.agent_definition

        calls_connected_percentage = self.calls_connected_percentage

        total_chats = self.total_chats

        agent_type = self.agent_type

        total_number_of_fagi_agent_turns = self.total_number_of_fagi_agent_turns

        source_type = self.source_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if status is not UNSET:
            field_dict["status"] = status
        if scenarios is not UNSET:
            field_dict["scenarios"] = scenarios
        if start_time is not UNSET:
            field_dict["start_time"] = start_time
        if duration is not UNSET:
            field_dict["duration"] = duration
        if error_reason is not UNSET:
            field_dict["error_reason"] = error_reason
        if success_rate is not UNSET:
            field_dict["success_rate"] = success_rate
        if avg_response_time is not UNSET:
            field_dict["avg_response_time"] = avg_response_time
        if calls is not UNSET:
            field_dict["calls"] = calls
        if calls_attempted is not UNSET:
            field_dict["calls_attempted"] = calls_attempted
        if connected_calls is not UNSET:
            field_dict["connected_calls"] = connected_calls
        if agent_version is not UNSET:
            field_dict["agent_version"] = agent_version
        if agent_definition is not UNSET:
            field_dict["agent_definition"] = agent_definition
        if calls_connected_percentage is not UNSET:
            field_dict["calls_connected_percentage"] = calls_connected_percentage
        if total_chats is not UNSET:
            field_dict["total_chats"] = total_chats
        if agent_type is not UNSET:
            field_dict["agent_type"] = agent_type
        if total_number_of_fagi_agent_turns is not UNSET:
            field_dict["total_number_of_fagi_agent_turns"] = (
                total_number_of_fagi_agent_turns
            )
        if source_type is not UNSET:
            field_dict["source_type"] = source_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        status = d.pop("status", UNSET)

        scenarios = d.pop("scenarios", UNSET)

        def _parse_start_time(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        start_time = _parse_start_time(d.pop("start_time", UNSET))

        duration = d.pop("duration", UNSET)

        def _parse_error_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_reason = _parse_error_reason(d.pop("error_reason", UNSET))

        success_rate = d.pop("success_rate", UNSET)

        avg_response_time = d.pop("avg_response_time", UNSET)

        calls = d.pop("calls", UNSET)

        calls_attempted = d.pop("calls_attempted", UNSET)

        connected_calls = d.pop("connected_calls", UNSET)

        agent_version = d.pop("agent_version", UNSET)

        agent_definition = d.pop("agent_definition", UNSET)

        calls_connected_percentage = d.pop("calls_connected_percentage", UNSET)

        total_chats = d.pop("total_chats", UNSET)

        agent_type = d.pop("agent_type", UNSET)

        total_number_of_fagi_agent_turns = d.pop(
            "total_number_of_fagi_agent_turns", UNSET
        )

        source_type = d.pop("source_type", UNSET)

        test_execution_item_response = cls(
            id=id,
            status=status,
            scenarios=scenarios,
            start_time=start_time,
            duration=duration,
            error_reason=error_reason,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            calls=calls,
            calls_attempted=calls_attempted,
            connected_calls=connected_calls,
            agent_version=agent_version,
            agent_definition=agent_definition,
            calls_connected_percentage=calls_connected_percentage,
            total_chats=total_chats,
            agent_type=agent_type,
            total_number_of_fagi_agent_turns=total_number_of_fagi_agent_turns,
            source_type=source_type,
        )

        test_execution_item_response.additional_properties = d
        return test_execution_item_response

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
