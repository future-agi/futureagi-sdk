from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.test_execution_status import TestExecutionStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.call_execution import CallExecution
    from ..models.test_execution_execution_metadata import (
        TestExecutionExecutionMetadata,
    )
    from ..models.test_execution_scenario_ids import TestExecutionScenarioIds


T = TypeVar("T", bound="TestExecution")


@_attrs_define
class TestExecution:
    """
    Attributes:
        run_test (UUID): The run test being executed
        id (UUID | Unset):
        run_test_name (str | Unset):
        agent_definition_name (str | Unset):
        status (TestExecutionStatus | Unset): Current status of the test execution
        error_reason (None | str | Unset):
        started_at (datetime.datetime | Unset): When the test execution started
        completed_at (datetime.datetime | None | Unset): When the test execution completed
        total_scenarios (int | Unset): Total number of scenarios in this execution
        total_calls (int | Unset): Total number of calls to be made
        completed_calls (int | Unset): Number of successfully completed calls
        failed_calls (int | Unset): Number of failed calls
        execution_metadata (TestExecutionExecutionMetadata | Unset): Additional metadata about the execution
        duration_seconds (str | Unset):
        success_rate (str | Unset):
        calls (list[CallExecution] | Unset):
        created_at (datetime.datetime | Unset):
        scenario_ids (TestExecutionScenarioIds | Unset): List of scenario IDs that were executed in this run
        simulator_agent_name (str | Unset):
        simulator_agent_id (UUID | Unset):
        agent_definition_used_name (str | Unset):
        agent_definition_used_id (UUID | Unset):
        calls_attempted (str | Unset):
        calls_connected_percentage (str | Unset):
    """

    run_test: UUID
    id: UUID | Unset = UNSET
    run_test_name: str | Unset = UNSET
    agent_definition_name: str | Unset = UNSET
    status: TestExecutionStatus | Unset = UNSET
    error_reason: None | str | Unset = UNSET
    started_at: datetime.datetime | Unset = UNSET
    completed_at: datetime.datetime | None | Unset = UNSET
    total_scenarios: int | Unset = UNSET
    total_calls: int | Unset = UNSET
    completed_calls: int | Unset = UNSET
    failed_calls: int | Unset = UNSET
    execution_metadata: TestExecutionExecutionMetadata | Unset = UNSET
    duration_seconds: str | Unset = UNSET
    success_rate: str | Unset = UNSET
    calls: list[CallExecution] | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    scenario_ids: TestExecutionScenarioIds | Unset = UNSET
    simulator_agent_name: str | Unset = UNSET
    simulator_agent_id: UUID | Unset = UNSET
    agent_definition_used_name: str | Unset = UNSET
    agent_definition_used_id: UUID | Unset = UNSET
    calls_attempted: str | Unset = UNSET
    calls_connected_percentage: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_test = str(self.run_test)

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        run_test_name = self.run_test_name

        agent_definition_name = self.agent_definition_name

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        error_reason: None | str | Unset
        if isinstance(self.error_reason, Unset):
            error_reason = UNSET
        else:
            error_reason = self.error_reason

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

        total_scenarios = self.total_scenarios

        total_calls = self.total_calls

        completed_calls = self.completed_calls

        failed_calls = self.failed_calls

        execution_metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.execution_metadata, Unset):
            execution_metadata = self.execution_metadata.to_dict()

        duration_seconds = self.duration_seconds

        success_rate = self.success_rate

        calls: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.calls, Unset):
            calls = []
            for calls_item_data in self.calls:
                calls_item = calls_item_data.to_dict()
                calls.append(calls_item)

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        scenario_ids: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scenario_ids, Unset):
            scenario_ids = self.scenario_ids.to_dict()

        simulator_agent_name = self.simulator_agent_name

        simulator_agent_id: str | Unset = UNSET
        if not isinstance(self.simulator_agent_id, Unset):
            simulator_agent_id = str(self.simulator_agent_id)

        agent_definition_used_name = self.agent_definition_used_name

        agent_definition_used_id: str | Unset = UNSET
        if not isinstance(self.agent_definition_used_id, Unset):
            agent_definition_used_id = str(self.agent_definition_used_id)

        calls_attempted = self.calls_attempted

        calls_connected_percentage = self.calls_connected_percentage

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "run_test": run_test,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if run_test_name is not UNSET:
            field_dict["run_test_name"] = run_test_name
        if agent_definition_name is not UNSET:
            field_dict["agent_definition_name"] = agent_definition_name
        if status is not UNSET:
            field_dict["status"] = status
        if error_reason is not UNSET:
            field_dict["error_reason"] = error_reason
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at
        if total_scenarios is not UNSET:
            field_dict["total_scenarios"] = total_scenarios
        if total_calls is not UNSET:
            field_dict["total_calls"] = total_calls
        if completed_calls is not UNSET:
            field_dict["completed_calls"] = completed_calls
        if failed_calls is not UNSET:
            field_dict["failed_calls"] = failed_calls
        if execution_metadata is not UNSET:
            field_dict["execution_metadata"] = execution_metadata
        if duration_seconds is not UNSET:
            field_dict["duration_seconds"] = duration_seconds
        if success_rate is not UNSET:
            field_dict["success_rate"] = success_rate
        if calls is not UNSET:
            field_dict["calls"] = calls
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if scenario_ids is not UNSET:
            field_dict["scenario_ids"] = scenario_ids
        if simulator_agent_name is not UNSET:
            field_dict["simulator_agent_name"] = simulator_agent_name
        if simulator_agent_id is not UNSET:
            field_dict["simulator_agent_id"] = simulator_agent_id
        if agent_definition_used_name is not UNSET:
            field_dict["agent_definition_used_name"] = agent_definition_used_name
        if agent_definition_used_id is not UNSET:
            field_dict["agent_definition_used_id"] = agent_definition_used_id
        if calls_attempted is not UNSET:
            field_dict["calls_attempted"] = calls_attempted
        if calls_connected_percentage is not UNSET:
            field_dict["calls_connected_percentage"] = calls_connected_percentage

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.call_execution import CallExecution
        from ..models.test_execution_execution_metadata import (
            TestExecutionExecutionMetadata,
        )
        from ..models.test_execution_scenario_ids import TestExecutionScenarioIds

        d = dict(src_dict)
        run_test = UUID(d.pop("run_test"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        run_test_name = d.pop("run_test_name", UNSET)

        agent_definition_name = d.pop("agent_definition_name", UNSET)

        _status = d.pop("status", UNSET)
        status: TestExecutionStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = TestExecutionStatus(_status)

        def _parse_error_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_reason = _parse_error_reason(d.pop("error_reason", UNSET))

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

        total_scenarios = d.pop("total_scenarios", UNSET)

        total_calls = d.pop("total_calls", UNSET)

        completed_calls = d.pop("completed_calls", UNSET)

        failed_calls = d.pop("failed_calls", UNSET)

        _execution_metadata = d.pop("execution_metadata", UNSET)
        execution_metadata: TestExecutionExecutionMetadata | Unset
        if isinstance(_execution_metadata, Unset):
            execution_metadata = UNSET
        else:
            execution_metadata = TestExecutionExecutionMetadata.from_dict(
                _execution_metadata
            )

        duration_seconds = d.pop("duration_seconds", UNSET)

        success_rate = d.pop("success_rate", UNSET)

        _calls = d.pop("calls", UNSET)
        calls: list[CallExecution] | Unset = UNSET
        if _calls is not UNSET:
            calls = []
            for calls_item_data in _calls:
                calls_item = CallExecution.from_dict(calls_item_data)

                calls.append(calls_item)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _scenario_ids = d.pop("scenario_ids", UNSET)
        scenario_ids: TestExecutionScenarioIds | Unset
        if isinstance(_scenario_ids, Unset):
            scenario_ids = UNSET
        else:
            scenario_ids = TestExecutionScenarioIds.from_dict(_scenario_ids)

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

        calls_attempted = d.pop("calls_attempted", UNSET)

        calls_connected_percentage = d.pop("calls_connected_percentage", UNSET)

        test_execution = cls(
            run_test=run_test,
            id=id,
            run_test_name=run_test_name,
            agent_definition_name=agent_definition_name,
            status=status,
            error_reason=error_reason,
            started_at=started_at,
            completed_at=completed_at,
            total_scenarios=total_scenarios,
            total_calls=total_calls,
            completed_calls=completed_calls,
            failed_calls=failed_calls,
            execution_metadata=execution_metadata,
            duration_seconds=duration_seconds,
            success_rate=success_rate,
            calls=calls,
            created_at=created_at,
            scenario_ids=scenario_ids,
            simulator_agent_name=simulator_agent_name,
            simulator_agent_id=simulator_agent_id,
            agent_definition_used_name=agent_definition_used_name,
            agent_definition_used_id=agent_definition_used_id,
            calls_attempted=calls_attempted,
            calls_connected_percentage=calls_connected_percentage,
        )

        test_execution.additional_properties = d
        return test_execution

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
