from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.execution_metrics_status import ExecutionMetricsStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="ExecutionMetrics")


@_attrs_define
class ExecutionMetrics:
    """
    Attributes:
        execution_id (UUID):
        status (ExecutionMetricsStatus | Unset): Current status of the test execution
        started_at (datetime.datetime | Unset): When the test execution started
        completed_at (datetime.datetime | None | Unset): When the test execution completed
        total_calls (int | Unset): Total number of calls to be made
        completed_calls (int | Unset): Number of successfully completed calls
        failed_calls (int | Unset): Number of failed calls
        metrics (str | Unset):
    """

    execution_id: UUID
    status: ExecutionMetricsStatus | Unset = UNSET
    started_at: datetime.datetime | Unset = UNSET
    completed_at: datetime.datetime | None | Unset = UNSET
    total_calls: int | Unset = UNSET
    completed_calls: int | Unset = UNSET
    failed_calls: int | Unset = UNSET
    metrics: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        execution_id = str(self.execution_id)

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        started_at: str | Unset = UNSET
        if not isinstance(self.started_at, Unset):
            started_at = self.started_at.isoformat()

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

        metrics = self.metrics

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "execution_id": execution_id,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status
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
        if metrics is not UNSET:
            field_dict["metrics"] = metrics

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        execution_id = UUID(d.pop("execution_id"))

        _status = d.pop("status", UNSET)
        status: ExecutionMetricsStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ExecutionMetricsStatus(_status)

        _started_at = d.pop("started_at", UNSET)
        started_at: datetime.datetime | Unset
        if isinstance(_started_at, Unset):
            started_at = UNSET
        else:
            started_at = isoparse(_started_at)

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

        metrics = d.pop("metrics", UNSET)

        execution_metrics = cls(
            execution_id=execution_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            total_calls=total_calls,
            completed_calls=completed_calls,
            failed_calls=failed_calls,
            metrics=metrics,
        )

        execution_metrics.additional_properties = d
        return execution_metrics

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
