from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="UsersTableRow")


@_attrs_define
class UsersTableRow:
    """
    Attributes:
        total_cost (float):
        user_id (None | str | Unset):
        total_tokens (int | None | Unset):
        input_tokens (int | None | Unset):
        output_tokens (int | None | Unset):
        num_traces (int | None | Unset):
        num_sessions (int | None | Unset):
        num_sessions_is_approximate (bool | Unset):
        avg_session_duration (float | None | Unset):
        avg_trace_latency (float | None | Unset):
        num_llm_calls (int | None | Unset):
        num_guardrails_triggered (int | None | Unset):
        activated_at (datetime.datetime | None | Unset):
        last_active (datetime.datetime | None | Unset):
        num_active_days (int | None | Unset):
        num_traces_with_errors (int | None | Unset):
        bool_eval_pass_rate (float | None | Unset):
        avg_output_float (float | None | Unset):
        project_id (None | Unset | UUID):
        project_name (None | str | Unset):
        user_id_type (None | str | Unset):
        user_id_hash (None | str | Unset):
        end_user_id (None | Unset | UUID):
    """

    total_cost: float
    user_id: None | str | Unset = UNSET
    total_tokens: int | None | Unset = UNSET
    input_tokens: int | None | Unset = UNSET
    output_tokens: int | None | Unset = UNSET
    num_traces: int | None | Unset = UNSET
    num_sessions: int | None | Unset = UNSET
    num_sessions_is_approximate: bool | Unset = UNSET
    avg_session_duration: float | None | Unset = UNSET
    avg_trace_latency: float | None | Unset = UNSET
    num_llm_calls: int | None | Unset = UNSET
    num_guardrails_triggered: int | None | Unset = UNSET
    activated_at: datetime.datetime | None | Unset = UNSET
    last_active: datetime.datetime | None | Unset = UNSET
    num_active_days: int | None | Unset = UNSET
    num_traces_with_errors: int | None | Unset = UNSET
    bool_eval_pass_rate: float | None | Unset = UNSET
    avg_output_float: float | None | Unset = UNSET
    project_id: None | Unset | UUID = UNSET
    project_name: None | str | Unset = UNSET
    user_id_type: None | str | Unset = UNSET
    user_id_hash: None | str | Unset = UNSET
    end_user_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_cost = self.total_cost

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        total_tokens: int | None | Unset
        if isinstance(self.total_tokens, Unset):
            total_tokens = UNSET
        else:
            total_tokens = self.total_tokens

        input_tokens: int | None | Unset
        if isinstance(self.input_tokens, Unset):
            input_tokens = UNSET
        else:
            input_tokens = self.input_tokens

        output_tokens: int | None | Unset
        if isinstance(self.output_tokens, Unset):
            output_tokens = UNSET
        else:
            output_tokens = self.output_tokens

        num_traces: int | None | Unset
        if isinstance(self.num_traces, Unset):
            num_traces = UNSET
        else:
            num_traces = self.num_traces

        num_sessions: int | None | Unset
        if isinstance(self.num_sessions, Unset):
            num_sessions = UNSET
        else:
            num_sessions = self.num_sessions

        num_sessions_is_approximate = self.num_sessions_is_approximate

        avg_session_duration: float | None | Unset
        if isinstance(self.avg_session_duration, Unset):
            avg_session_duration = UNSET
        else:
            avg_session_duration = self.avg_session_duration

        avg_trace_latency: float | None | Unset
        if isinstance(self.avg_trace_latency, Unset):
            avg_trace_latency = UNSET
        else:
            avg_trace_latency = self.avg_trace_latency

        num_llm_calls: int | None | Unset
        if isinstance(self.num_llm_calls, Unset):
            num_llm_calls = UNSET
        else:
            num_llm_calls = self.num_llm_calls

        num_guardrails_triggered: int | None | Unset
        if isinstance(self.num_guardrails_triggered, Unset):
            num_guardrails_triggered = UNSET
        else:
            num_guardrails_triggered = self.num_guardrails_triggered

        activated_at: None | str | Unset
        if isinstance(self.activated_at, Unset):
            activated_at = UNSET
        elif isinstance(self.activated_at, datetime.datetime):
            activated_at = self.activated_at.isoformat()
        else:
            activated_at = self.activated_at

        last_active: None | str | Unset
        if isinstance(self.last_active, Unset):
            last_active = UNSET
        elif isinstance(self.last_active, datetime.datetime):
            last_active = self.last_active.isoformat()
        else:
            last_active = self.last_active

        num_active_days: int | None | Unset
        if isinstance(self.num_active_days, Unset):
            num_active_days = UNSET
        else:
            num_active_days = self.num_active_days

        num_traces_with_errors: int | None | Unset
        if isinstance(self.num_traces_with_errors, Unset):
            num_traces_with_errors = UNSET
        else:
            num_traces_with_errors = self.num_traces_with_errors

        bool_eval_pass_rate: float | None | Unset
        if isinstance(self.bool_eval_pass_rate, Unset):
            bool_eval_pass_rate = UNSET
        else:
            bool_eval_pass_rate = self.bool_eval_pass_rate

        avg_output_float: float | None | Unset
        if isinstance(self.avg_output_float, Unset):
            avg_output_float = UNSET
        else:
            avg_output_float = self.avg_output_float

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        elif isinstance(self.project_id, UUID):
            project_id = str(self.project_id)
        else:
            project_id = self.project_id

        project_name: None | str | Unset
        if isinstance(self.project_name, Unset):
            project_name = UNSET
        else:
            project_name = self.project_name

        user_id_type: None | str | Unset
        if isinstance(self.user_id_type, Unset):
            user_id_type = UNSET
        else:
            user_id_type = self.user_id_type

        user_id_hash: None | str | Unset
        if isinstance(self.user_id_hash, Unset):
            user_id_hash = UNSET
        else:
            user_id_hash = self.user_id_hash

        end_user_id: None | str | Unset
        if isinstance(self.end_user_id, Unset):
            end_user_id = UNSET
        elif isinstance(self.end_user_id, UUID):
            end_user_id = str(self.end_user_id)
        else:
            end_user_id = self.end_user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_cost": total_cost,
            }
        )
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if total_tokens is not UNSET:
            field_dict["total_tokens"] = total_tokens
        if input_tokens is not UNSET:
            field_dict["input_tokens"] = input_tokens
        if output_tokens is not UNSET:
            field_dict["output_tokens"] = output_tokens
        if num_traces is not UNSET:
            field_dict["num_traces"] = num_traces
        if num_sessions is not UNSET:
            field_dict["num_sessions"] = num_sessions
        if num_sessions_is_approximate is not UNSET:
            field_dict["num_sessions_is_approximate"] = num_sessions_is_approximate
        if avg_session_duration is not UNSET:
            field_dict["avg_session_duration"] = avg_session_duration
        if avg_trace_latency is not UNSET:
            field_dict["avg_trace_latency"] = avg_trace_latency
        if num_llm_calls is not UNSET:
            field_dict["num_llm_calls"] = num_llm_calls
        if num_guardrails_triggered is not UNSET:
            field_dict["num_guardrails_triggered"] = num_guardrails_triggered
        if activated_at is not UNSET:
            field_dict["activated_at"] = activated_at
        if last_active is not UNSET:
            field_dict["last_active"] = last_active
        if num_active_days is not UNSET:
            field_dict["num_active_days"] = num_active_days
        if num_traces_with_errors is not UNSET:
            field_dict["num_traces_with_errors"] = num_traces_with_errors
        if bool_eval_pass_rate is not UNSET:
            field_dict["bool_eval_pass_rate"] = bool_eval_pass_rate
        if avg_output_float is not UNSET:
            field_dict["avg_output_float"] = avg_output_float
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if project_name is not UNSET:
            field_dict["project_name"] = project_name
        if user_id_type is not UNSET:
            field_dict["user_id_type"] = user_id_type
        if user_id_hash is not UNSET:
            field_dict["user_id_hash"] = user_id_hash
        if end_user_id is not UNSET:
            field_dict["end_user_id"] = end_user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_cost = d.pop("total_cost")

        def _parse_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_total_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_tokens = _parse_total_tokens(d.pop("total_tokens", UNSET))

        def _parse_input_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        input_tokens = _parse_input_tokens(d.pop("input_tokens", UNSET))

        def _parse_output_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        output_tokens = _parse_output_tokens(d.pop("output_tokens", UNSET))

        def _parse_num_traces(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_traces = _parse_num_traces(d.pop("num_traces", UNSET))

        def _parse_num_sessions(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_sessions = _parse_num_sessions(d.pop("num_sessions", UNSET))

        num_sessions_is_approximate = d.pop("num_sessions_is_approximate", UNSET)

        def _parse_avg_session_duration(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_session_duration = _parse_avg_session_duration(
            d.pop("avg_session_duration", UNSET)
        )

        def _parse_avg_trace_latency(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_trace_latency = _parse_avg_trace_latency(d.pop("avg_trace_latency", UNSET))

        def _parse_num_llm_calls(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_llm_calls = _parse_num_llm_calls(d.pop("num_llm_calls", UNSET))

        def _parse_num_guardrails_triggered(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_guardrails_triggered = _parse_num_guardrails_triggered(
            d.pop("num_guardrails_triggered", UNSET)
        )

        def _parse_activated_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                activated_at_type_0 = isoparse(data)

                return activated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        activated_at = _parse_activated_at(d.pop("activated_at", UNSET))

        def _parse_last_active(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_active_type_0 = isoparse(data)

                return last_active_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_active = _parse_last_active(d.pop("last_active", UNSET))

        def _parse_num_active_days(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_active_days = _parse_num_active_days(d.pop("num_active_days", UNSET))

        def _parse_num_traces_with_errors(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        num_traces_with_errors = _parse_num_traces_with_errors(
            d.pop("num_traces_with_errors", UNSET)
        )

        def _parse_bool_eval_pass_rate(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        bool_eval_pass_rate = _parse_bool_eval_pass_rate(
            d.pop("bool_eval_pass_rate", UNSET)
        )

        def _parse_avg_output_float(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_output_float = _parse_avg_output_float(d.pop("avg_output_float", UNSET))

        def _parse_project_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                project_id_type_0 = UUID(data)

                return project_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        def _parse_project_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_name = _parse_project_name(d.pop("project_name", UNSET))

        def _parse_user_id_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id_type = _parse_user_id_type(d.pop("user_id_type", UNSET))

        def _parse_user_id_hash(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id_hash = _parse_user_id_hash(d.pop("user_id_hash", UNSET))

        def _parse_end_user_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_user_id_type_0 = UUID(data)

                return end_user_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        end_user_id = _parse_end_user_id(d.pop("end_user_id", UNSET))

        users_table_row = cls(
            total_cost=total_cost,
            user_id=user_id,
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            num_traces=num_traces,
            num_sessions=num_sessions,
            num_sessions_is_approximate=num_sessions_is_approximate,
            avg_session_duration=avg_session_duration,
            avg_trace_latency=avg_trace_latency,
            num_llm_calls=num_llm_calls,
            num_guardrails_triggered=num_guardrails_triggered,
            activated_at=activated_at,
            last_active=last_active,
            num_active_days=num_active_days,
            num_traces_with_errors=num_traces_with_errors,
            bool_eval_pass_rate=bool_eval_pass_rate,
            avg_output_float=avg_output_float,
            project_id=project_id,
            project_name=project_name,
            user_id_type=user_id_type,
            user_id_hash=user_id_hash,
            end_user_id=end_user_id,
        )

        users_table_row.additional_properties = d
        return users_table_row

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
