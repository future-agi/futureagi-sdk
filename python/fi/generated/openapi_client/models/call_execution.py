from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.call_execution_simulation_call_type import CallExecutionSimulationCallType
from ..models.call_execution_status import CallExecutionStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.call_execution_analysis_data import CallExecutionAnalysisData
    from ..models.call_execution_call_metadata import CallExecutionCallMetadata
    from ..models.call_execution_eval_outputs import CallExecutionEvalOutputs
    from ..models.call_execution_evaluation_data import CallExecutionEvaluationData
    from ..models.call_execution_provider_call_data import CallExecutionProviderCallData


T = TypeVar("T", bound="CallExecution")


@_attrs_define
class CallExecution:
    """
    Attributes:
        id (UUID | Unset):
        phone_number (None | str | Unset): Phone number called (null for TEXT/chat simulations)
        service_provider_call_id (str | Unset):
        status (CallExecutionStatus | Unset): Current status of the call
        started_at (datetime.datetime | None | Unset): When the call started
        completed_at (datetime.datetime | None | Unset): When the call completed
        duration_seconds (int | None | Unset): Duration of the call in seconds
        recording_url (None | str | Unset): URL to the call recording
        cost_cents (int | None | Unset): Cost of the call in cents
        call_metadata (CallExecutionCallMetadata | Unset): Additional metadata about the call
        error_message (None | str | Unset): Error message if the call failed
        scenario_name (str | Unset):
        transcripts (str | Unset):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        provider_call_data (CallExecutionProviderCallData | Unset): Complete call data from the provider. Format:
            dict[provider_name, data] where provider_name must be from SupportedProviders
        stereo_recording_url (None | str | Unset): Stereo recording URL from Vapi
        ended_reason (None | str | Unset): Reason why the call ended
        stt_cost_cents (int | None | Unset): STT cost in cents
        llm_cost_cents (int | None | Unset): LLM cost in cents
        tts_cost_cents (int | None | Unset): TTS cost in cents
        overall_score (float | None | Unset): Overall call performance score
        response_time_ms (int | None | Unset): Average response time in milliseconds
        response_time_seconds (str | Unset):
        assistant_id (None | str | Unset): Assistant ID used for the call (system side)
        customer_number (None | str | Unset): Customer phone number (E.164 format)
        call_type (None | str | Unset): Type of call (e.g., outboundPhoneCall)
        ended_at (datetime.datetime | None | Unset): When the call ended
        analysis_data (CallExecutionAnalysisData | Unset): Call analysis data from the service provider
        evaluation_data (CallExecutionEvaluationData | Unset): Call evaluation data from the service provider
        message_count (int | None | Unset): Number of messages in the call
        transcript_available (bool | Unset): Whether transcript is available
        recording_available (bool | Unset): Whether recording is available
        eval_outputs (CallExecutionEvalOutputs | Unset): Evaluation output
        error_localizer_tasks (str | Unset):
        call_summary (None | str | Unset): Call summary from the service
        agent_version (None | Unset | UUID):
        customer_cost_cents (int | None | Unset): Total customer-reported cost in cents
        system_metrics (str | Unset):
        cost_breakdown (str | Unset):
        customer_call_id (None | str | Unset): Customer call ID if available
        simulation_call_type (CallExecutionSimulationCallType | Unset): Type of simulation call
        processing_skipped (str | Unset):
        processing_skip_reason (str | Unset):
    """

    id: UUID | Unset = UNSET
    phone_number: None | str | Unset = UNSET
    service_provider_call_id: str | Unset = UNSET
    status: CallExecutionStatus | Unset = UNSET
    started_at: datetime.datetime | None | Unset = UNSET
    completed_at: datetime.datetime | None | Unset = UNSET
    duration_seconds: int | None | Unset = UNSET
    recording_url: None | str | Unset = UNSET
    cost_cents: int | None | Unset = UNSET
    call_metadata: CallExecutionCallMetadata | Unset = UNSET
    error_message: None | str | Unset = UNSET
    scenario_name: str | Unset = UNSET
    transcripts: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    provider_call_data: CallExecutionProviderCallData | Unset = UNSET
    stereo_recording_url: None | str | Unset = UNSET
    ended_reason: None | str | Unset = UNSET
    stt_cost_cents: int | None | Unset = UNSET
    llm_cost_cents: int | None | Unset = UNSET
    tts_cost_cents: int | None | Unset = UNSET
    overall_score: float | None | Unset = UNSET
    response_time_ms: int | None | Unset = UNSET
    response_time_seconds: str | Unset = UNSET
    assistant_id: None | str | Unset = UNSET
    customer_number: None | str | Unset = UNSET
    call_type: None | str | Unset = UNSET
    ended_at: datetime.datetime | None | Unset = UNSET
    analysis_data: CallExecutionAnalysisData | Unset = UNSET
    evaluation_data: CallExecutionEvaluationData | Unset = UNSET
    message_count: int | None | Unset = UNSET
    transcript_available: bool | Unset = UNSET
    recording_available: bool | Unset = UNSET
    eval_outputs: CallExecutionEvalOutputs | Unset = UNSET
    error_localizer_tasks: str | Unset = UNSET
    call_summary: None | str | Unset = UNSET
    agent_version: None | Unset | UUID = UNSET
    customer_cost_cents: int | None | Unset = UNSET
    system_metrics: str | Unset = UNSET
    cost_breakdown: str | Unset = UNSET
    customer_call_id: None | str | Unset = UNSET
    simulation_call_type: CallExecutionSimulationCallType | Unset = UNSET
    processing_skipped: str | Unset = UNSET
    processing_skip_reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        phone_number: None | str | Unset
        if isinstance(self.phone_number, Unset):
            phone_number = UNSET
        else:
            phone_number = self.phone_number

        service_provider_call_id = self.service_provider_call_id

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        started_at: None | str | Unset
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        elif isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        completed_at: None | str | Unset
        if isinstance(self.completed_at, Unset):
            completed_at = UNSET
        elif isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

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

        cost_cents: int | None | Unset
        if isinstance(self.cost_cents, Unset):
            cost_cents = UNSET
        else:
            cost_cents = self.cost_cents

        call_metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.call_metadata, Unset):
            call_metadata = self.call_metadata.to_dict()

        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        scenario_name = self.scenario_name

        transcripts = self.transcripts

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        provider_call_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.provider_call_data, Unset):
            provider_call_data = self.provider_call_data.to_dict()

        stereo_recording_url: None | str | Unset
        if isinstance(self.stereo_recording_url, Unset):
            stereo_recording_url = UNSET
        else:
            stereo_recording_url = self.stereo_recording_url

        ended_reason: None | str | Unset
        if isinstance(self.ended_reason, Unset):
            ended_reason = UNSET
        else:
            ended_reason = self.ended_reason

        stt_cost_cents: int | None | Unset
        if isinstance(self.stt_cost_cents, Unset):
            stt_cost_cents = UNSET
        else:
            stt_cost_cents = self.stt_cost_cents

        llm_cost_cents: int | None | Unset
        if isinstance(self.llm_cost_cents, Unset):
            llm_cost_cents = UNSET
        else:
            llm_cost_cents = self.llm_cost_cents

        tts_cost_cents: int | None | Unset
        if isinstance(self.tts_cost_cents, Unset):
            tts_cost_cents = UNSET
        else:
            tts_cost_cents = self.tts_cost_cents

        overall_score: float | None | Unset
        if isinstance(self.overall_score, Unset):
            overall_score = UNSET
        else:
            overall_score = self.overall_score

        response_time_ms: int | None | Unset
        if isinstance(self.response_time_ms, Unset):
            response_time_ms = UNSET
        else:
            response_time_ms = self.response_time_ms

        response_time_seconds = self.response_time_seconds

        assistant_id: None | str | Unset
        if isinstance(self.assistant_id, Unset):
            assistant_id = UNSET
        else:
            assistant_id = self.assistant_id

        customer_number: None | str | Unset
        if isinstance(self.customer_number, Unset):
            customer_number = UNSET
        else:
            customer_number = self.customer_number

        call_type: None | str | Unset
        if isinstance(self.call_type, Unset):
            call_type = UNSET
        else:
            call_type = self.call_type

        ended_at: None | str | Unset
        if isinstance(self.ended_at, Unset):
            ended_at = UNSET
        elif isinstance(self.ended_at, datetime.datetime):
            ended_at = self.ended_at.isoformat()
        else:
            ended_at = self.ended_at

        analysis_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.analysis_data, Unset):
            analysis_data = self.analysis_data.to_dict()

        evaluation_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.evaluation_data, Unset):
            evaluation_data = self.evaluation_data.to_dict()

        message_count: int | None | Unset
        if isinstance(self.message_count, Unset):
            message_count = UNSET
        else:
            message_count = self.message_count

        transcript_available = self.transcript_available

        recording_available = self.recording_available

        eval_outputs: dict[str, Any] | Unset = UNSET
        if not isinstance(self.eval_outputs, Unset):
            eval_outputs = self.eval_outputs.to_dict()

        error_localizer_tasks = self.error_localizer_tasks

        call_summary: None | str | Unset
        if isinstance(self.call_summary, Unset):
            call_summary = UNSET
        else:
            call_summary = self.call_summary

        agent_version: None | str | Unset
        if isinstance(self.agent_version, Unset):
            agent_version = UNSET
        elif isinstance(self.agent_version, UUID):
            agent_version = str(self.agent_version)
        else:
            agent_version = self.agent_version

        customer_cost_cents: int | None | Unset
        if isinstance(self.customer_cost_cents, Unset):
            customer_cost_cents = UNSET
        else:
            customer_cost_cents = self.customer_cost_cents

        system_metrics = self.system_metrics

        cost_breakdown = self.cost_breakdown

        customer_call_id: None | str | Unset
        if isinstance(self.customer_call_id, Unset):
            customer_call_id = UNSET
        else:
            customer_call_id = self.customer_call_id

        simulation_call_type: str | Unset = UNSET
        if not isinstance(self.simulation_call_type, Unset):
            simulation_call_type = self.simulation_call_type.value

        processing_skipped = self.processing_skipped

        processing_skip_reason = self.processing_skip_reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if phone_number is not UNSET:
            field_dict["phone_number"] = phone_number
        if service_provider_call_id is not UNSET:
            field_dict["service_provider_call_id"] = service_provider_call_id
        if status is not UNSET:
            field_dict["status"] = status
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at
        if duration_seconds is not UNSET:
            field_dict["duration_seconds"] = duration_seconds
        if recording_url is not UNSET:
            field_dict["recording_url"] = recording_url
        if cost_cents is not UNSET:
            field_dict["cost_cents"] = cost_cents
        if call_metadata is not UNSET:
            field_dict["call_metadata"] = call_metadata
        if error_message is not UNSET:
            field_dict["error_message"] = error_message
        if scenario_name is not UNSET:
            field_dict["scenario_name"] = scenario_name
        if transcripts is not UNSET:
            field_dict["transcripts"] = transcripts
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if provider_call_data is not UNSET:
            field_dict["provider_call_data"] = provider_call_data
        if stereo_recording_url is not UNSET:
            field_dict["stereo_recording_url"] = stereo_recording_url
        if ended_reason is not UNSET:
            field_dict["ended_reason"] = ended_reason
        if stt_cost_cents is not UNSET:
            field_dict["stt_cost_cents"] = stt_cost_cents
        if llm_cost_cents is not UNSET:
            field_dict["llm_cost_cents"] = llm_cost_cents
        if tts_cost_cents is not UNSET:
            field_dict["tts_cost_cents"] = tts_cost_cents
        if overall_score is not UNSET:
            field_dict["overall_score"] = overall_score
        if response_time_ms is not UNSET:
            field_dict["response_time_ms"] = response_time_ms
        if response_time_seconds is not UNSET:
            field_dict["response_time_seconds"] = response_time_seconds
        if assistant_id is not UNSET:
            field_dict["assistant_id"] = assistant_id
        if customer_number is not UNSET:
            field_dict["customer_number"] = customer_number
        if call_type is not UNSET:
            field_dict["call_type"] = call_type
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at
        if analysis_data is not UNSET:
            field_dict["analysis_data"] = analysis_data
        if evaluation_data is not UNSET:
            field_dict["evaluation_data"] = evaluation_data
        if message_count is not UNSET:
            field_dict["message_count"] = message_count
        if transcript_available is not UNSET:
            field_dict["transcript_available"] = transcript_available
        if recording_available is not UNSET:
            field_dict["recording_available"] = recording_available
        if eval_outputs is not UNSET:
            field_dict["eval_outputs"] = eval_outputs
        if error_localizer_tasks is not UNSET:
            field_dict["error_localizer_tasks"] = error_localizer_tasks
        if call_summary is not UNSET:
            field_dict["call_summary"] = call_summary
        if agent_version is not UNSET:
            field_dict["agent_version"] = agent_version
        if customer_cost_cents is not UNSET:
            field_dict["customer_cost_cents"] = customer_cost_cents
        if system_metrics is not UNSET:
            field_dict["system_metrics"] = system_metrics
        if cost_breakdown is not UNSET:
            field_dict["cost_breakdown"] = cost_breakdown
        if customer_call_id is not UNSET:
            field_dict["customer_call_id"] = customer_call_id
        if simulation_call_type is not UNSET:
            field_dict["simulation_call_type"] = simulation_call_type
        if processing_skipped is not UNSET:
            field_dict["processing_skipped"] = processing_skipped
        if processing_skip_reason is not UNSET:
            field_dict["processing_skip_reason"] = processing_skip_reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.call_execution_analysis_data import CallExecutionAnalysisData
        from ..models.call_execution_call_metadata import CallExecutionCallMetadata
        from ..models.call_execution_eval_outputs import CallExecutionEvalOutputs
        from ..models.call_execution_evaluation_data import CallExecutionEvaluationData
        from ..models.call_execution_provider_call_data import (
            CallExecutionProviderCallData,
        )

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        def _parse_phone_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone_number = _parse_phone_number(d.pop("phone_number", UNSET))

        service_provider_call_id = d.pop("service_provider_call_id", UNSET)

        _status = d.pop("status", UNSET)
        status: CallExecutionStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = CallExecutionStatus(_status)

        def _parse_started_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_completed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        completed_at = _parse_completed_at(d.pop("completed_at", UNSET))

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

        def _parse_cost_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        cost_cents = _parse_cost_cents(d.pop("cost_cents", UNSET))

        _call_metadata = d.pop("call_metadata", UNSET)
        call_metadata: CallExecutionCallMetadata | Unset
        if isinstance(_call_metadata, Unset):
            call_metadata = UNSET
        else:
            call_metadata = CallExecutionCallMetadata.from_dict(_call_metadata)

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        scenario_name = d.pop("scenario_name", UNSET)

        transcripts = d.pop("transcripts", UNSET)

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

        _provider_call_data = d.pop("provider_call_data", UNSET)
        provider_call_data: CallExecutionProviderCallData | Unset
        if isinstance(_provider_call_data, Unset):
            provider_call_data = UNSET
        else:
            provider_call_data = CallExecutionProviderCallData.from_dict(
                _provider_call_data
            )

        def _parse_stereo_recording_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stereo_recording_url = _parse_stereo_recording_url(
            d.pop("stereo_recording_url", UNSET)
        )

        def _parse_ended_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ended_reason = _parse_ended_reason(d.pop("ended_reason", UNSET))

        def _parse_stt_cost_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        stt_cost_cents = _parse_stt_cost_cents(d.pop("stt_cost_cents", UNSET))

        def _parse_llm_cost_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        llm_cost_cents = _parse_llm_cost_cents(d.pop("llm_cost_cents", UNSET))

        def _parse_tts_cost_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        tts_cost_cents = _parse_tts_cost_cents(d.pop("tts_cost_cents", UNSET))

        def _parse_overall_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        overall_score = _parse_overall_score(d.pop("overall_score", UNSET))

        def _parse_response_time_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        response_time_ms = _parse_response_time_ms(d.pop("response_time_ms", UNSET))

        response_time_seconds = d.pop("response_time_seconds", UNSET)

        def _parse_assistant_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        assistant_id = _parse_assistant_id(d.pop("assistant_id", UNSET))

        def _parse_customer_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        customer_number = _parse_customer_number(d.pop("customer_number", UNSET))

        def _parse_call_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_type = _parse_call_type(d.pop("call_type", UNSET))

        def _parse_ended_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ended_at_type_0 = isoparse(data)

                return ended_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        ended_at = _parse_ended_at(d.pop("ended_at", UNSET))

        _analysis_data = d.pop("analysis_data", UNSET)
        analysis_data: CallExecutionAnalysisData | Unset
        if isinstance(_analysis_data, Unset):
            analysis_data = UNSET
        else:
            analysis_data = CallExecutionAnalysisData.from_dict(_analysis_data)

        _evaluation_data = d.pop("evaluation_data", UNSET)
        evaluation_data: CallExecutionEvaluationData | Unset
        if isinstance(_evaluation_data, Unset):
            evaluation_data = UNSET
        else:
            evaluation_data = CallExecutionEvaluationData.from_dict(_evaluation_data)

        def _parse_message_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        message_count = _parse_message_count(d.pop("message_count", UNSET))

        transcript_available = d.pop("transcript_available", UNSET)

        recording_available = d.pop("recording_available", UNSET)

        _eval_outputs = d.pop("eval_outputs", UNSET)
        eval_outputs: CallExecutionEvalOutputs | Unset
        if isinstance(_eval_outputs, Unset):
            eval_outputs = UNSET
        else:
            eval_outputs = CallExecutionEvalOutputs.from_dict(_eval_outputs)

        error_localizer_tasks = d.pop("error_localizer_tasks", UNSET)

        def _parse_call_summary(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_summary = _parse_call_summary(d.pop("call_summary", UNSET))

        def _parse_agent_version(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                agent_version_type_0 = UUID(data)

                return agent_version_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        agent_version = _parse_agent_version(d.pop("agent_version", UNSET))

        def _parse_customer_cost_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        customer_cost_cents = _parse_customer_cost_cents(
            d.pop("customer_cost_cents", UNSET)
        )

        system_metrics = d.pop("system_metrics", UNSET)

        cost_breakdown = d.pop("cost_breakdown", UNSET)

        def _parse_customer_call_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        customer_call_id = _parse_customer_call_id(d.pop("customer_call_id", UNSET))

        _simulation_call_type = d.pop("simulation_call_type", UNSET)
        simulation_call_type: CallExecutionSimulationCallType | Unset
        if isinstance(_simulation_call_type, Unset):
            simulation_call_type = UNSET
        else:
            simulation_call_type = CallExecutionSimulationCallType(
                _simulation_call_type
            )

        processing_skipped = d.pop("processing_skipped", UNSET)

        processing_skip_reason = d.pop("processing_skip_reason", UNSET)

        call_execution = cls(
            id=id,
            phone_number=phone_number,
            service_provider_call_id=service_provider_call_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            recording_url=recording_url,
            cost_cents=cost_cents,
            call_metadata=call_metadata,
            error_message=error_message,
            scenario_name=scenario_name,
            transcripts=transcripts,
            created_at=created_at,
            updated_at=updated_at,
            provider_call_data=provider_call_data,
            stereo_recording_url=stereo_recording_url,
            ended_reason=ended_reason,
            stt_cost_cents=stt_cost_cents,
            llm_cost_cents=llm_cost_cents,
            tts_cost_cents=tts_cost_cents,
            overall_score=overall_score,
            response_time_ms=response_time_ms,
            response_time_seconds=response_time_seconds,
            assistant_id=assistant_id,
            customer_number=customer_number,
            call_type=call_type,
            ended_at=ended_at,
            analysis_data=analysis_data,
            evaluation_data=evaluation_data,
            message_count=message_count,
            transcript_available=transcript_available,
            recording_available=recording_available,
            eval_outputs=eval_outputs,
            error_localizer_tasks=error_localizer_tasks,
            call_summary=call_summary,
            agent_version=agent_version,
            customer_cost_cents=customer_cost_cents,
            system_metrics=system_metrics,
            cost_breakdown=cost_breakdown,
            customer_call_id=customer_call_id,
            simulation_call_type=simulation_call_type,
            processing_skipped=processing_skipped,
            processing_skip_reason=processing_skip_reason,
        )

        call_execution.additional_properties = d
        return call_execution

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
