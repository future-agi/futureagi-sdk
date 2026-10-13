from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.run_item_identity import RunItemIdentity


T = TypeVar("T", bound="MissingRunItems")


@_attrs_define
class MissingRunItems:
    """
    Attributes:
        baseline (list[RunItemIdentity]):
        candidate (list[RunItemIdentity]):
    """

    baseline: list[RunItemIdentity]
    candidate: list[RunItemIdentity]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        baseline = []
        for baseline_item_data in self.baseline:
            baseline_item = baseline_item_data.to_dict()
            baseline.append(baseline_item)

        candidate = []
        for candidate_item_data in self.candidate:
            candidate_item = candidate_item_data.to_dict()
            candidate.append(candidate_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "baseline": baseline,
                "candidate": candidate,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_item_identity import RunItemIdentity

        d = dict(src_dict)
        baseline = []
        _baseline = d.pop("baseline")
        for baseline_item_data in _baseline:
            baseline_item = RunItemIdentity.from_dict(baseline_item_data)

            baseline.append(baseline_item)

        candidate = []
        _candidate = d.pop("candidate")
        for candidate_item_data in _candidate:
            candidate_item = RunItemIdentity.from_dict(candidate_item_data)

            candidate.append(candidate_item)

        missing_run_items = cls(
            baseline=baseline,
            candidate=candidate,
        )

        missing_run_items.additional_properties = d
        return missing_run_items

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
