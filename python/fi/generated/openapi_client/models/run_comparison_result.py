from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.missing_run_items import MissingRunItems
    from ..models.release_gate_report import ReleaseGateReport
    from ..models.run_case_trace_references import RunCaseTraceReferences
    from ..models.run_comparison_summary import RunComparisonSummary
    from ..models.run_counts import RunCounts
    from ..models.trial_stability import TrialStability


T = TypeVar("T", bound="RunComparisonResult")


@_attrs_define
class RunComparisonResult:
    """
    Attributes:
        baseline_run_id (UUID):
        candidate_run_id (UUID):
        dataset_version_id (UUID):
        metric_id (UUID):
        evaluator_version_id (UUID):
        comparison (RunComparisonSummary):
        baseline_counts (RunCounts):
        candidate_counts (RunCounts):
        missing_by_side (MissingRunItems):
        trace_refs (list[RunCaseTraceReferences]):
        release_gate (ReleaseGateReport | Unset):
        trial_stability (list[TrialStability] | Unset):
    """

    baseline_run_id: UUID
    candidate_run_id: UUID
    dataset_version_id: UUID
    metric_id: UUID
    evaluator_version_id: UUID
    comparison: RunComparisonSummary
    baseline_counts: RunCounts
    candidate_counts: RunCounts
    missing_by_side: MissingRunItems
    trace_refs: list[RunCaseTraceReferences]
    release_gate: ReleaseGateReport | Unset = UNSET
    trial_stability: list[TrialStability] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        baseline_run_id = str(self.baseline_run_id)

        candidate_run_id = str(self.candidate_run_id)

        dataset_version_id = str(self.dataset_version_id)

        metric_id = str(self.metric_id)

        evaluator_version_id = str(self.evaluator_version_id)

        comparison = self.comparison.to_dict()

        baseline_counts = self.baseline_counts.to_dict()

        candidate_counts = self.candidate_counts.to_dict()

        missing_by_side = self.missing_by_side.to_dict()

        trace_refs = []
        for trace_refs_item_data in self.trace_refs:
            trace_refs_item = trace_refs_item_data.to_dict()
            trace_refs.append(trace_refs_item)

        release_gate: dict[str, Any] | Unset = UNSET
        if not isinstance(self.release_gate, Unset):
            release_gate = self.release_gate.to_dict()

        trial_stability: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.trial_stability, Unset):
            trial_stability = []
            for trial_stability_item_data in self.trial_stability:
                trial_stability_item = trial_stability_item_data.to_dict()
                trial_stability.append(trial_stability_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "baseline_run_id": baseline_run_id,
                "candidate_run_id": candidate_run_id,
                "dataset_version_id": dataset_version_id,
                "metric_id": metric_id,
                "evaluator_version_id": evaluator_version_id,
                "comparison": comparison,
                "baseline_counts": baseline_counts,
                "candidate_counts": candidate_counts,
                "missing_by_side": missing_by_side,
                "trace_refs": trace_refs,
            }
        )
        if release_gate is not UNSET:
            field_dict["release_gate"] = release_gate
        if trial_stability is not UNSET:
            field_dict["trial_stability"] = trial_stability

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.missing_run_items import MissingRunItems
        from ..models.release_gate_report import ReleaseGateReport
        from ..models.run_case_trace_references import RunCaseTraceReferences
        from ..models.run_comparison_summary import RunComparisonSummary
        from ..models.run_counts import RunCounts
        from ..models.trial_stability import TrialStability

        d = dict(src_dict)
        baseline_run_id = UUID(d.pop("baseline_run_id"))

        candidate_run_id = UUID(d.pop("candidate_run_id"))

        dataset_version_id = UUID(d.pop("dataset_version_id"))

        metric_id = UUID(d.pop("metric_id"))

        evaluator_version_id = UUID(d.pop("evaluator_version_id"))

        comparison = RunComparisonSummary.from_dict(d.pop("comparison"))

        baseline_counts = RunCounts.from_dict(d.pop("baseline_counts"))

        candidate_counts = RunCounts.from_dict(d.pop("candidate_counts"))

        missing_by_side = MissingRunItems.from_dict(d.pop("missing_by_side"))

        trace_refs = []
        _trace_refs = d.pop("trace_refs")
        for trace_refs_item_data in _trace_refs:
            trace_refs_item = RunCaseTraceReferences.from_dict(trace_refs_item_data)

            trace_refs.append(trace_refs_item)

        _release_gate = d.pop("release_gate", UNSET)
        release_gate: ReleaseGateReport | Unset
        if isinstance(_release_gate, Unset):
            release_gate = UNSET
        else:
            release_gate = ReleaseGateReport.from_dict(_release_gate)

        _trial_stability = d.pop("trial_stability", UNSET)
        trial_stability: list[TrialStability] | Unset = UNSET
        if _trial_stability is not UNSET:
            trial_stability = []
            for trial_stability_item_data in _trial_stability:
                trial_stability_item = TrialStability.from_dict(
                    trial_stability_item_data
                )

                trial_stability.append(trial_stability_item)

        run_comparison_result = cls(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            dataset_version_id=dataset_version_id,
            metric_id=metric_id,
            evaluator_version_id=evaluator_version_id,
            comparison=comparison,
            baseline_counts=baseline_counts,
            candidate_counts=candidate_counts,
            missing_by_side=missing_by_side,
            trace_refs=trace_refs,
            release_gate=release_gate,
            trial_stability=trial_stability,
        )

        run_comparison_result.additional_properties = d
        return run_comparison_result

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
