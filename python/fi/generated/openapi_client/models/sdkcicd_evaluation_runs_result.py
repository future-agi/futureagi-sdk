from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.sdkcicd_evaluation_runs_result_status import (
    SDKCICDEvaluationRunsResultStatus,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sdkcicd_evaluation_run_summary import SDKCICDEvaluationRunSummary


T = TypeVar("T", bound="SDKCICDEvaluationRunsResult")


@_attrs_define
class SDKCICDEvaluationRunsResult:
    """
    Attributes:
        message (str):
        status (SDKCICDEvaluationRunsResultStatus):
        evaluation_runs (list[SDKCICDEvaluationRunSummary] | Unset):
    """

    message: str
    status: SDKCICDEvaluationRunsResultStatus
    evaluation_runs: list[SDKCICDEvaluationRunSummary] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        status = self.status.value

        evaluation_runs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.evaluation_runs, Unset):
            evaluation_runs = []
            for evaluation_runs_item_data in self.evaluation_runs:
                evaluation_runs_item = evaluation_runs_item_data.to_dict()
                evaluation_runs.append(evaluation_runs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "status": status,
            }
        )
        if evaluation_runs is not UNSET:
            field_dict["evaluation_runs"] = evaluation_runs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdkcicd_evaluation_run_summary import SDKCICDEvaluationRunSummary

        d = dict(src_dict)
        message = d.pop("message")

        status = SDKCICDEvaluationRunsResultStatus(d.pop("status"))

        _evaluation_runs = d.pop("evaluation_runs", UNSET)
        evaluation_runs: list[SDKCICDEvaluationRunSummary] | Unset = UNSET
        if _evaluation_runs is not UNSET:
            evaluation_runs = []
            for evaluation_runs_item_data in _evaluation_runs:
                evaluation_runs_item = SDKCICDEvaluationRunSummary.from_dict(
                    evaluation_runs_item_data
                )

                evaluation_runs.append(evaluation_runs_item)

        sdkcicd_evaluation_runs_result = cls(
            message=message,
            status=status,
            evaluation_runs=evaluation_runs,
        )

        sdkcicd_evaluation_runs_result.additional_properties = d
        return sdkcicd_evaluation_runs_result

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
