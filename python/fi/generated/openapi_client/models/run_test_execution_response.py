from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RunTestExecutionResponse")


@_attrs_define
class RunTestExecutionResponse:
    """
    Attributes:
        message (str | Unset):
        execution_id (UUID | Unset):
        run_test_id (UUID | Unset):
        status (str | Unset):
        total_scenarios (int | Unset):
        total_calls (int | Unset):
        scenario_ids (list[UUID] | Unset):
    """

    message: str | Unset = UNSET
    execution_id: UUID | Unset = UNSET
    run_test_id: UUID | Unset = UNSET
    status: str | Unset = UNSET
    total_scenarios: int | Unset = UNSET
    total_calls: int | Unset = UNSET
    scenario_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        execution_id: str | Unset = UNSET
        if not isinstance(self.execution_id, Unset):
            execution_id = str(self.execution_id)

        run_test_id: str | Unset = UNSET
        if not isinstance(self.run_test_id, Unset):
            run_test_id = str(self.run_test_id)

        status = self.status

        total_scenarios = self.total_scenarios

        total_calls = self.total_calls

        scenario_ids: list[str] | Unset = UNSET
        if not isinstance(self.scenario_ids, Unset):
            scenario_ids = []
            for scenario_ids_item_data in self.scenario_ids:
                scenario_ids_item = str(scenario_ids_item_data)
                scenario_ids.append(scenario_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if execution_id is not UNSET:
            field_dict["execution_id"] = execution_id
        if run_test_id is not UNSET:
            field_dict["run_test_id"] = run_test_id
        if status is not UNSET:
            field_dict["status"] = status
        if total_scenarios is not UNSET:
            field_dict["total_scenarios"] = total_scenarios
        if total_calls is not UNSET:
            field_dict["total_calls"] = total_calls
        if scenario_ids is not UNSET:
            field_dict["scenario_ids"] = scenario_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _execution_id = d.pop("execution_id", UNSET)
        execution_id: UUID | Unset
        if isinstance(_execution_id, Unset):
            execution_id = UNSET
        else:
            execution_id = UUID(_execution_id)

        _run_test_id = d.pop("run_test_id", UNSET)
        run_test_id: UUID | Unset
        if isinstance(_run_test_id, Unset):
            run_test_id = UNSET
        else:
            run_test_id = UUID(_run_test_id)

        status = d.pop("status", UNSET)

        total_scenarios = d.pop("total_scenarios", UNSET)

        total_calls = d.pop("total_calls", UNSET)

        _scenario_ids = d.pop("scenario_ids", UNSET)
        scenario_ids: list[UUID] | Unset = UNSET
        if _scenario_ids is not UNSET:
            scenario_ids = []
            for scenario_ids_item_data in _scenario_ids:
                scenario_ids_item = UUID(scenario_ids_item_data)

                scenario_ids.append(scenario_ids_item)

        run_test_execution_response = cls(
            message=message,
            execution_id=execution_id,
            run_test_id=run_test_id,
            status=status,
            total_scenarios=total_scenarios,
            total_calls=total_calls,
            scenario_ids=scenario_ids,
        )

        run_test_execution_response.additional_properties = d
        return run_test_execution_response

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
