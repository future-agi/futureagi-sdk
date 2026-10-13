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
    from ..models.execution_metrics import ExecutionMetrics
    from ..models.sdk_simulation_metrics_result_chat_metrics import (
        SDKSimulationMetricsResultChatMetrics,
    )
    from ..models.sdk_simulation_metrics_result_conversation import (
        SDKSimulationMetricsResultConversation,
    )
    from ..models.sdk_simulation_metrics_result_cost import (
        SDKSimulationMetricsResultCost,
    )
    from ..models.sdk_simulation_metrics_result_latency import (
        SDKSimulationMetricsResultLatency,
    )
    from ..models.sdk_simulation_metrics_result_metrics import (
        SDKSimulationMetricsResultMetrics,
    )


T = TypeVar("T", bound="SDKSimulationMetricsResult")


@_attrs_define
class SDKSimulationMetricsResult:
    """
    Attributes:
        call_execution_id (UUID | Unset):
        execution_id (UUID | Unset):
        status (str | Unset):
        duration_seconds (float | None | Unset):
        started_at (datetime.datetime | None | Unset):
        completed_at (datetime.datetime | None | Unset):
        total_calls (int | Unset):
        completed_calls (int | Unset):
        failed_calls (int | Unset):
        latency (SDKSimulationMetricsResultLatency | Unset):
        cost (SDKSimulationMetricsResultCost | Unset):
        conversation (SDKSimulationMetricsResultConversation | Unset):
        chat_metrics (SDKSimulationMetricsResultChatMetrics | Unset):
        metrics (SDKSimulationMetricsResultMetrics | Unset):
        total_pages (int | Unset):
        current_page (int | Unset):
        count (int | Unset):
        results (list[ExecutionMetrics] | Unset):
    """

    call_execution_id: UUID | Unset = UNSET
    execution_id: UUID | Unset = UNSET
    status: str | Unset = UNSET
    duration_seconds: float | None | Unset = UNSET
    started_at: datetime.datetime | None | Unset = UNSET
    completed_at: datetime.datetime | None | Unset = UNSET
    total_calls: int | Unset = UNSET
    completed_calls: int | Unset = UNSET
    failed_calls: int | Unset = UNSET
    latency: SDKSimulationMetricsResultLatency | Unset = UNSET
    cost: SDKSimulationMetricsResultCost | Unset = UNSET
    conversation: SDKSimulationMetricsResultConversation | Unset = UNSET
    chat_metrics: SDKSimulationMetricsResultChatMetrics | Unset = UNSET
    metrics: SDKSimulationMetricsResultMetrics | Unset = UNSET
    total_pages: int | Unset = UNSET
    current_page: int | Unset = UNSET
    count: int | Unset = UNSET
    results: list[ExecutionMetrics] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        call_execution_id: str | Unset = UNSET
        if not isinstance(self.call_execution_id, Unset):
            call_execution_id = str(self.call_execution_id)

        execution_id: str | Unset = UNSET
        if not isinstance(self.execution_id, Unset):
            execution_id = str(self.execution_id)

        status = self.status

        duration_seconds: float | None | Unset
        if isinstance(self.duration_seconds, Unset):
            duration_seconds = UNSET
        else:
            duration_seconds = self.duration_seconds

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

        total_calls = self.total_calls

        completed_calls = self.completed_calls

        failed_calls = self.failed_calls

        latency: dict[str, Any] | Unset = UNSET
        if not isinstance(self.latency, Unset):
            latency = self.latency.to_dict()

        cost: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cost, Unset):
            cost = self.cost.to_dict()

        conversation: dict[str, Any] | Unset = UNSET
        if not isinstance(self.conversation, Unset):
            conversation = self.conversation.to_dict()

        chat_metrics: dict[str, Any] | Unset = UNSET
        if not isinstance(self.chat_metrics, Unset):
            chat_metrics = self.chat_metrics.to_dict()

        metrics: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metrics, Unset):
            metrics = self.metrics.to_dict()

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
        if status is not UNSET:
            field_dict["status"] = status
        if duration_seconds is not UNSET:
            field_dict["duration_seconds"] = duration_seconds
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at
        if total_calls is not UNSET:
            field_dict["total_calls"] = total_calls
        if completed_calls is not UNSET:
            field_dict["completed_calls"] = completed_calls
        if failed_calls is not UNSET:
            field_dict["failed_calls"] = failed_calls
        if latency is not UNSET:
            field_dict["latency"] = latency
        if cost is not UNSET:
            field_dict["cost"] = cost
        if conversation is not UNSET:
            field_dict["conversation"] = conversation
        if chat_metrics is not UNSET:
            field_dict["chat_metrics"] = chat_metrics
        if metrics is not UNSET:
            field_dict["metrics"] = metrics
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
        from ..models.execution_metrics import ExecutionMetrics
        from ..models.sdk_simulation_metrics_result_chat_metrics import (
            SDKSimulationMetricsResultChatMetrics,
        )
        from ..models.sdk_simulation_metrics_result_conversation import (
            SDKSimulationMetricsResultConversation,
        )
        from ..models.sdk_simulation_metrics_result_cost import (
            SDKSimulationMetricsResultCost,
        )
        from ..models.sdk_simulation_metrics_result_latency import (
            SDKSimulationMetricsResultLatency,
        )
        from ..models.sdk_simulation_metrics_result_metrics import (
            SDKSimulationMetricsResultMetrics,
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

        status = d.pop("status", UNSET)

        def _parse_duration_seconds(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        duration_seconds = _parse_duration_seconds(d.pop("duration_seconds", UNSET))

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

        total_calls = d.pop("total_calls", UNSET)

        completed_calls = d.pop("completed_calls", UNSET)

        failed_calls = d.pop("failed_calls", UNSET)

        _latency = d.pop("latency", UNSET)
        latency: SDKSimulationMetricsResultLatency | Unset
        if isinstance(_latency, Unset):
            latency = UNSET
        else:
            latency = SDKSimulationMetricsResultLatency.from_dict(_latency)

        _cost = d.pop("cost", UNSET)
        cost: SDKSimulationMetricsResultCost | Unset
        if isinstance(_cost, Unset):
            cost = UNSET
        else:
            cost = SDKSimulationMetricsResultCost.from_dict(_cost)

        _conversation = d.pop("conversation", UNSET)
        conversation: SDKSimulationMetricsResultConversation | Unset
        if isinstance(_conversation, Unset):
            conversation = UNSET
        else:
            conversation = SDKSimulationMetricsResultConversation.from_dict(
                _conversation
            )

        _chat_metrics = d.pop("chat_metrics", UNSET)
        chat_metrics: SDKSimulationMetricsResultChatMetrics | Unset
        if isinstance(_chat_metrics, Unset):
            chat_metrics = UNSET
        else:
            chat_metrics = SDKSimulationMetricsResultChatMetrics.from_dict(
                _chat_metrics
            )

        _metrics = d.pop("metrics", UNSET)
        metrics: SDKSimulationMetricsResultMetrics | Unset
        if isinstance(_metrics, Unset):
            metrics = UNSET
        else:
            metrics = SDKSimulationMetricsResultMetrics.from_dict(_metrics)

        total_pages = d.pop("total_pages", UNSET)

        current_page = d.pop("current_page", UNSET)

        count = d.pop("count", UNSET)

        _results = d.pop("results", UNSET)
        results: list[ExecutionMetrics] | Unset = UNSET
        if _results is not UNSET:
            results = []
            for results_item_data in _results:
                results_item = ExecutionMetrics.from_dict(results_item_data)

                results.append(results_item)

        sdk_simulation_metrics_result = cls(
            call_execution_id=call_execution_id,
            execution_id=execution_id,
            status=status,
            duration_seconds=duration_seconds,
            started_at=started_at,
            completed_at=completed_at,
            total_calls=total_calls,
            completed_calls=completed_calls,
            failed_calls=failed_calls,
            latency=latency,
            cost=cost,
            conversation=conversation,
            chat_metrics=chat_metrics,
            metrics=metrics,
            total_pages=total_pages,
            current_page=current_page,
            count=count,
            results=results,
        )

        sdk_simulation_metrics_result.additional_properties = d
        return sdk_simulation_metrics_result

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
