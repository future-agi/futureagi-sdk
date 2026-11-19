from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.output_diff_comparison import OutputDiffComparison
    from ..models.output_diff_side import OutputDiffSide


T = TypeVar("T", bound="CaseOutputDiff")


@_attrs_define
class CaseOutputDiff:
    """
    Attributes:
        example_id (UUID):
        trial_number (int):
        baseline (OutputDiffSide):
        candidate (OutputDiffSide):
        output_comparison (OutputDiffComparison):
    """

    example_id: UUID
    trial_number: int
    baseline: OutputDiffSide
    candidate: OutputDiffSide
    output_comparison: OutputDiffComparison
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        example_id = str(self.example_id)

        trial_number = self.trial_number

        baseline = self.baseline.to_dict()

        candidate = self.candidate.to_dict()

        output_comparison = self.output_comparison.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "example_id": example_id,
                "trial_number": trial_number,
                "baseline": baseline,
                "candidate": candidate,
                "output_comparison": output_comparison,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.output_diff_comparison import OutputDiffComparison
        from ..models.output_diff_side import OutputDiffSide

        d = dict(src_dict)
        example_id = UUID(d.pop("example_id"))

        trial_number = d.pop("trial_number")

        baseline = OutputDiffSide.from_dict(d.pop("baseline"))

        candidate = OutputDiffSide.from_dict(d.pop("candidate"))

        output_comparison = OutputDiffComparison.from_dict(d.pop("output_comparison"))

        case_output_diff = cls(
            example_id=example_id,
            trial_number=trial_number,
            baseline=baseline,
            candidate=candidate,
            output_comparison=output_comparison,
        )

        case_output_diff.additional_properties = d
        return case_output_diff

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
