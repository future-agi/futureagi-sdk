from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_voice_call_detail_result_analysis_data import (
        TraceVoiceCallDetailResultAnalysisData,
    )
    from ..models.trace_voice_call_detail_result_call_metadata import (
        TraceVoiceCallDetailResultCallMetadata,
    )
    from ..models.trace_voice_call_detail_result_cost_breakdown import (
        TraceVoiceCallDetailResultCostBreakdown,
    )
    from ..models.trace_voice_call_detail_result_eval_outputs import (
        TraceVoiceCallDetailResultEvalOutputs,
    )
    from ..models.trace_voice_call_detail_result_eval_rollup import (
        TraceVoiceCallDetailResultEvalRollup,
    )
    from ..models.trace_voice_call_detail_result_evaluation_data import (
        TraceVoiceCallDetailResultEvaluationData,
    )
    from ..models.trace_voice_call_detail_result_messages_type_0_item import (
        TraceVoiceCallDetailResultMessagesType0Item,
    )
    from ..models.trace_voice_call_detail_result_observation_span_item import (
        TraceVoiceCallDetailResultObservationSpanItem,
    )
    from ..models.trace_voice_call_detail_result_recording import (
        TraceVoiceCallDetailResultRecording,
    )
    from ..models.trace_voice_call_detail_result_scenario_graph import (
        TraceVoiceCallDetailResultScenarioGraph,
    )
    from ..models.trace_voice_call_detail_result_transcript_type_0_item import (
        TraceVoiceCallDetailResultTranscriptType0Item,
    )


T = TypeVar("T", bound="TraceVoiceCallDetailResult")


