from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.trial_aggregate import TrialAggregate
    from ..models.trial_delta_aggregate import TrialDeltaAggregate


T = TypeVar("T", bound="TrialStability")


@_attrs_define
class TrialStability:
    """
    Attributes:
        example_id (UUID):
        expected_trial_count (int):
        baseline (TrialAggregate):
        candidate (TrialAggregate):
        paired (TrialDeltaAggregate):
    """

    example_id: UUID
    expected_trial_count: int
    baseline: TrialAggregate
    candidate: TrialAggregate
    paired: TrialDeltaAggregate
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        example_id = str(self.example_id)

        expected_trial_count = self.expected_trial_count

        baseline = self.baseline.to_dict()

        candidate = self.candidate.to_dict()

        paired = self.paired.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "example_id": example_id,
                "expected_trial_count": expected_trial_count,
                "baseline": baseline,
                "candidate": candidate,
                "paired": paired,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trial_aggregate import TrialAggregate
        from ..models.trial_delta_aggregate import TrialDeltaAggregate

        d = dict(src_dict)
        example_id = UUID(d.pop("example_id"))

        expected_trial_count = d.pop("expected_trial_count")

        baseline = TrialAggregate.from_dict(d.pop("baseline"))

        candidate = TrialAggregate.from_dict(d.pop("candidate"))

        paired = TrialDeltaAggregate.from_dict(d.pop("paired"))

        trial_stability = cls(
            example_id=example_id,
            expected_trial_count=expected_trial_count,
            baseline=baseline,
            candidate=candidate,
            paired=paired,
        )

        trial_stability.additional_properties = d
        return trial_stability

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
