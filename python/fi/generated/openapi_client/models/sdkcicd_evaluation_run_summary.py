from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.sdkcicd_evaluation_run_summary_results_summary import (
        SDKCICDEvaluationRunSummaryResultsSummary,
    )


T = TypeVar("T", bound="SDKCICDEvaluationRunSummary")


@_attrs_define
class SDKCICDEvaluationRunSummary:
    """
    Attributes:
        id (UUID):
        project (str):
        version (str):
        results_summary (SDKCICDEvaluationRunSummaryResultsSummary):
    """

    id: UUID
    project: str
    version: str
    results_summary: SDKCICDEvaluationRunSummaryResultsSummary
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        project = self.project

        version = self.version

        results_summary = self.results_summary.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project": project,
                "version": version,
                "results_summary": results_summary,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdkcicd_evaluation_run_summary_results_summary import (
            SDKCICDEvaluationRunSummaryResultsSummary,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        project = d.pop("project")

        version = d.pop("version")

        results_summary = SDKCICDEvaluationRunSummaryResultsSummary.from_dict(
            d.pop("results_summary")
        )

        sdkcicd_evaluation_run_summary = cls(
            id=id,
            project=project,
            version=version,
            results_summary=results_summary,
        )

        sdkcicd_evaluation_run_summary.additional_properties = d
        return sdkcicd_evaluation_run_summary

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
