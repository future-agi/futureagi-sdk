from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.run_case_comparison_missing_side import RunCaseComparisonMissingSide
from ..models.run_case_comparison_status import RunCaseComparisonStatus

T = TypeVar("T", bound="RunCaseComparison")


@_attrs_define
class RunCaseComparison:
    """
    Attributes:
        example_id (UUID):
        trial_number (int):
        status (RunCaseComparisonStatus):
        baseline_status (None | str):
        candidate_status (None | str):
        baseline_score (float | None):
        candidate_score (float | None):
        score_delta (float | None):
        missing_side (None | RunCaseComparisonMissingSide):
    """

    example_id: UUID
    trial_number: int
    status: RunCaseComparisonStatus
    baseline_status: None | str
    candidate_status: None | str
    baseline_score: float | None
    candidate_score: float | None
    score_delta: float | None
    missing_side: None | RunCaseComparisonMissingSide
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        example_id = str(self.example_id)

        trial_number = self.trial_number

        status = self.status.value

        baseline_status: None | str
        baseline_status = self.baseline_status

        candidate_status: None | str
        candidate_status = self.candidate_status

        baseline_score: float | None
        baseline_score = self.baseline_score

        candidate_score: float | None
        candidate_score = self.candidate_score

        score_delta: float | None
        score_delta = self.score_delta

        missing_side: None | str
        if isinstance(self.missing_side, RunCaseComparisonMissingSide):
            missing_side = self.missing_side.value
        else:
            missing_side = self.missing_side

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "example_id": example_id,
                "trial_number": trial_number,
                "status": status,
                "baseline_status": baseline_status,
                "candidate_status": candidate_status,
                "baseline_score": baseline_score,
                "candidate_score": candidate_score,
                "score_delta": score_delta,
                "missing_side": missing_side,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        example_id = UUID(d.pop("example_id"))

        trial_number = d.pop("trial_number")

        status = RunCaseComparisonStatus(d.pop("status"))

        def _parse_baseline_status(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        baseline_status = _parse_baseline_status(d.pop("baseline_status"))

        def _parse_candidate_status(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        candidate_status = _parse_candidate_status(d.pop("candidate_status"))

        def _parse_baseline_score(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        baseline_score = _parse_baseline_score(d.pop("baseline_score"))

        def _parse_candidate_score(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        candidate_score = _parse_candidate_score(d.pop("candidate_score"))

        def _parse_score_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        score_delta = _parse_score_delta(d.pop("score_delta"))

        def _parse_missing_side(data: object) -> None | RunCaseComparisonMissingSide:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                missing_side_type_1 = RunCaseComparisonMissingSide(data)

                return missing_side_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunCaseComparisonMissingSide, data)

        missing_side = _parse_missing_side(d.pop("missing_side"))

        run_case_comparison = cls(
            example_id=example_id,
            trial_number=trial_number,
            status=status,
            baseline_status=baseline_status,
            candidate_status=candidate_status,
            baseline_score=baseline_score,
            candidate_score=candidate_score,
            score_delta=score_delta,
            missing_side=missing_side,
        )

        run_case_comparison.additional_properties = d
        return run_case_comparison

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
