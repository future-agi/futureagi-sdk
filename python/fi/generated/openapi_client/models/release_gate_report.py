from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.release_gate_report_verdict import ReleaseGateReportVerdict

if TYPE_CHECKING:
    from ..models.release_gate_blocker import ReleaseGateBlocker
    from ..models.release_gate_policy import ReleaseGatePolicy


T = TypeVar("T", bound="ReleaseGateReport")


@_attrs_define
class ReleaseGateReport:
    """
    Attributes:
        verdict (ReleaseGateReportVerdict):
        expected_count (int):
        comparable_count (int):
        regression_count (int):
        policy (ReleaseGatePolicy):
        passing_score (float | None):
        higher_is_better (bool):
        blockers (list[ReleaseGateBlocker]):
    """

    verdict: ReleaseGateReportVerdict
    expected_count: int
    comparable_count: int
    regression_count: int
    policy: ReleaseGatePolicy
    passing_score: float | None
    higher_is_better: bool
    blockers: list[ReleaseGateBlocker]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        verdict = self.verdict.value

        expected_count = self.expected_count

        comparable_count = self.comparable_count

        regression_count = self.regression_count

        policy = self.policy.to_dict()

        passing_score: float | None
        passing_score = self.passing_score

        higher_is_better = self.higher_is_better

        blockers = []
        for blockers_item_data in self.blockers:
            blockers_item = blockers_item_data.to_dict()
            blockers.append(blockers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "verdict": verdict,
                "expected_count": expected_count,
                "comparable_count": comparable_count,
                "regression_count": regression_count,
                "policy": policy,
                "passing_score": passing_score,
                "higher_is_better": higher_is_better,
                "blockers": blockers,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.release_gate_blocker import ReleaseGateBlocker
        from ..models.release_gate_policy import ReleaseGatePolicy

        d = dict(src_dict)
        verdict = ReleaseGateReportVerdict(d.pop("verdict"))

        expected_count = d.pop("expected_count")

        comparable_count = d.pop("comparable_count")

        regression_count = d.pop("regression_count")

        policy = ReleaseGatePolicy.from_dict(d.pop("policy"))

        def _parse_passing_score(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        passing_score = _parse_passing_score(d.pop("passing_score"))

        higher_is_better = d.pop("higher_is_better")

        blockers = []
        _blockers = d.pop("blockers")
        for blockers_item_data in _blockers:
            blockers_item = ReleaseGateBlocker.from_dict(blockers_item_data)

            blockers.append(blockers_item)

        release_gate_report = cls(
            verdict=verdict,
            expected_count=expected_count,
            comparable_count=comparable_count,
            regression_count=regression_count,
            policy=policy,
            passing_score=passing_score,
            higher_is_better=higher_is_better,
            blockers=blockers,
        )

        release_gate_report.additional_properties = d
        return release_gate_report

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
