from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.test_execution_rerun_result import TestExecutionRerunResult


T = TypeVar("T", bound="TestExecutionRerunResponse")


@_attrs_define
class TestExecutionRerunResponse:
    """
    Attributes:
        message (str | Unset):
        run_test_id (UUID | Unset):
        rerun_type (str | Unset):
        total_test_executions (int | Unset):
        results (list[TestExecutionRerunResult] | Unset):
        overall_success_count (int | Unset):
        overall_failure_count (int | Unset):
    """

    message: str | Unset = UNSET
    run_test_id: UUID | Unset = UNSET
    rerun_type: str | Unset = UNSET
    total_test_executions: int | Unset = UNSET
    results: list[TestExecutionRerunResult] | Unset = UNSET
    overall_success_count: int | Unset = UNSET
    overall_failure_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        run_test_id: str | Unset = UNSET
        if not isinstance(self.run_test_id, Unset):
            run_test_id = str(self.run_test_id)

        rerun_type = self.rerun_type

        total_test_executions = self.total_test_executions

        results: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.results, Unset):
            results = []
            for results_item_data in self.results:
                results_item = results_item_data.to_dict()
                results.append(results_item)

        overall_success_count = self.overall_success_count

        overall_failure_count = self.overall_failure_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if run_test_id is not UNSET:
            field_dict["run_test_id"] = run_test_id
        if rerun_type is not UNSET:
            field_dict["rerun_type"] = rerun_type
        if total_test_executions is not UNSET:
            field_dict["total_test_executions"] = total_test_executions
        if results is not UNSET:
            field_dict["results"] = results
        if overall_success_count is not UNSET:
            field_dict["overall_success_count"] = overall_success_count
        if overall_failure_count is not UNSET:
            field_dict["overall_failure_count"] = overall_failure_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.test_execution_rerun_result import TestExecutionRerunResult

        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _run_test_id = d.pop("run_test_id", UNSET)
        run_test_id: UUID | Unset
        if isinstance(_run_test_id, Unset):
            run_test_id = UNSET
        else:
            run_test_id = UUID(_run_test_id)

        rerun_type = d.pop("rerun_type", UNSET)

        total_test_executions = d.pop("total_test_executions", UNSET)

        _results = d.pop("results", UNSET)
        results: list[TestExecutionRerunResult] | Unset = UNSET
        if _results is not UNSET:
            results = []
            for results_item_data in _results:
                results_item = TestExecutionRerunResult.from_dict(results_item_data)

                results.append(results_item)

        overall_success_count = d.pop("overall_success_count", UNSET)

        overall_failure_count = d.pop("overall_failure_count", UNSET)

        test_execution_rerun_response = cls(
            message=message,
            run_test_id=run_test_id,
            rerun_type=rerun_type,
            total_test_executions=total_test_executions,
            results=results,
            overall_success_count=overall_success_count,
            overall_failure_count=overall_failure_count,
        )

        test_execution_rerun_response.additional_properties = d
        return test_execution_rerun_response

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
