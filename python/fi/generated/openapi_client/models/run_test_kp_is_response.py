from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_test_kp_is_response_scenario_graphs import (
        RunTestKPIsResponseScenarioGraphs,
    )


T = TypeVar("T", bound="RunTestKPIsResponse")


@_attrs_define
class RunTestKPIsResponse:
    """
    Attributes:
        total_calls (int | Unset):
        avg_score (float | Unset):
        avg_response (float | Unset):
        calls_attempted (int | Unset):
        connected_calls (int | Unset):
        calls_connected_percentage (float | Unset):
        scenario_graphs (RunTestKPIsResponseScenarioGraphs | Unset):
        agent_type (str | Unset):
        is_inbound (bool | None | Unset):
        avg_agent_latency (float | Unset):
        avg_user_interruption_count (float | Unset):
        avg_user_interruption_rate (float | Unset):
        avg_user_wpm (float | Unset):
        avg_bot_wpm (float | Unset):
        avg_talk_ratio (float | Unset):
        avg_ai_interruption_count (float | Unset):
        avg_ai_interruption_rate (float | Unset):
        avg_stop_time_after_interruption (float | Unset):
        agent_talk_percentage (float | Unset):
        customer_talk_percentage (float | Unset):
        avg_total_tokens (float | Unset):
        avg_input_tokens (float | Unset):
        avg_output_tokens (float | Unset):
        avg_chat_latency_ms (float | Unset):
        avg_turn_count (float | Unset):
        avg_csat_score (float | Unset):
        failed_calls (int | Unset):
        total_duration (float | Unset):
    """

    total_calls: int | Unset = UNSET
    avg_score: float | Unset = UNSET
    avg_response: float | Unset = UNSET
    calls_attempted: int | Unset = UNSET
    connected_calls: int | Unset = UNSET
    calls_connected_percentage: float | Unset = UNSET
    scenario_graphs: RunTestKPIsResponseScenarioGraphs | Unset = UNSET
    agent_type: str | Unset = UNSET
    is_inbound: bool | None | Unset = UNSET
    avg_agent_latency: float | Unset = UNSET
    avg_user_interruption_count: float | Unset = UNSET
    avg_user_interruption_rate: float | Unset = UNSET
    avg_user_wpm: float | Unset = UNSET
    avg_bot_wpm: float | Unset = UNSET
    avg_talk_ratio: float | Unset = UNSET
    avg_ai_interruption_count: float | Unset = UNSET
    avg_ai_interruption_rate: float | Unset = UNSET
    avg_stop_time_after_interruption: float | Unset = UNSET
    agent_talk_percentage: float | Unset = UNSET
    customer_talk_percentage: float | Unset = UNSET
    avg_total_tokens: float | Unset = UNSET
    avg_input_tokens: float | Unset = UNSET
    avg_output_tokens: float | Unset = UNSET
    avg_chat_latency_ms: float | Unset = UNSET
    avg_turn_count: float | Unset = UNSET
    avg_csat_score: float | Unset = UNSET
    failed_calls: int | Unset = UNSET
    total_duration: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_calls = self.total_calls

        avg_score = self.avg_score

        avg_response = self.avg_response

        calls_attempted = self.calls_attempted

        connected_calls = self.connected_calls

        calls_connected_percentage = self.calls_connected_percentage

        scenario_graphs: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scenario_graphs, Unset):
            scenario_graphs = self.scenario_graphs.to_dict()

        agent_type = self.agent_type

        is_inbound: bool | None | Unset
        if isinstance(self.is_inbound, Unset):
            is_inbound = UNSET
        else:
            is_inbound = self.is_inbound

        avg_agent_latency = self.avg_agent_latency

        avg_user_interruption_count = self.avg_user_interruption_count

        avg_user_interruption_rate = self.avg_user_interruption_rate

        avg_user_wpm = self.avg_user_wpm

        avg_bot_wpm = self.avg_bot_wpm

        avg_talk_ratio = self.avg_talk_ratio

        avg_ai_interruption_count = self.avg_ai_interruption_count

        avg_ai_interruption_rate = self.avg_ai_interruption_rate

        avg_stop_time_after_interruption = self.avg_stop_time_after_interruption

        agent_talk_percentage = self.agent_talk_percentage

        customer_talk_percentage = self.customer_talk_percentage

        avg_total_tokens = self.avg_total_tokens

        avg_input_tokens = self.avg_input_tokens

        avg_output_tokens = self.avg_output_tokens

        avg_chat_latency_ms = self.avg_chat_latency_ms

        avg_turn_count = self.avg_turn_count

        avg_csat_score = self.avg_csat_score

        failed_calls = self.failed_calls

        total_duration = self.total_duration

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if total_calls is not UNSET:
            field_dict["total_calls"] = total_calls
        if avg_score is not UNSET:
            field_dict["avg_score"] = avg_score
        if avg_response is not UNSET:
            field_dict["avg_response"] = avg_response
        if calls_attempted is not UNSET:
            field_dict["calls_attempted"] = calls_attempted
        if connected_calls is not UNSET:
            field_dict["connected_calls"] = connected_calls
        if calls_connected_percentage is not UNSET:
            field_dict["calls_connected_percentage"] = calls_connected_percentage
        if scenario_graphs is not UNSET:
            field_dict["scenario_graphs"] = scenario_graphs
        if agent_type is not UNSET:
            field_dict["agent_type"] = agent_type
        if is_inbound is not UNSET:
            field_dict["is_inbound"] = is_inbound
        if avg_agent_latency is not UNSET:
            field_dict["avg_agent_latency"] = avg_agent_latency
        if avg_user_interruption_count is not UNSET:
            field_dict["avg_user_interruption_count"] = avg_user_interruption_count
        if avg_user_interruption_rate is not UNSET:
            field_dict["avg_user_interruption_rate"] = avg_user_interruption_rate
        if avg_user_wpm is not UNSET:
            field_dict["avg_user_wpm"] = avg_user_wpm
        if avg_bot_wpm is not UNSET:
            field_dict["avg_bot_wpm"] = avg_bot_wpm
        if avg_talk_ratio is not UNSET:
            field_dict["avg_talk_ratio"] = avg_talk_ratio
        if avg_ai_interruption_count is not UNSET:
            field_dict["avg_ai_interruption_count"] = avg_ai_interruption_count
        if avg_ai_interruption_rate is not UNSET:
            field_dict["avg_ai_interruption_rate"] = avg_ai_interruption_rate
        if avg_stop_time_after_interruption is not UNSET:
            field_dict["avg_stop_time_after_interruption"] = (
                avg_stop_time_after_interruption
            )
        if agent_talk_percentage is not UNSET:
            field_dict["agent_talk_percentage"] = agent_talk_percentage
        if customer_talk_percentage is not UNSET:
            field_dict["customer_talk_percentage"] = customer_talk_percentage
        if avg_total_tokens is not UNSET:
            field_dict["avg_total_tokens"] = avg_total_tokens
        if avg_input_tokens is not UNSET:
            field_dict["avg_input_tokens"] = avg_input_tokens
        if avg_output_tokens is not UNSET:
            field_dict["avg_output_tokens"] = avg_output_tokens
        if avg_chat_latency_ms is not UNSET:
            field_dict["avg_chat_latency_ms"] = avg_chat_latency_ms
        if avg_turn_count is not UNSET:
            field_dict["avg_turn_count"] = avg_turn_count
        if avg_csat_score is not UNSET:
            field_dict["avg_csat_score"] = avg_csat_score
        if failed_calls is not UNSET:
            field_dict["failed_calls"] = failed_calls
        if total_duration is not UNSET:
            field_dict["total_duration"] = total_duration

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_test_kp_is_response_scenario_graphs import (
            RunTestKPIsResponseScenarioGraphs,
        )

        d = dict(src_dict)
        total_calls = d.pop("total_calls", UNSET)

        avg_score = d.pop("avg_score", UNSET)

        avg_response = d.pop("avg_response", UNSET)

        calls_attempted = d.pop("calls_attempted", UNSET)

        connected_calls = d.pop("connected_calls", UNSET)

        calls_connected_percentage = d.pop("calls_connected_percentage", UNSET)

        _scenario_graphs = d.pop("scenario_graphs", UNSET)
        scenario_graphs: RunTestKPIsResponseScenarioGraphs | Unset
        if isinstance(_scenario_graphs, Unset):
            scenario_graphs = UNSET
        else:
            scenario_graphs = RunTestKPIsResponseScenarioGraphs.from_dict(
                _scenario_graphs
            )

        agent_type = d.pop("agent_type", UNSET)

        def _parse_is_inbound(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_inbound = _parse_is_inbound(d.pop("is_inbound", UNSET))

        avg_agent_latency = d.pop("avg_agent_latency", UNSET)

        avg_user_interruption_count = d.pop("avg_user_interruption_count", UNSET)

        avg_user_interruption_rate = d.pop("avg_user_interruption_rate", UNSET)

        avg_user_wpm = d.pop("avg_user_wpm", UNSET)

        avg_bot_wpm = d.pop("avg_bot_wpm", UNSET)

        avg_talk_ratio = d.pop("avg_talk_ratio", UNSET)

        avg_ai_interruption_count = d.pop("avg_ai_interruption_count", UNSET)

        avg_ai_interruption_rate = d.pop("avg_ai_interruption_rate", UNSET)

        avg_stop_time_after_interruption = d.pop(
            "avg_stop_time_after_interruption", UNSET
        )

        agent_talk_percentage = d.pop("agent_talk_percentage", UNSET)

        customer_talk_percentage = d.pop("customer_talk_percentage", UNSET)

        avg_total_tokens = d.pop("avg_total_tokens", UNSET)

        avg_input_tokens = d.pop("avg_input_tokens", UNSET)

        avg_output_tokens = d.pop("avg_output_tokens", UNSET)

        avg_chat_latency_ms = d.pop("avg_chat_latency_ms", UNSET)

        avg_turn_count = d.pop("avg_turn_count", UNSET)

        avg_csat_score = d.pop("avg_csat_score", UNSET)

        failed_calls = d.pop("failed_calls", UNSET)

        total_duration = d.pop("total_duration", UNSET)

        run_test_kp_is_response = cls(
            total_calls=total_calls,
            avg_score=avg_score,
            avg_response=avg_response,
            calls_attempted=calls_attempted,
            connected_calls=connected_calls,
            calls_connected_percentage=calls_connected_percentage,
            scenario_graphs=scenario_graphs,
            agent_type=agent_type,
            is_inbound=is_inbound,
            avg_agent_latency=avg_agent_latency,
            avg_user_interruption_count=avg_user_interruption_count,
            avg_user_interruption_rate=avg_user_interruption_rate,
            avg_user_wpm=avg_user_wpm,
            avg_bot_wpm=avg_bot_wpm,
            avg_talk_ratio=avg_talk_ratio,
            avg_ai_interruption_count=avg_ai_interruption_count,
            avg_ai_interruption_rate=avg_ai_interruption_rate,
            avg_stop_time_after_interruption=avg_stop_time_after_interruption,
            agent_talk_percentage=agent_talk_percentage,
            customer_talk_percentage=customer_talk_percentage,
            avg_total_tokens=avg_total_tokens,
            avg_input_tokens=avg_input_tokens,
            avg_output_tokens=avg_output_tokens,
            avg_chat_latency_ms=avg_chat_latency_ms,
            avg_turn_count=avg_turn_count,
            avg_csat_score=avg_csat_score,
            failed_calls=failed_calls,
            total_duration=total_duration,
        )

        run_test_kp_is_response.additional_properties = d
        return run_test_kp_is_response

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
