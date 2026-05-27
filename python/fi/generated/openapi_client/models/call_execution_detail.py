from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.call_execution_detail_simulation_call_type import (
    CallExecutionDetailSimulationCallType,
)
from ..models.call_execution_detail_status import CallExecutionDetailStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.call_execution_detail_customer_cost_breakdown import (
        CallExecutionDetailCustomerCostBreakdown,
    )
    from ..models.call_execution_detail_customer_latency_metrics import (
        CallExecutionDetailCustomerLatencyMetrics,
    )
    from ..models.call_execution_detail_tool_outputs import (
        CallExecutionDetailToolOutputs,
    )


T = TypeVar("T", bound="CallExecutionDetail")


@_attrs_define
class CallExecutionDetail:
    """
    Attributes:
        id (UUID | Unset):
        service_provider_call_id (str | Unset):
        session_id (str | Unset):
        timestamp (datetime.datetime | Unset):
        call_type (str | Unset):
        status (CallExecutionDetailStatus | Unset): Current status of the call
        duration (str | Unset):
        duration_seconds (int | None | Unset): Duration of the call in seconds
        start_time (str | Unset):
        transcript (str | Unset):
        scenario (str | Unset):
        overall_score (str | Unset):
        response_time (str | Unset):
        response_time_ms (int | None | Unset): Average response time in milliseconds
        audio_url (str | Unset):
        customer_name (str | Unset):
        eval_outputs (str | Unset):
        eval_metrics (str | Unset):
        scenario_columns (str | Unset):
        ended_reason (None | str | Unset): Reason why the call ended
        simulator_agent_name (str | Unset):
        simulator_agent_id (UUID | Unset):
        agent_definition_used_name (str | Unset):
        agent_definition_used_id (UUID | Unset):
        call_summary (None | str | Unset): Call summary from the service
        recordings (str | Unset):
        scenario_id (str | Unset):
        avg_agent_latency (int | Unset):
        avg_agent_latency_ms (int | None | Unset): Average agent latency in milliseconds (time taken by agent to respond
            after user's pause)
        user_interruption_count (int | None | Unset): Number of times user interrupted the AI
        user_interruption_rate (float | None | Unset): Rate of user interruptions (interruptions per minute)
        user_wpm (float | None | Unset): User's words per minute
        bot_wpm (float | None | Unset): Bot's words per minute
        talk_ratio (float | None | Unset): Ratio of bot speaking time to user speaking time
        ai_interruption_count (int | None | Unset): Number of times AI interrupted the user
        ai_interruption_rate (float | None | Unset): Rate of AI interruptions (interruptions per minute)
        avg_stop_time_after_interruption (int | Unset):
        total_tokens (str | Unset):
        input_tokens (str | Unset):
        output_tokens (str | Unset):
        avg_latency_ms (str | Unset):
        turn_count (str | Unset):
        agent_talk_percentage (str | Unset):
        csat_score (str | Unset):
        processing_skipped (str | Unset):
        processing_skip_reason (str | Unset):
        rerun_snapshots (str | Unset):
        is_snapshot (str | Unset):
        snapshot_timestamp (str | Unset):
        rerun_type (str | Unset):
        original_call_execution_id (str | Unset):
        tool_outputs (CallExecutionDetailToolOutputs | Unset): Tool evaluation output - separate from standard
            evaluations
        cost_cents (int | None | Unset): Cost of the call in cents
        customer_cost_cents (int | None | Unset): Total customer-reported cost in cents
        customer_cost_breakdown (CallExecutionDetailCustomerCostBreakdown | Unset): Detailed cost breakdown from
            customer call data
        customer_latency_metrics (CallExecutionDetailCustomerLatencyMetrics | Unset): Latency metrics from customer call
            data
        customer_call_id (None | str | Unset): Customer call ID if available
        simulation_call_type (CallExecutionDetailSimulationCallType | Unset): Type of simulation call
        provider (str | Unset):
        phone_number (None | str | Unset): Phone number called (null for TEXT/chat simulations)
    """

    id: UUID | Unset = UNSET
    service_provider_call_id: str | Unset = UNSET
    session_id: str | Unset = UNSET
    timestamp: datetime.datetime | Unset = UNSET
    call_type: str | Unset = UNSET
    status: CallExecutionDetailStatus | Unset = UNSET
    duration: str | Unset = UNSET
    duration_seconds: int | None | Unset = UNSET
    start_time: str | Unset = UNSET
    transcript: str | Unset = UNSET
    scenario: str | Unset = UNSET
    overall_score: str | Unset = UNSET
    response_time: str | Unset = UNSET
    response_time_ms: int | None | Unset = UNSET
    audio_url: str | Unset = UNSET
    customer_name: str | Unset = UNSET
    eval_outputs: str | Unset = UNSET
    eval_metrics: str | Unset = UNSET
    scenario_columns: str | Unset = UNSET
    ended_reason: None | str | Unset = UNSET
    simulator_agent_name: str | Unset = UNSET
    simulator_agent_id: UUID | Unset = UNSET
    agent_definition_used_name: str | Unset = UNSET
    agent_definition_used_id: UUID | Unset = UNSET
    call_summary: None | str | Unset = UNSET
    recordings: str | Unset = UNSET
    scenario_id: str | Unset = UNSET
    avg_agent_latency: int | Unset = UNSET
    avg_agent_latency_ms: int | None | Unset = UNSET
    user_interruption_count: int | None | Unset = UNSET
    user_interruption_rate: float | None | Unset = UNSET
    user_wpm: float | None | Unset = UNSET
    bot_wpm: float | None | Unset = UNSET
    talk_ratio: float | None | Unset = UNSET
    ai_interruption_count: int | None | Unset = UNSET
    ai_interruption_rate: float | None | Unset = UNSET
    avg_stop_time_after_interruption: int | Unset = UNSET
    total_tokens: str | Unset = UNSET
    input_tokens: str | Unset = UNSET
    output_tokens: str | Unset = UNSET
    avg_latency_ms: str | Unset = UNSET
    turn_count: str | Unset = UNSET
    agent_talk_percentage: str | Unset = UNSET
    csat_score: str | Unset = UNSET
    processing_skipped: str | Unset = UNSET
    processing_skip_reason: str | Unset = UNSET
    rerun_snapshots: str | Unset = UNSET
    is_snapshot: str | Unset = UNSET
    snapshot_timestamp: str | Unset = UNSET
    rerun_type: str | Unset = UNSET
    original_call_execution_id: str | Unset = UNSET
    tool_outputs: CallExecutionDetailToolOutputs | Unset = UNSET
    cost_cents: int | None | Unset = UNSET
    customer_cost_cents: int | None | Unset = UNSET
    customer_cost_breakdown: CallExecutionDetailCustomerCostBreakdown | Unset = UNSET
    customer_latency_metrics: CallExecutionDetailCustomerLatencyMetrics | Unset = UNSET
    customer_call_id: None | str | Unset = UNSET
    simulation_call_type: CallExecutionDetailSimulationCallType | Unset = UNSET
    provider: str | Unset = UNSET
    phone_number: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        service_provider_call_id = self.service_provider_call_id

        session_id = self.session_id

        timestamp: str | Unset = UNSET
        if not isinstance(self.timestamp, Unset):
            timestamp = self.timestamp.isoformat()

        call_type = self.call_type

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        duration = self.duration

        duration_seconds: int | None | Unset
        if isinstance(self.duration_seconds, Unset):
            duration_seconds = UNSET
        else:
            duration_seconds = self.duration_seconds

        start_time = self.start_time

        transcript = self.transcript

        scenario = self.scenario

        overall_score = self.overall_score

        response_time = self.response_time

        response_time_ms: int | None | Unset
        if isinstance(self.response_time_ms, Unset):
            response_time_ms = UNSET
        else:
            response_time_ms = self.response_time_ms

        audio_url = self.audio_url

        customer_name = self.customer_name

        eval_outputs = self.eval_outputs

        eval_metrics = self.eval_metrics

        scenario_columns = self.scenario_columns

        ended_reason: None | str | Unset
        if isinstance(self.ended_reason, Unset):
            ended_reason = UNSET
        else:
            ended_reason = self.ended_reason

        simulator_agent_name = self.simulator_agent_name

        simulator_agent_id: str | Unset = UNSET
        if not isinstance(self.simulator_agent_id, Unset):
            simulator_agent_id = str(self.simulator_agent_id)

        agent_definition_used_name = self.agent_definition_used_name

        agent_definition_used_id: str | Unset = UNSET
        if not isinstance(self.agent_definition_used_id, Unset):
            agent_definition_used_id = str(self.agent_definition_used_id)

        call_summary: None | str | Unset
        if isinstance(self.call_summary, Unset):
            call_summary = UNSET
        else:
            call_summary = self.call_summary

        recordings = self.recordings

        scenario_id = self.scenario_id

        avg_agent_latency = self.avg_agent_latency

        avg_agent_latency_ms: int | None | Unset
        if isinstance(self.avg_agent_latency_ms, Unset):
            avg_agent_latency_ms = UNSET
        else:
            avg_agent_latency_ms = self.avg_agent_latency_ms

        user_interruption_count: int | None | Unset
        if isinstance(self.user_interruption_count, Unset):
            user_interruption_count = UNSET
        else:
            user_interruption_count = self.user_interruption_count

        user_interruption_rate: float | None | Unset
        if isinstance(self.user_interruption_rate, Unset):
            user_interruption_rate = UNSET
        else:
            user_interruption_rate = self.user_interruption_rate

        user_wpm: float | None | Unset
        if isinstance(self.user_wpm, Unset):
            user_wpm = UNSET
        else:
            user_wpm = self.user_wpm

        bot_wpm: float | None | Unset
        if isinstance(self.bot_wpm, Unset):
            bot_wpm = UNSET
        else:
            bot_wpm = self.bot_wpm

        talk_ratio: float | None | Unset
        if isinstance(self.talk_ratio, Unset):
            talk_ratio = UNSET
        else:
            talk_ratio = self.talk_ratio

        ai_interruption_count: int | None | Unset
        if isinstance(self.ai_interruption_count, Unset):
            ai_interruption_count = UNSET
        else:
            ai_interruption_count = self.ai_interruption_count

        ai_interruption_rate: float | None | Unset
        if isinstance(self.ai_interruption_rate, Unset):
            ai_interruption_rate = UNSET
        else:
            ai_interruption_rate = self.ai_interruption_rate

        avg_stop_time_after_interruption = self.avg_stop_time_after_interruption

        total_tokens = self.total_tokens

        input_tokens = self.input_tokens

        output_tokens = self.output_tokens

        avg_latency_ms = self.avg_latency_ms

        turn_count = self.turn_count

        agent_talk_percentage = self.agent_talk_percentage

        csat_score = self.csat_score

        processing_skipped = self.processing_skipped

        processing_skip_reason = self.processing_skip_reason

        rerun_snapshots = self.rerun_snapshots

        is_snapshot = self.is_snapshot

        snapshot_timestamp = self.snapshot_timestamp

        rerun_type = self.rerun_type

        original_call_execution_id = self.original_call_execution_id

        tool_outputs: dict[str, Any] | Unset = UNSET
        if not isinstance(self.tool_outputs, Unset):
            tool_outputs = self.tool_outputs.to_dict()

        cost_cents: int | None | Unset
        if isinstance(self.cost_cents, Unset):
            cost_cents = UNSET
        else:
            cost_cents = self.cost_cents

        customer_cost_cents: int | None | Unset
        if isinstance(self.customer_cost_cents, Unset):
            customer_cost_cents = UNSET
        else:
            customer_cost_cents = self.customer_cost_cents

        customer_cost_breakdown: dict[str, Any] | Unset = UNSET
        if not isinstance(self.customer_cost_breakdown, Unset):
            customer_cost_breakdown = self.customer_cost_breakdown.to_dict()

        customer_latency_metrics: dict[str, Any] | Unset = UNSET
        if not isinstance(self.customer_latency_metrics, Unset):
            customer_latency_metrics = self.customer_latency_metrics.to_dict()

        customer_call_id: None | str | Unset
        if isinstance(self.customer_call_id, Unset):
            customer_call_id = UNSET
        else:
            customer_call_id = self.customer_call_id

        simulation_call_type: str | Unset = UNSET
        if not isinstance(self.simulation_call_type, Unset):
            simulation_call_type = self.simulation_call_type.value

        provider = self.provider

        phone_number: None | str | Unset
        if isinstance(self.phone_number, Unset):
            phone_number = UNSET
        else:
            phone_number = self.phone_number

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if service_provider_call_id is not UNSET:
            field_dict["service_provider_call_id"] = service_provider_call_id
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp
        if call_type is not UNSET:
            field_dict["call_type"] = call_type
        if status is not UNSET:
            field_dict["status"] = status
        if duration is not UNSET:
            field_dict["duration"] = duration
        if duration_seconds is not UNSET:
            field_dict["duration_seconds"] = duration_seconds
        if start_time is not UNSET:
            field_dict["start_time"] = start_time
        if transcript is not UNSET:
            field_dict["transcript"] = transcript
        if scenario is not UNSET:
            field_dict["scenario"] = scenario
        if overall_score is not UNSET:
            field_dict["overall_score"] = overall_score
        if response_time is not UNSET:
            field_dict["response_time"] = response_time
        if response_time_ms is not UNSET:
            field_dict["response_time_ms"] = response_time_ms
        if audio_url is not UNSET:
            field_dict["audio_url"] = audio_url
        if customer_name is not UNSET:
            field_dict["customer_name"] = customer_name
        if eval_outputs is not UNSET:
            field_dict["eval_outputs"] = eval_outputs
        if eval_metrics is not UNSET:
            field_dict["eval_metrics"] = eval_metrics
        if scenario_columns is not UNSET:
            field_dict["scenario_columns"] = scenario_columns
        if ended_reason is not UNSET:
            field_dict["ended_reason"] = ended_reason
        if simulator_agent_name is not UNSET:
            field_dict["simulator_agent_name"] = simulator_agent_name
        if simulator_agent_id is not UNSET:
            field_dict["simulator_agent_id"] = simulator_agent_id
        if agent_definition_used_name is not UNSET:
            field_dict["agent_definition_used_name"] = agent_definition_used_name
        if agent_definition_used_id is not UNSET:
            field_dict["agent_definition_used_id"] = agent_definition_used_id
        if call_summary is not UNSET:
            field_dict["call_summary"] = call_summary
        if recordings is not UNSET:
            field_dict["recordings"] = recordings
        if scenario_id is not UNSET:
            field_dict["scenario_id"] = scenario_id
        if avg_agent_latency is not UNSET:
            field_dict["avg_agent_latency"] = avg_agent_latency
        if avg_agent_latency_ms is not UNSET:
            field_dict["avg_agent_latency_ms"] = avg_agent_latency_ms
        if user_interruption_count is not UNSET:
            field_dict["user_interruption_count"] = user_interruption_count
        if user_interruption_rate is not UNSET:
            field_dict["user_interruption_rate"] = user_interruption_rate
        if user_wpm is not UNSET:
            field_dict["user_wpm"] = user_wpm
        if bot_wpm is not UNSET:
            field_dict["bot_wpm"] = bot_wpm
        if talk_ratio is not UNSET:
            field_dict["talk_ratio"] = talk_ratio
        if ai_interruption_count is not UNSET:
            field_dict["ai_interruption_count"] = ai_interruption_count
        if ai_interruption_rate is not UNSET:
            field_dict["ai_interruption_rate"] = ai_interruption_rate
        if avg_stop_time_after_interruption is not UNSET:
            field_dict["avg_stop_time_after_interruption"] = (
                avg_stop_time_after_interruption
            )
        if total_tokens is not UNSET:
            field_dict["total_tokens"] = total_tokens
        if input_tokens is not UNSET:
            field_dict["input_tokens"] = input_tokens
        if output_tokens is not UNSET:
            field_dict["output_tokens"] = output_tokens
        if avg_latency_ms is not UNSET:
            field_dict["avg_latency_ms"] = avg_latency_ms
        if turn_count is not UNSET:
            field_dict["turn_count"] = turn_count
        if agent_talk_percentage is not UNSET:
            field_dict["agent_talk_percentage"] = agent_talk_percentage
        if csat_score is not UNSET:
            field_dict["csat_score"] = csat_score
        if processing_skipped is not UNSET:
            field_dict["processing_skipped"] = processing_skipped
        if processing_skip_reason is not UNSET:
            field_dict["processing_skip_reason"] = processing_skip_reason
        if rerun_snapshots is not UNSET:
            field_dict["rerun_snapshots"] = rerun_snapshots
        if is_snapshot is not UNSET:
            field_dict["is_snapshot"] = is_snapshot
        if snapshot_timestamp is not UNSET:
            field_dict["snapshot_timestamp"] = snapshot_timestamp
        if rerun_type is not UNSET:
            field_dict["rerun_type"] = rerun_type
        if original_call_execution_id is not UNSET:
            field_dict["original_call_execution_id"] = original_call_execution_id
        if tool_outputs is not UNSET:
            field_dict["tool_outputs"] = tool_outputs
        if cost_cents is not UNSET:
            field_dict["cost_cents"] = cost_cents
        if customer_cost_cents is not UNSET:
            field_dict["customer_cost_cents"] = customer_cost_cents
        if customer_cost_breakdown is not UNSET:
            field_dict["customer_cost_breakdown"] = customer_cost_breakdown
        if customer_latency_metrics is not UNSET:
            field_dict["customer_latency_metrics"] = customer_latency_metrics
        if customer_call_id is not UNSET:
            field_dict["customer_call_id"] = customer_call_id
        if simulation_call_type is not UNSET:
            field_dict["simulation_call_type"] = simulation_call_type
        if provider is not UNSET:
            field_dict["provider"] = provider
        if phone_number is not UNSET:
            field_dict["phone_number"] = phone_number

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.call_execution_detail_customer_cost_breakdown import (
            CallExecutionDetailCustomerCostBreakdown,
        )
        from ..models.call_execution_detail_customer_latency_metrics import (
            CallExecutionDetailCustomerLatencyMetrics,
        )
        from ..models.call_execution_detail_tool_outputs import (
            CallExecutionDetailToolOutputs,
        )

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        service_provider_call_id = d.pop("service_provider_call_id", UNSET)

        session_id = d.pop("session_id", UNSET)

        _timestamp = d.pop("timestamp", UNSET)
        timestamp: datetime.datetime | Unset
        if isinstance(_timestamp, Unset):
            timestamp = UNSET
        else:
            timestamp = isoparse(_timestamp)

        call_type = d.pop("call_type", UNSET)

        _status = d.pop("status", UNSET)
        status: CallExecutionDetailStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = CallExecutionDetailStatus(_status)

        duration = d.pop("duration", UNSET)

        def _parse_duration_seconds(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        duration_seconds = _parse_duration_seconds(d.pop("duration_seconds", UNSET))

        start_time = d.pop("start_time", UNSET)

        transcript = d.pop("transcript", UNSET)

        scenario = d.pop("scenario", UNSET)

        overall_score = d.pop("overall_score", UNSET)

        response_time = d.pop("response_time", UNSET)

        def _parse_response_time_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        response_time_ms = _parse_response_time_ms(d.pop("response_time_ms", UNSET))

        audio_url = d.pop("audio_url", UNSET)

        customer_name = d.pop("customer_name", UNSET)

        eval_outputs = d.pop("eval_outputs", UNSET)

        eval_metrics = d.pop("eval_metrics", UNSET)

        scenario_columns = d.pop("scenario_columns", UNSET)

        def _parse_ended_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ended_reason = _parse_ended_reason(d.pop("ended_reason", UNSET))

        simulator_agent_name = d.pop("simulator_agent_name", UNSET)

        _simulator_agent_id = d.pop("simulator_agent_id", UNSET)
        simulator_agent_id: UUID | Unset
        if isinstance(_simulator_agent_id, Unset):
            simulator_agent_id = UNSET
        else:
            simulator_agent_id = UUID(_simulator_agent_id)

        agent_definition_used_name = d.pop("agent_definition_used_name", UNSET)

        _agent_definition_used_id = d.pop("agent_definition_used_id", UNSET)
        agent_definition_used_id: UUID | Unset
        if isinstance(_agent_definition_used_id, Unset):
            agent_definition_used_id = UNSET
        else:
            agent_definition_used_id = UUID(_agent_definition_used_id)

        def _parse_call_summary(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_summary = _parse_call_summary(d.pop("call_summary", UNSET))

        recordings = d.pop("recordings", UNSET)

        scenario_id = d.pop("scenario_id", UNSET)

        avg_agent_latency = d.pop("avg_agent_latency", UNSET)

        def _parse_avg_agent_latency_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        avg_agent_latency_ms = _parse_avg_agent_latency_ms(
            d.pop("avg_agent_latency_ms", UNSET)
        )

        def _parse_user_interruption_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        user_interruption_count = _parse_user_interruption_count(
            d.pop("user_interruption_count", UNSET)
        )

        def _parse_user_interruption_rate(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        user_interruption_rate = _parse_user_interruption_rate(
            d.pop("user_interruption_rate", UNSET)
        )

        def _parse_user_wpm(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        user_wpm = _parse_user_wpm(d.pop("user_wpm", UNSET))

        def _parse_bot_wpm(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        bot_wpm = _parse_bot_wpm(d.pop("bot_wpm", UNSET))

        def _parse_talk_ratio(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        talk_ratio = _parse_talk_ratio(d.pop("talk_ratio", UNSET))

        def _parse_ai_interruption_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        ai_interruption_count = _parse_ai_interruption_count(
            d.pop("ai_interruption_count", UNSET)
        )

        def _parse_ai_interruption_rate(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        ai_interruption_rate = _parse_ai_interruption_rate(
            d.pop("ai_interruption_rate", UNSET)
        )

        avg_stop_time_after_interruption = d.pop(
            "avg_stop_time_after_interruption", UNSET
        )

        total_tokens = d.pop("total_tokens", UNSET)

        input_tokens = d.pop("input_tokens", UNSET)

        output_tokens = d.pop("output_tokens", UNSET)

        avg_latency_ms = d.pop("avg_latency_ms", UNSET)

        turn_count = d.pop("turn_count", UNSET)

        agent_talk_percentage = d.pop("agent_talk_percentage", UNSET)

        csat_score = d.pop("csat_score", UNSET)

        processing_skipped = d.pop("processing_skipped", UNSET)

        processing_skip_reason = d.pop("processing_skip_reason", UNSET)

        rerun_snapshots = d.pop("rerun_snapshots", UNSET)

        is_snapshot = d.pop("is_snapshot", UNSET)

        snapshot_timestamp = d.pop("snapshot_timestamp", UNSET)

        rerun_type = d.pop("rerun_type", UNSET)

        original_call_execution_id = d.pop("original_call_execution_id", UNSET)

        _tool_outputs = d.pop("tool_outputs", UNSET)
        tool_outputs: CallExecutionDetailToolOutputs | Unset
        if isinstance(_tool_outputs, Unset):
            tool_outputs = UNSET
        else:
            tool_outputs = CallExecutionDetailToolOutputs.from_dict(_tool_outputs)

        def _parse_cost_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        cost_cents = _parse_cost_cents(d.pop("cost_cents", UNSET))

        def _parse_customer_cost_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        customer_cost_cents = _parse_customer_cost_cents(
            d.pop("customer_cost_cents", UNSET)
        )

        _customer_cost_breakdown = d.pop("customer_cost_breakdown", UNSET)
        customer_cost_breakdown: CallExecutionDetailCustomerCostBreakdown | Unset
        if isinstance(_customer_cost_breakdown, Unset):
            customer_cost_breakdown = UNSET
        else:
            customer_cost_breakdown = (
                CallExecutionDetailCustomerCostBreakdown.from_dict(
                    _customer_cost_breakdown
                )
            )

        _customer_latency_metrics = d.pop("customer_latency_metrics", UNSET)
        customer_latency_metrics: CallExecutionDetailCustomerLatencyMetrics | Unset
        if isinstance(_customer_latency_metrics, Unset):
            customer_latency_metrics = UNSET
        else:
            customer_latency_metrics = (
                CallExecutionDetailCustomerLatencyMetrics.from_dict(
                    _customer_latency_metrics
                )
            )

        def _parse_customer_call_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        customer_call_id = _parse_customer_call_id(d.pop("customer_call_id", UNSET))

        _simulation_call_type = d.pop("simulation_call_type", UNSET)
        simulation_call_type: CallExecutionDetailSimulationCallType | Unset
        if isinstance(_simulation_call_type, Unset):
            simulation_call_type = UNSET
        else:
            simulation_call_type = CallExecutionDetailSimulationCallType(
                _simulation_call_type
            )

        provider = d.pop("provider", UNSET)

        def _parse_phone_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone_number = _parse_phone_number(d.pop("phone_number", UNSET))

        call_execution_detail = cls(
            id=id,
            service_provider_call_id=service_provider_call_id,
            session_id=session_id,
            timestamp=timestamp,
            call_type=call_type,
            status=status,
            duration=duration,
            duration_seconds=duration_seconds,
            start_time=start_time,
            transcript=transcript,
            scenario=scenario,
            overall_score=overall_score,
            response_time=response_time,
            response_time_ms=response_time_ms,
            audio_url=audio_url,
            customer_name=customer_name,
            eval_outputs=eval_outputs,
            eval_metrics=eval_metrics,
            scenario_columns=scenario_columns,
            ended_reason=ended_reason,
            simulator_agent_name=simulator_agent_name,
            simulator_agent_id=simulator_agent_id,
            agent_definition_used_name=agent_definition_used_name,
            agent_definition_used_id=agent_definition_used_id,
            call_summary=call_summary,
            recordings=recordings,
            scenario_id=scenario_id,
            avg_agent_latency=avg_agent_latency,
            avg_agent_latency_ms=avg_agent_latency_ms,
            user_interruption_count=user_interruption_count,
            user_interruption_rate=user_interruption_rate,
            user_wpm=user_wpm,
            bot_wpm=bot_wpm,
            talk_ratio=talk_ratio,
            ai_interruption_count=ai_interruption_count,
            ai_interruption_rate=ai_interruption_rate,
            avg_stop_time_after_interruption=avg_stop_time_after_interruption,
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            avg_latency_ms=avg_latency_ms,
            turn_count=turn_count,
            agent_talk_percentage=agent_talk_percentage,
            csat_score=csat_score,
            processing_skipped=processing_skipped,
            processing_skip_reason=processing_skip_reason,
            rerun_snapshots=rerun_snapshots,
            is_snapshot=is_snapshot,
            snapshot_timestamp=snapshot_timestamp,
            rerun_type=rerun_type,
            original_call_execution_id=original_call_execution_id,
            tool_outputs=tool_outputs,
            cost_cents=cost_cents,
            customer_cost_cents=customer_cost_cents,
            customer_cost_breakdown=customer_cost_breakdown,
            customer_latency_metrics=customer_latency_metrics,
            customer_call_id=customer_call_id,
            simulation_call_type=simulation_call_type,
            provider=provider,
            phone_number=phone_number,
        )

        call_execution_detail.additional_properties = d
        return call_execution_detail

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
