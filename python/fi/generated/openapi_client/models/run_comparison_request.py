from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.release_gate_policy import ReleaseGatePolicy


T = TypeVar("T", bound="RunComparisonRequest")


@_attrs_define
class RunComparisonRequest:
    """
    Attributes:
        baseline_run_id (UUID):
        candidate_run_id (UUID):
        metric_id (UUID):
        passing_score (float | None | Unset):
        higher_is_better (bool | Unset):  Default: True.
        release_gate (ReleaseGatePolicy | Unset):
        include_trial_stability (bool | Unset):  Default: False.
    """

    baseline_run_id: UUID
    candidate_run_id: UUID
    metric_id: UUID
    passing_score: float | None | Unset = UNSET
    higher_is_better: bool | Unset = True
    release_gate: ReleaseGatePolicy | Unset = UNSET
    include_trial_stability: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        baseline_run_id = str(self.baseline_run_id)

        candidate_run_id = str(self.candidate_run_id)

        metric_id = str(self.metric_id)

        passing_score: float | None | Unset
        if isinstance(self.passing_score, Unset):
            passing_score = UNSET
        else:
            passing_score = self.passing_score

        higher_is_better = self.higher_is_better

        release_gate: dict[str, Any] | Unset = UNSET
        if not isinstance(self.release_gate, Unset):
            release_gate = self.release_gate.to_dict()

        include_trial_stability = self.include_trial_stability

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "baseline_run_id": baseline_run_id,
                "candidate_run_id": candidate_run_id,
                "metric_id": metric_id,
            }
        )
        if passing_score is not UNSET:
            field_dict["passing_score"] = passing_score
        if higher_is_better is not UNSET:
            field_dict["higher_is_better"] = higher_is_better
        if release_gate is not UNSET:
            field_dict["release_gate"] = release_gate
        if include_trial_stability is not UNSET:
            field_dict["include_trial_stability"] = include_trial_stability

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.release_gate_policy import ReleaseGatePolicy

        d = dict(src_dict)
        baseline_run_id = UUID(d.pop("baseline_run_id"))

        candidate_run_id = UUID(d.pop("candidate_run_id"))

        metric_id = UUID(d.pop("metric_id"))

        def _parse_passing_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        passing_score = _parse_passing_score(d.pop("passing_score", UNSET))

        higher_is_better = d.pop("higher_is_better", UNSET)

        _release_gate = d.pop("release_gate", UNSET)
        release_gate: ReleaseGatePolicy | Unset
        if isinstance(_release_gate, Unset):
            release_gate = UNSET
        else:
            release_gate = ReleaseGatePolicy.from_dict(_release_gate)

        include_trial_stability = d.pop("include_trial_stability", UNSET)

        run_comparison_request = cls(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            metric_id=metric_id,
            passing_score=passing_score,
            higher_is_better=higher_is_better,
            release_gate=release_gate,
            include_trial_stability=include_trial_stability,
        )

        run_comparison_request.additional_properties = d
        return run_comparison_request

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