@_attrs_define
class TraceVoiceCallDetailResult:
    """
    Attributes:
        id (str):
        trace_id (str):
        project_id (str):
        provider_call_id (None | str):
        recording (TraceVoiceCallDetailResultRecording):
        recording_available (bool):
        call_metadata (TraceVoiceCallDetailResultCallMetadata):
        observation_span (list[TraceVoiceCallDetailResultObservationSpanItem]):
        eval_outputs (TraceVoiceCallDetailResultEvalOutputs):
        turn_count (int | None):
        talk_ratio (float | None):
        agent_talk_percentage (float | None):
        bot_talk_pct (int | None):
        user_talk_pct (int | None):
        avg_agent_latency_ms (int | None):
        user_wpm (int | None):
        bot_wpm (int | None):
        user_interruption_count (int | None):
        ai_interruption_count (int | None):
        phone_number (None | str | Unset):
        customer_name (None | str | Unset):
        call_id (None | str | Unset):
        status (None | str | Unset):
        started_at (None | str | Unset):
        ended_at (None | str | Unset):
        created_at (None | str | Unset):
        duration_seconds (int | None | Unset):
        recording_url (None | str | Unset):
        stereo_recording_url (None | str | Unset):
        cost_cents (float | None | Unset):
        cost_breakdown (TraceVoiceCallDetailResultCostBreakdown | Unset):
        error_message (None | str | Unset):
        call_summary (None | str | Unset):
        ended_reason (None | str | Unset):
        overall_score (float | None | Unset):
        response_time_ms (float | None | Unset):
        response_time_seconds (float | None | Unset):
        assistant_id (None | str | Unset):
        assistant_phone_number (None | str | Unset):
        call_type (None | str | Unset):
        message_count (int | None | Unset):
        transcript_available (bool | None | Unset):
        transcript (list[TraceVoiceCallDetailResultTranscriptType0Item] | None | Unset):
        messages (list[TraceVoiceCallDetailResultMessagesType0Item] | None | Unset):
        analysis_data (TraceVoiceCallDetailResultAnalysisData | Unset):
        evaluation_data (TraceVoiceCallDetailResultEvaluationData | Unset):
        eval_rollup (TraceVoiceCallDetailResultEvalRollup | Unset):
        call_execution_id (None | str | Unset):
        test_execution_id (None | str | Unset):
        scenario_id (None | str | Unset):
        scenario_name (None | str | Unset):
        scenario_graph_id (None | str | Unset):
        scenario_graph (TraceVoiceCallDetailResultScenarioGraph | Unset):
    """

    id: str
    trace_id: str
    project_id: str
    provider_call_id: None | str
    recording: TraceVoiceCallDetailResultRecording
    recording_available: bool
    call_metadata: TraceVoiceCallDetailResultCallMetadata
    observation_span: list[TraceVoiceCallDetailResultObservationSpanItem]
    eval_outputs: TraceVoiceCallDetailResultEvalOutputs
    turn_count: int | None
    talk_ratio: float | None
    agent_talk_percentage: float | None
    bot_talk_pct: int | None
    user_talk_pct: int | None
    avg_agent_latency_ms: int | None
    user_wpm: int | None
    bot_wpm: int | None
    user_interruption_count: int | None
    ai_interruption_count: int | None
    phone_number: None | str | Unset = UNSET
    customer_name: None | str | Unset = UNSET
    call_id: None | str | Unset = UNSET
    status: None | str | Unset = UNSET
    started_at: None | str | Unset = UNSET
    ended_at: None | str | Unset = UNSET
    created_at: None | str | Unset = UNSET
    duration_seconds: int | None | Unset = UNSET
    recording_url: None | str | Unset = UNSET
    stereo_recording_url: None | str | Unset = UNSET
    cost_cents: float | None | Unset = UNSET
    cost_breakdown: TraceVoiceCallDetailResultCostBreakdown | Unset = UNSET
    error_message: None | str | Unset = UNSET
    call_summary: None | str | Unset = UNSET
    ended_reason: None | str | Unset = UNSET
    overall_score: float | None | Unset = UNSET
    response_time_ms: float | None | Unset = UNSET
    response_time_seconds: float | None | Unset = UNSET
    assistant_id: None | str | Unset = UNSET
    assistant_phone_number: None | str | Unset = UNSET
    call_type: None | str | Unset = UNSET
    message_count: int | None | Unset = UNSET
    transcript_available: bool | None | Unset = UNSET
    transcript: list[TraceVoiceCallDetailResultTranscriptType0Item] | None | Unset = (
        UNSET
    )
    messages: list[TraceVoiceCallDetailResultMessagesType0Item] | None | Unset = UNSET
    analysis_data: TraceVoiceCallDetailResultAnalysisData | Unset = UNSET
    evaluation_data: TraceVoiceCallDetailResultEvaluationData | Unset = UNSET
    eval_rollup: TraceVoiceCallDetailResultEvalRollup | Unset = UNSET
    call_execution_id: None | str | Unset = UNSET
    test_execution_id: None | str | Unset = UNSET
    scenario_id: None | str | Unset = UNSET
    scenario_name: None | str | Unset = UNSET
    scenario_graph_id: None | str | Unset = UNSET
    scenario_graph: TraceVoiceCallDetailResultScenarioGraph | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        trace_id = self.trace_id

        project_id = self.project_id

        provider_call_id: None | str
        provider_call_id = self.provider_call_id

        recording = self.recording.to_dict()

        recording_available = self.recording_available

        call_metadata = self.call_metadata.to_dict()

        observation_span = []
        for observation_span_item_data in self.observation_span:
            observation_span_item = observation_span_item_data.to_dict()
            observation_span.append(observation_span_item)

        eval_outputs = self.eval_outputs.to_dict()

        turn_count: int | None
        turn_count = self.turn_count

        talk_ratio: float | None
        talk_ratio = self.talk_ratio

        agent_talk_percentage: float | None
        agent_talk_percentage = self.agent_talk_percentage

        bot_talk_pct: int | None
        bot_talk_pct = self.bot_talk_pct

        user_talk_pct: int | None
        user_talk_pct = self.user_talk_pct

        avg_agent_latency_ms: int | None
        avg_agent_latency_ms = self.avg_agent_latency_ms

        user_wpm: int | None
        user_wpm = self.user_wpm

        bot_wpm: int | None
        bot_wpm = self.bot_wpm

        user_interruption_count: int | None
        user_interruption_count = self.user_interruption_count

        ai_interruption_count: int | None
        ai_interruption_count = self.ai_interruption_count

        phone_number: None | str | Unset
        if isinstance(self.phone_number, Unset):
            phone_number = UNSET
        else:
            phone_number = self.phone_number

        customer_name: None | str | Unset
        if isinstance(self.customer_name, Unset):
            customer_name = UNSET
        else:
            customer_name = self.customer_name

        call_id: None | str | Unset
        if isinstance(self.call_id, Unset):
            call_id = UNSET
        else:
            call_id = self.call_id

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        started_at: None | str | Unset
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        else:
            started_at = self.started_at

        ended_at: None | str | Unset
        if isinstance(self.ended_at, Unset):
            ended_at = UNSET
        else:
            ended_at = self.ended_at

        created_at: None | str | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        duration_seconds: int | None | Unset
        if isinstance(self.duration_seconds, Unset):
            duration_seconds = UNSET
        else:
            duration_seconds = self.duration_seconds

        recording_url: None | str | Unset
        if isinstance(self.recording_url, Unset):
            recording_url = UNSET
        else:
            recording_url = self.recording_url

        stereo_recording_url: None | str | Unset
        if isinstance(self.stereo_recording_url, Unset):
            stereo_recording_url = UNSET
        else:
            stereo_recording_url = self.stereo_recording_url

        cost_cents: float | None | Unset
        if isinstance(self.cost_cents, Unset):
            cost_cents = UNSET
        else:
            cost_cents = self.cost_cents

        cost_breakdown: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cost_breakdown, Unset):
            cost_breakdown = self.cost_breakdown.to_dict()

        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        call_summary: None | str | Unset
        if isinstance(self.call_summary, Unset):
            call_summary = UNSET
        else:
            call_summary = self.call_summary

        ended_reason: None | str | Unset
        if isinstance(self.ended_reason, Unset):
            ended_reason = UNSET
        else:
            ended_reason = self.ended_reason

        overall_score: float | None | Unset
        if isinstance(self.overall_score, Unset):
            overall_score = UNSET
        else:
            overall_score = self.overall_score

        response_time_ms: float | None | Unset
        if isinstance(self.response_time_ms, Unset):
            response_time_ms = UNSET
        else:
            response_time_ms = self.response_time_ms

        response_time_seconds: float | None | Unset
        if isinstance(self.response_time_seconds, Unset):
            response_time_seconds = UNSET
        else:
            response_time_seconds = self.response_time_seconds

        assistant_id: None | str | Unset
        if isinstance(self.assistant_id, Unset):
            assistant_id = UNSET
        else:
            assistant_id = self.assistant_id

        assistant_phone_number: None | str | Unset
        if isinstance(self.assistant_phone_number, Unset):
            assistant_phone_number = UNSET
        else:
            assistant_phone_number = self.assistant_phone_number

        call_type: None | str | Unset
        if isinstance(self.call_type, Unset):
            call_type = UNSET
        else:
            call_type = self.call_type

        message_count: int | None | Unset
        if isinstance(self.message_count, Unset):
            message_count = UNSET
        else:
            message_count = self.message_count

        transcript_available: bool | None | Unset
        if isinstance(self.transcript_available, Unset):
            transcript_available = UNSET
        else:
            transcript_available = self.transcript_available

        transcript: list[dict[str, Any]] | None | Unset
        if isinstance(self.transcript, Unset):
            transcript = UNSET
        elif isinstance(self.transcript, list):
            transcript = []
            for transcript_type_0_item_data in self.transcript:
                transcript_type_0_item = transcript_type_0_item_data.to_dict()
                transcript.append(transcript_type_0_item)

        else:
            transcript = self.transcript

        messages: list[dict[str, Any]] | None | Unset
        if isinstance(self.messages, Unset):
            messages = UNSET
        elif isinstance(self.messages, list):
            messages = []
            for messages_type_0_item_data in self.messages:
                messages_type_0_item = messages_type_0_item_data.to_dict()
                messages.append(messages_type_0_item)

        else:
            messages = self.messages

        analysis_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.analysis_data, Unset):
            analysis_data = self.analysis_data.to_dict()

        evaluation_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.evaluation_data, Unset):
            evaluation_data = self.evaluation_data.to_dict()

        eval_rollup: dict[str, Any] | Unset = UNSET
        if not isinstance(self.eval_rollup, Unset):
            eval_rollup = self.eval_rollup.to_dict()

        call_execution_id: None | str | Unset
        if isinstance(self.call_execution_id, Unset):
            call_execution_id = UNSET
        else:
            call_execution_id = self.call_execution_id

        test_execution_id: None | str | Unset
        if isinstance(self.test_execution_id, Unset):
            test_execution_id = UNSET
        else:
            test_execution_id = self.test_execution_id

        scenario_id: None | str | Unset
        if isinstance(self.scenario_id, Unset):
            scenario_id = UNSET
        else:
            scenario_id = self.scenario_id

        scenario_name: None | str | Unset
        if isinstance(self.scenario_name, Unset):
            scenario_name = UNSET
        else:
            scenario_name = self.scenario_name

        scenario_graph_id: None | str | Unset
        if isinstance(self.scenario_graph_id, Unset):
            scenario_graph_id = UNSET
        else:
            scenario_graph_id = self.scenario_graph_id

        scenario_graph: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scenario_graph, Unset):
            scenario_graph = self.scenario_graph.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "trace_id": trace_id,
                "project_id": project_id,
                "provider_call_id": provider_call_id,
                "recording": recording,
                "recording_available": recording_available,
                "call_metadata": call_metadata,
                "observation_span": observation_span,
                "eval_outputs": eval_outputs,
                "turn_count": turn_count,
                "talk_ratio": talk_ratio,
                "agent_talk_percentage": agent_talk_percentage,
                "bot_talk_pct": bot_talk_pct,
                "user_talk_pct": user_talk_pct,
                "avg_agent_latency_ms": avg_agent_latency_ms,
                "user_wpm": user_wpm,
                "bot_wpm": bot_wpm,
                "user_interruption_count": user_interruption_count,
                "ai_interruption_count": ai_interruption_count,
            }
        )
        if phone_number is not UNSET:
            field_dict["phone_number"] = phone_number
        if customer_name is not UNSET:
            field_dict["customer_name"] = customer_name
        if call_id is not UNSET:
            field_dict["call_id"] = call_id
        if status is not UNSET:
            field_dict["status"] = status
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if duration_seconds is not UNSET:
            field_dict["duration_seconds"] = duration_seconds
        if recording_url is not UNSET:
            field_dict["recording_url"] = recording_url
        if stereo_recording_url is not UNSET:
            field_dict["stereo_recording_url"] = stereo_recording_url
        if cost_cents is not UNSET:
            field_dict["cost_cents"] = cost_cents
        if cost_breakdown is not UNSET:
            field_dict["cost_breakdown"] = cost_breakdown
        if error_message is not UNSET:
            field_dict["error_message"] = error_message
        if call_summary is not UNSET:
            field_dict["call_summary"] = call_summary
        if ended_reason is not UNSET:
            field_dict["ended_reason"] = ended_reason
        if overall_score is not UNSET:
            field_dict["overall_score"] = overall_score
        if response_time_ms is not UNSET:
            field_dict["response_time_ms"] = response_time_ms
        if response_time_seconds is not UNSET:
            field_dict["response_time_seconds"] = response_time_seconds
        if assistant_id is not UNSET:
            field_dict["assistant_id"] = assistant_id
        if assistant_phone_number is not UNSET:
            field_dict["assistant_phone_number"] = assistant_phone_number
        if call_type is not UNSET:
            field_dict["call_type"] = call_type
        if message_count is not UNSET:
            field_dict["message_count"] = message_count
        if transcript_available is not UNSET:
            field_dict["transcript_available"] = transcript_available
        if transcript is not UNSET:
            field_dict["transcript"] = transcript
        if messages is not UNSET:
            field_dict["messages"] = messages
        if analysis_data is not UNSET:
            field_dict["analysis_data"] = analysis_data
        if evaluation_data is not UNSET:
            field_dict["evaluation_data"] = evaluation_data
        if eval_rollup is not UNSET:
            field_dict["eval_rollup"] = eval_rollup
        if call_execution_id is not UNSET:
            field_dict["call_execution_id"] = call_execution_id
        if test_execution_id is not UNSET:
            field_dict["test_execution_id"] = test_execution_id
        if scenario_id is not UNSET:
            field_dict["scenario_id"] = scenario_id
        if scenario_name is not UNSET:
            field_dict["scenario_name"] = scenario_name
        if scenario_graph_id is not UNSET:
            field_dict["scenario_graph_id"] = scenario_graph_id
        if scenario_graph is not UNSET:
            field_dict["scenario_graph"] = scenario_graph

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_voice_call_detail_result_analysis_data import (
            TraceVoiceCallDetailResultAnalysisData,
        )
        from ..models.trace_voice_call_detail_result_call_metadata import (
            TraceVoiceCallDetailResultCallMetadata,
        )
        from ..models.trace_voice_call_detail_result_cost_breakdown import (
            TraceVoiceCallDetailResultCostBreakdown,
        )
        from ..models.trace_voice_call_detail_result_eval_outputs import (
            TraceVoiceCallDetailResultEvalOutputs,
        )
        from ..models.trace_voice_call_detail_result_eval_rollup import (
            TraceVoiceCallDetailResultEvalRollup,
        )
        from ..models.trace_voice_call_detail_result_evaluation_data import (
            TraceVoiceCallDetailResultEvaluationData,
        )
        from ..models.trace_voice_call_detail_result_messages_type_0_item import (
            TraceVoiceCallDetailResultMessagesType0Item,
        )
        from ..models.trace_voice_call_detail_result_observation_span_item import (
            TraceVoiceCallDetailResultObservationSpanItem,
        )
        from ..models.trace_voice_call_detail_result_recording import (
            TraceVoiceCallDetailResultRecording,
        )
        from ..models.trace_voice_call_detail_result_scenario_graph import (
            TraceVoiceCallDetailResultScenarioGraph,
        )
        from ..models.trace_voice_call_detail_result_transcript_type_0_item import (
            TraceVoiceCallDetailResultTranscriptType0Item,
        )

        d = dict(src_dict)
        id = d.pop("id")

        trace_id = d.pop("trace_id")

        project_id = d.pop("project_id")

        def _parse_provider_call_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        provider_call_id = _parse_provider_call_id(d.pop("provider_call_id"))

        recording = TraceVoiceCallDetailResultRecording.from_dict(d.pop("recording"))

        recording_available = d.pop("recording_available")

        call_metadata = TraceVoiceCallDetailResultCallMetadata.from_dict(
            d.pop("call_metadata")
        )

        observation_span = []
        _observation_span = d.pop("observation_span")
        for observation_span_item_data in _observation_span:
            observation_span_item = (
                TraceVoiceCallDetailResultObservationSpanItem.from_dict(
                    observation_span_item_data
                )
            )

            observation_span.append(observation_span_item)

        eval_outputs = TraceVoiceCallDetailResultEvalOutputs.from_dict(
            d.pop("eval_outputs")
        )

        def _parse_turn_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        turn_count = _parse_turn_count(d.pop("turn_count"))

        def _parse_talk_ratio(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        talk_ratio = _parse_talk_ratio(d.pop("talk_ratio"))

        def _parse_agent_talk_percentage(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        agent_talk_percentage = _parse_agent_talk_percentage(
            d.pop("agent_talk_percentage")
        )

        def _parse_bot_talk_pct(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        bot_talk_pct = _parse_bot_talk_pct(d.pop("bot_talk_pct"))

        def _parse_user_talk_pct(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        user_talk_pct = _parse_user_talk_pct(d.pop("user_talk_pct"))

        def _parse_avg_agent_latency_ms(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        avg_agent_latency_ms = _parse_avg_agent_latency_ms(
            d.pop("avg_agent_latency_ms")
        )

        def _parse_user_wpm(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        user_wpm = _parse_user_wpm(d.pop("user_wpm"))

        def _parse_bot_wpm(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        bot_wpm = _parse_bot_wpm(d.pop("bot_wpm"))

        def _parse_user_interruption_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        user_interruption_count = _parse_user_interruption_count(
            d.pop("user_interruption_count")
        )

        def _parse_ai_interruption_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        ai_interruption_count = _parse_ai_interruption_count(
            d.pop("ai_interruption_count")
        )

        def _parse_phone_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone_number = _parse_phone_number(d.pop("phone_number", UNSET))

        def _parse_customer_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        customer_name = _parse_customer_name(d.pop("customer_name", UNSET))

        def _parse_call_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_id = _parse_call_id(d.pop("call_id", UNSET))

        def _parse_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_started_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_ended_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ended_at = _parse_ended_at(d.pop("ended_at", UNSET))

        def _parse_created_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_duration_seconds(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        duration_seconds = _parse_duration_seconds(d.pop("duration_seconds", UNSET))

        def _parse_recording_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        recording_url = _parse_recording_url(d.pop("recording_url", UNSET))

        def _parse_stereo_recording_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stereo_recording_url = _parse_stereo_recording_url(
            d.pop("stereo_recording_url", UNSET)
        )

        def _parse_cost_cents(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        cost_cents = _parse_cost_cents(d.pop("cost_cents", UNSET))

        _cost_breakdown = d.pop("cost_breakdown", UNSET)
        cost_breakdown: TraceVoiceCallDetailResultCostBreakdown | Unset
        if isinstance(_cost_breakdown, Unset):
            cost_breakdown = UNSET
        else:
            cost_breakdown = TraceVoiceCallDetailResultCostBreakdown.from_dict(
                _cost_breakdown
            )

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        def _parse_call_summary(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_summary = _parse_call_summary(d.pop("call_summary", UNSET))

        def _parse_ended_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ended_reason = _parse_ended_reason(d.pop("ended_reason", UNSET))

        def _parse_overall_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        overall_score = _parse_overall_score(d.pop("overall_score", UNSET))

        def _parse_response_time_ms(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        response_time_ms = _parse_response_time_ms(d.pop("response_time_ms", UNSET))

        def _parse_response_time_seconds(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        response_time_seconds = _parse_response_time_seconds(
            d.pop("response_time_seconds", UNSET)
        )

        def _parse_assistant_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        assistant_id = _parse_assistant_id(d.pop("assistant_id", UNSET))

        def _parse_assistant_phone_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        assistant_phone_number = _parse_assistant_phone_number(
            d.pop("assistant_phone_number", UNSET)
        )

        def _parse_call_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_type = _parse_call_type(d.pop("call_type", UNSET))

        def _parse_message_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        message_count = _parse_message_count(d.pop("message_count", UNSET))

        def _parse_transcript_available(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        transcript_available = _parse_transcript_available(
            d.pop("transcript_available", UNSET)
        )

        def _parse_transcript(
            data: object,
        ) -> list[TraceVoiceCallDetailResultTranscriptType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                transcript_type_0 = []
                _transcript_type_0 = data
                for transcript_type_0_item_data in _transcript_type_0:
                    transcript_type_0_item = (
                        TraceVoiceCallDetailResultTranscriptType0Item.from_dict(
                            transcript_type_0_item_data
                        )
                    )

                    transcript_type_0.append(transcript_type_0_item)

                return transcript_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[TraceVoiceCallDetailResultTranscriptType0Item] | None | Unset, data
            )

        transcript = _parse_transcript(d.pop("transcript", UNSET))

        def _parse_messages(
            data: object,
        ) -> list[TraceVoiceCallDetailResultMessagesType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                messages_type_0 = []
                _messages_type_0 = data
                for messages_type_0_item_data in _messages_type_0:
                    messages_type_0_item = (
                        TraceVoiceCallDetailResultMessagesType0Item.from_dict(
                            messages_type_0_item_data
                        )
                    )

                    messages_type_0.append(messages_type_0_item)

                return messages_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[TraceVoiceCallDetailResultMessagesType0Item] | None | Unset, data
            )

        messages = _parse_messages(d.pop("messages", UNSET))

        _analysis_data = d.pop("analysis_data", UNSET)
        analysis_data: TraceVoiceCallDetailResultAnalysisData | Unset
        if isinstance(_analysis_data, Unset):
            analysis_data = UNSET
        else:
            analysis_data = TraceVoiceCallDetailResultAnalysisData.from_dict(
                _analysis_data
            )

        _evaluation_data = d.pop("evaluation_data", UNSET)
        evaluation_data: TraceVoiceCallDetailResultEvaluationData | Unset
        if isinstance(_evaluation_data, Unset):
            evaluation_data = UNSET
        else:
            evaluation_data = TraceVoiceCallDetailResultEvaluationData.from_dict(
                _evaluation_data
            )

        _eval_rollup = d.pop("eval_rollup", UNSET)
        eval_rollup: TraceVoiceCallDetailResultEvalRollup | Unset
        if isinstance(_eval_rollup, Unset):
            eval_rollup = UNSET
        else:
            eval_rollup = TraceVoiceCallDetailResultEvalRollup.from_dict(_eval_rollup)

        def _parse_call_execution_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_execution_id = _parse_call_execution_id(d.pop("call_execution_id", UNSET))

        def _parse_test_execution_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        test_execution_id = _parse_test_execution_id(d.pop("test_execution_id", UNSET))

        def _parse_scenario_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        scenario_id = _parse_scenario_id(d.pop("scenario_id", UNSET))

        def _parse_scenario_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        scenario_name = _parse_scenario_name(d.pop("scenario_name", UNSET))

        def _parse_scenario_graph_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        scenario_graph_id = _parse_scenario_graph_id(d.pop("scenario_graph_id", UNSET))

        _scenario_graph = d.pop("scenario_graph", UNSET)
        scenario_graph: TraceVoiceCallDetailResultScenarioGraph | Unset
        if isinstance(_scenario_graph, Unset):
            scenario_graph = UNSET
        else:
            scenario_graph = TraceVoiceCallDetailResultScenarioGraph.from_dict(
                _scenario_graph
            )

        trace_voice_call_detail_result = cls(
            id=id,
            trace_id=trace_id,
            project_id=project_id,
            provider_call_id=provider_call_id,
            recording=recording,
            recording_available=recording_available,
            call_metadata=call_metadata,
            observation_span=observation_span,
            eval_outputs=eval_outputs,
            turn_count=turn_count,
            talk_ratio=talk_ratio,
            agent_talk_percentage=agent_talk_percentage,
            bot_talk_pct=bot_talk_pct,
            user_talk_pct=user_talk_pct,
            avg_agent_latency_ms=avg_agent_latency_ms,
            user_wpm=user_wpm,
            bot_wpm=bot_wpm,
            user_interruption_count=user_interruption_count,
            ai_interruption_count=ai_interruption_count,
            phone_number=phone_number,
            customer_name=customer_name,
            call_id=call_id,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            created_at=created_at,
            duration_seconds=duration_seconds,
            recording_url=recording_url,
            stereo_recording_url=stereo_recording_url,
            cost_cents=cost_cents,
            cost_breakdown=cost_breakdown,
            error_message=error_message,
            call_summary=call_summary,
            ended_reason=ended_reason,
            overall_score=overall_score,
            response_time_ms=response_time_ms,
            response_time_seconds=response_time_seconds,
            assistant_id=assistant_id,
            assistant_phone_number=assistant_phone_number,
            call_type=call_type,
            message_count=message_count,
            transcript_available=transcript_available,
            transcript=transcript,
            messages=messages,
            analysis_data=analysis_data,
            evaluation_data=evaluation_data,
            eval_rollup=eval_rollup,
            call_execution_id=call_execution_id,
            test_execution_id=test_execution_id,
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            scenario_graph_id=scenario_graph_id,
            scenario_graph=scenario_graph,
        )

        trace_voice_call_detail_result.additional_properties = d
        return trace_voice_call_detail_result

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
