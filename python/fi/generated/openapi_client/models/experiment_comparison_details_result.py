from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.experiment_comparison_detail import ExperimentComparisonDetail


T = TypeVar("T", bound="ExperimentComparisonDetailsResult")


@_attrs_define
class ExperimentComparisonDetailsResult:
    """
    Attributes:
        experiment_id (UUID):
        total_comparisons (int):
        comparisons (list[ExperimentComparisonDetail]):
    """

    experiment_id: UUID
    total_comparisons: int
    comparisons: list[ExperimentComparisonDetail]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        experiment_id = str(self.experiment_id)

        total_comparisons = self.total_comparisons

        comparisons = []
        for comparisons_item_data in self.comparisons:
            comparisons_item = comparisons_item_data.to_dict()
            comparisons.append(comparisons_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "experiment_id": experiment_id,
                "total_comparisons": total_comparisons,
                "comparisons": comparisons,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_comparison_detail import ExperimentComparisonDetail

        d = dict(src_dict)
        experiment_id = UUID(d.pop("experiment_id"))

        total_comparisons = d.pop("total_comparisons")

        comparisons = []
        _comparisons = d.pop("comparisons")
        for comparisons_item_data in _comparisons:
            comparisons_item = ExperimentComparisonDetail.from_dict(
                comparisons_item_data
            )

            comparisons.append(comparisons_item)

        experiment_comparison_details_result = cls(
            experiment_id=experiment_id,
            total_comparisons=total_comparisons,
            comparisons=comparisons,
        )

        experiment_comparison_details_result.additional_properties = d
        return experiment_comparison_details_result

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
