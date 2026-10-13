from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.execution_runs import ExecutionRuns
    from ..models.sdk_simulation_runs_result_call_results import (
        SDKSimulationRunsResultCallResults,
    )
    from ..models.sdk_simulation_runs_result_cost import SDKSimulationRunsResultCost
    from ..models.sdk_simulation_runs_result_eval_explanation_summary import (
        SDKSimulationRunsResultEvalExplanationSummary,
    )
    from ..models.sdk_simulation_runs_result_eval_outputs import (
        SDKSimulationRunsResultEvalOutputs,
    )
    from ..models.sdk_simulation_runs_result_eval_results_item import (
        SDKSimulationRunsResultEvalResultsItem,
    )
    from ..models.sdk_simulation_runs_result_latency import (
        SDKSimulationRunsResultLatency,
    )


T = TypeVar("T", bound="SDKSimulationRunsResult")


@_attrs_define
class SDKSimulationRunsResult:
    """
    Attributes:
        call_execution_id (UUID | Unset):
        execution_id (UUID | Unset):
        scenario_id (UUID | Unset):
        scenario_name (str | Unset):
        status (str | Unset):
        started_at (datetime.datetime | None | Unset):
        completed_at (datetime.datetime | None | Unset):
        duration_seconds (float | None | Unset):
        ended_reason (None | str | Unset):
        call_summary (None | str | Unset):
        total_calls (int | Unset):
        completed_calls (int | Unset):
        failed_calls (int | Unset):
        eval_outputs (SDKSimulationRunsResultEvalOutputs | Unset):
        eval_results (list[SDKSimulationRunsResultEvalResultsItem] | Unset):
        latency (SDKSimulationRunsResultLatency | Unset):
        cost (SDKSimulationRunsResultCost | Unset):
        call_results (SDKSimulationRunsResultCallResults | Unset):
        eval_explanation_summary (SDKSimulationRunsResultEvalExplanationSummary | Unset):
        eval_explanation_summary_status (None | str | Unset):
        total_pages (int | Unset):
        current_page (int | Unset):
        count (int | Unset):
        results (list[ExecutionRuns] | Unset):
    """

    call_execution_id: UUID | Unset = UNSET
    execution_id: UUID | Unset = UNSET
    scenario_id: UUID | Unset = UNSET
    scenario_name: str | Unset = UNSET
    status: str | Unset = UNSET
    started_at: datetime.datetime | None | Unset = UNSET
    completed_at: datetime.datetime | None | Unset = UNSET
    duration_seconds: float | None | Unset = UNSET
    ended_reason: None | str | Unset = UNSET
    call_summary: None | str | Unset = UNSET
    total_calls: int | Unset = UNSET
    completed_calls: int | Unset = UNSET
    failed_calls: int | Unset = UNSET
    eval_outputs: SDKSimulationRunsResultEvalOutputs | Unset = UNSET
    eval_results: list[SDKSimulationRunsResultEvalResultsItem] | Unset = UNSET
    latency: SDKSimulationRunsResultLatency | Unset = UNSET
    cost: SDKSimulationRunsResultCost | Unset = UNSET
    call_results: SDKSimulationRunsResultCallResults | Unset = UNSET
    eval_explanation_summary: SDKSimulationRunsResultEvalExplanationSummary | Unset = (
        UNSET
    )
    eval_explanation_summary_status: None | str | Unset = UNSET
    total_pages: int | Unset = UNSET
    current_page: int | Unset = UNSET
    count: int | Unset = UNSET
    results: list[ExecutionRuns] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        call_execution_id: str | Unset = UNSET
        if not isinstance(self.call_execution_id, Unset):
            call_execution_id = str(self.call_execution_id)

        execution_id: str | Unset = UNSET
        if not isinstance(self.execution_id, Unset):
            execution_id = str(self.execution_id)

        scenario_id: str | Unset = UNSET
        if not isinstance(self.scenario_id, Unset):
            scenario_id = str(self.scenario_id)

        scenario_name = self.scenario_name

        status = self.status

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

        duration_seconds: float | None | Unset
        if isinstance(self.duration_seconds, Unset):
            duration_seconds = UNSET
        else:
            duration_seconds = self.duration_seconds

        ended_reason: None | str | Unset
        if isinstance(self.ended_reason, Unset):
            ended_reason = UNSET
        else:
            ended_reason = self.ended_reason

        call_summary: None | str | Unset
        if isinstance(self.call_summary, Unset):
            call_summary = UNSET
        else:
            call_summary = self.call_summary

        total_calls = self.total_calls

        completed_calls = self.completed_calls

        failed_calls = self.failed_calls

        eval_outputs: dict[str, Any] | Unset = UNSET
        if not isinstance(self.eval_outputs, Unset):
            eval_outputs = self.eval_outputs.to_dict()

        eval_results: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.eval_results, Unset):
            eval_results = []
            for eval_results_item_data in self.eval_results:
                eval_results_item = eval_results_item_data.to_dict()
                eval_results.append(eval_results_item)

        latency: dict[str, Any] | Unset = UNSET
        if not isinstance(self.latency, Unset):
            latency = self.latency.to_dict()

        cost: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cost, Unset):
            cost = self.cost.to_dict()

        call_results: dict[str, Any] | Unset = UNSET
        if not isinstance(self.call_results, Unset):
            call_results = self.call_results.to_dict()

        eval_explanation_summary: dict[str, Any] | Unset = UNSET
        if not isinstance(self.eval_explanation_summary, Unset):
            eval_explanation_summary = self.eval_explanation_summary.to_dict()

        eval_explanation_summary_status: None | str | Unset
        if isinstance(self.eval_explanation_summary_status, Unset):
            eval_explanation_summary_status = UNSET
        else:
            eval_explanation_summary_status = self.eval_explanation_summary_status

        total_pages = self.total_pages

        current_page = self.current_page

        count = self.count

        results: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.results, Unset):
            results = []
            for results_item_data in self.results:
                results_item = results_item_data.to_dict()
                results.append(results_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if call_execution_id is not UNSET:
            field_dict["call_execution_id"] = call_execution_id
        if execution_id is not UNSET:
            field_dict["execution_id"] = execution_id
        if scenario_id is not UNSET:
            field_dict["scenario_id"] = scenario_id
        if scenario_name is not UNSET:
            field_dict["scenario_name"] = scenario_name
        if status is not UNSET:
            field_dict["status"] = status
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at
        if duration_seconds is not UNSET:
            field_dict["duration_seconds"] = duration_seconds
        if ended_reason is not UNSET:
            field_dict["ended_reason"] = ended_reason
        if call_summary is not UNSET:
            field_dict["call_summary"] = call_summary
        if total_calls is not UNSET:
            field_dict["total_calls"] = total_calls
        if completed_calls is not UNSET:
            field_dict["completed_calls"] = completed_calls
        if failed_calls is not UNSET:
            field_dict["failed_calls"] = failed_calls
        if eval_outputs is not UNSET:
            field_dict["eval_outputs"] = eval_outputs
        if eval_results is not UNSET:
            field_dict["eval_results"] = eval_results
        if latency is not UNSET:
            field_dict["latency"] = latency
        if cost is not UNSET:
            field_dict["cost"] = cost
        if call_results is not UNSET:
            field_dict["call_results"] = call_results
        if eval_explanation_summary is not UNSET:
            field_dict["eval_explanation_summary"] = eval_explanation_summary
        if eval_explanation_summary_status is not UNSET:
            field_dict["eval_explanation_summary_status"] = (
                eval_explanation_summary_status
            )
        if total_pages is not UNSET:
            field_dict["total_pages"] = total_pages
        if current_page is not UNSET:
            field_dict["current_page"] = current_page
        if count is not UNSET:
            field_dict["count"] = count
        if results is not UNSET:
            field_dict["results"] = results

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.execution_runs import ExecutionRuns
        from ..models.sdk_simulation_runs_result_call_results import (
            SDKSimulationRunsResultCallResults,
        )
        from ..models.sdk_simulation_runs_result_cost import SDKSimulationRunsResultCost
        from ..models.sdk_simulation_runs_result_eval_explanation_summary import (
            SDKSimulationRunsResultEvalExplanationSummary,
        )
        from ..models.sdk_simulation_runs_result_eval_outputs import (
            SDKSimulationRunsResultEvalOutputs,
        )
        from ..models.sdk_simulation_runs_result_eval_results_item import (
            SDKSimulationRunsResultEvalResultsItem,
        )
        from ..models.sdk_simulation_runs_result_latency import (
            SDKSimulationRunsResultLatency,
        )

        d = dict(src_dict)
        _call_execution_id = d.pop("call_execution_id", UNSET)
        call_execution_id: UUID | Unset
        if isinstance(_call_execution_id, Unset):
            call_execution_id = UNSET
        else:
            call_execution_id = UUID(_call_execution_id)

        _execution_id = d.pop("execution_id", UNSET)
        execution_id: UUID | Unset
        if isinstance(_execution_id, Unset):
            execution_id = UNSET
        else:
            execution_id = UUID(_execution_id)

        _scenario_id = d.pop("scenario_id", UNSET)
        scenario_id: UUID | Unset
        if isinstance(_scenario_id, Unset):
            scenario_id = UNSET
        else:
            scenario_id = UUID(_scenario_id)

        scenario_name = d.pop("scenario_name", UNSET)

        status = d.pop("status", UNSET)

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

        def _parse_duration_seconds(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        duration_seconds = _parse_duration_seconds(d.pop("duration_seconds", UNSET))

        def _parse_ended_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ended_reason = _parse_ended_reason(d.pop("ended_reason", UNSET))

        def _parse_call_summary(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_summary = _parse_call_summary(d.pop("call_summary", UNSET))

        total_calls = d.pop("total_calls", UNSET)

        completed_calls = d.pop("completed_calls", UNSET)

        failed_calls = d.pop("failed_calls", UNSET)

        _eval_outputs = d.pop("eval_outputs", UNSET)
        eval_outputs: SDKSimulationRunsResultEvalOutputs | Unset
        if isinstance(_eval_outputs, Unset):
            eval_outputs = UNSET
        else:
            eval_outputs = SDKSimulationRunsResultEvalOutputs.from_dict(_eval_outputs)

        _eval_results = d.pop("eval_results", UNSET)
        eval_results: list[SDKSimulationRunsResultEvalResultsItem] | Unset = UNSET
        if _eval_results is not UNSET:
            eval_results = []
            for eval_results_item_data in _eval_results:
                eval_results_item = SDKSimulationRunsResultEvalResultsItem.from_dict(
                    eval_results_item_data
                )

                eval_results.append(eval_results_item)

        _latency = d.pop("latency", UNSET)
        latency: SDKSimulationRunsResultLatency | Unset
        if isinstance(_latency, Unset):
            latency = UNSET
        else:
            latency = SDKSimulationRunsResultLatency.from_dict(_latency)

        _cost = d.pop("cost", UNSET)
        cost: SDKSimulationRunsResultCost | Unset
        if isinstance(_cost, Unset):
            cost = UNSET
        else:
            cost = SDKSimulationRunsResultCost.from_dict(_cost)

        _call_results = d.pop("call_results", UNSET)
        call_results: SDKSimulationRunsResultCallResults | Unset
        if isinstance(_call_results, Unset):
            call_results = UNSET
        else:
            call_results = SDKSimulationRunsResultCallResults.from_dict(_call_results)

        _eval_explanation_summary = d.pop("eval_explanation_summary", UNSET)
        eval_explanation_summary: SDKSimulationRunsResultEvalExplanationSummary | Unset
        if isinstance(_eval_explanation_summary, Unset):
            eval_explanation_summary = UNSET
        else:
            eval_explanation_summary = (
                SDKSimulationRunsResultEvalExplanationSummary.from_dict(
                    _eval_explanation_summary
                )
            )

        def _parse_eval_explanation_summary_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_explanation_summary_status = _parse_eval_explanation_summary_status(
            d.pop("eval_explanation_summary_status", UNSET)
        )

        total_pages = d.pop("total_pages", UNSET)

        current_page = d.pop("current_page", UNSET)

        count = d.pop("count", UNSET)

        _results = d.pop("results", UNSET)
        results: list[ExecutionRuns] | Unset = UNSET
        if _results is not UNSET:
            results = []
            for results_item_data in _results:
                results_item = ExecutionRuns.from_dict(results_item_data)

                results.append(results_item)

        sdk_simulation_runs_result = cls(
            call_execution_id=call_execution_id,
            execution_id=execution_id,
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            ended_reason=ended_reason,
            call_summary=call_summary,
            total_calls=total_calls,
            completed_calls=completed_calls,
            failed_calls=failed_calls,
            eval_outputs=eval_outputs,
            eval_results=eval_results,
            latency=latency,
            cost=cost,
            call_results=call_results,
            eval_explanation_summary=eval_explanation_summary,
            eval_explanation_summary_status=eval_explanation_summary_status,
            total_pages=total_pages,
            current_page=current_page,
            count=count,
            results=results,
        )

        sdk_simulation_runs_result.additional_properties = d
        return sdk_simulation_runs_result

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
