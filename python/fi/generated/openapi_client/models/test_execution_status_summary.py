from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.test_execution_status_summary_scenarios_item import (
        TestExecutionStatusSummaryScenariosItem,
    )


T = TypeVar("T", bound="TestExecutionStatusSummary")


@_attrs_define
class TestExecutionStatusSummary:
    """
    Attributes:
        run_test_id (str):
        execution_id (str):
        status (str):
        total_scenarios (int):
        total_calls (int):
        completed_calls (int):
        failed_calls (int):
        success_rate (float):
        start_time (datetime.datetime):
        end_time (datetime.datetime | None):
        scenarios (list[TestExecutionStatusSummaryScenariosItem]):
        error (None | str):
    """

    run_test_id: str
    execution_id: str
    status: str
    total_scenarios: int
    total_calls: int
    completed_calls: int
    failed_calls: int
    success_rate: float
    start_time: datetime.datetime
    end_time: datetime.datetime | None
    scenarios: list[TestExecutionStatusSummaryScenariosItem]
    error: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_test_id = self.run_test_id

        execution_id = self.execution_id

        status = self.status

        total_scenarios = self.total_scenarios

        total_calls = self.total_calls

        completed_calls = self.completed_calls

        failed_calls = self.failed_calls

        success_rate = self.success_rate

        start_time = self.start_time.isoformat()

        end_time: None | str
        if isinstance(self.end_time, datetime.datetime):
            end_time = self.end_time.isoformat()
        else:
            end_time = self.end_time

        scenarios = []
        for scenarios_item_data in self.scenarios:
            scenarios_item = scenarios_item_data.to_dict()
            scenarios.append(scenarios_item)

        error: None | str
        error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "run_test_id": run_test_id,
                "execution_id": execution_id,
                "status": status,
                "total_scenarios": total_scenarios,
                "total_calls": total_calls,
                "completed_calls": completed_calls,
                "failed_calls": failed_calls,
                "success_rate": success_rate,
                "start_time": start_time,
                "end_time": end_time,
                "scenarios": scenarios,
                "error": error,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.test_execution_status_summary_scenarios_item import (
            TestExecutionStatusSummaryScenariosItem,
        )

        d = dict(src_dict)
        run_test_id = d.pop("run_test_id")

        execution_id = d.pop("execution_id")

        status = d.pop("status")

        total_scenarios = d.pop("total_scenarios")

        total_calls = d.pop("total_calls")

        completed_calls = d.pop("completed_calls")

        failed_calls = d.pop("failed_calls")

        success_rate = d.pop("success_rate")

        start_time = isoparse(d.pop("start_time"))

        def _parse_end_time(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_time_type_0 = isoparse(data)

                return end_time_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        end_time = _parse_end_time(d.pop("end_time"))

        scenarios = []
        _scenarios = d.pop("scenarios")
        for scenarios_item_data in _scenarios:
            scenarios_item = TestExecutionStatusSummaryScenariosItem.from_dict(
                scenarios_item_data
            )

            scenarios.append(scenarios_item)

        def _parse_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error = _parse_error(d.pop("error"))

        test_execution_status_summary = cls(
            run_test_id=run_test_id,
            execution_id=execution_id,
            status=status,
            total_scenarios=total_scenarios,
            total_calls=total_calls,
            completed_calls=completed_calls,
            failed_calls=failed_calls,
            success_rate=success_rate,
            start_time=start_time,
            end_time=end_time,
            scenarios=scenarios,
            error=error,
        )

        test_execution_status_summary.additional_properties = d
        return test_execution_status_summary

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
