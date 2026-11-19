from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_comparison_dataset_metric import (
        ExperimentComparisonDatasetMetric,
    )
    from ..models.experiment_dataset_comparison_result_weights_applied import (
        ExperimentDatasetComparisonResultWeightsApplied,
    )


T = TypeVar("T", bound="ExperimentDatasetComparisonResult")


@_attrs_define
class ExperimentDatasetComparisonResult:
    """
    Attributes:
        experiment_id (UUID):
        experiment_name (str):
        total_datasets (int):
        dataset_comparisons (list[ExperimentComparisonDatasetMetric]):
        weights_applied (ExperimentDatasetComparisonResultWeightsApplied | Unset):
    """

    experiment_id: UUID
    experiment_name: str
    total_datasets: int
    dataset_comparisons: list[ExperimentComparisonDatasetMetric]
    weights_applied: ExperimentDatasetComparisonResultWeightsApplied | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        experiment_id = str(self.experiment_id)

        experiment_name = self.experiment_name

        total_datasets = self.total_datasets

        dataset_comparisons = []
        for dataset_comparisons_item_data in self.dataset_comparisons:
            dataset_comparisons_item = dataset_comparisons_item_data.to_dict()
            dataset_comparisons.append(dataset_comparisons_item)

        weights_applied: dict[str, Any] | Unset = UNSET
        if not isinstance(self.weights_applied, Unset):
            weights_applied = self.weights_applied.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "experiment_id": experiment_id,
                "experiment_name": experiment_name,
                "total_datasets": total_datasets,
                "dataset_comparisons": dataset_comparisons,
            }
        )
        if weights_applied is not UNSET:
            field_dict["weights_applied"] = weights_applied

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_comparison_dataset_metric import (
            ExperimentComparisonDatasetMetric,
        )
        from ..models.experiment_dataset_comparison_result_weights_applied import (
            ExperimentDatasetComparisonResultWeightsApplied,
        )

        d = dict(src_dict)
        experiment_id = UUID(d.pop("experiment_id"))

        experiment_name = d.pop("experiment_name")

        total_datasets = d.pop("total_datasets")

        dataset_comparisons = []
        _dataset_comparisons = d.pop("dataset_comparisons")
        for dataset_comparisons_item_data in _dataset_comparisons:
            dataset_comparisons_item = ExperimentComparisonDatasetMetric.from_dict(
                dataset_comparisons_item_data
            )

            dataset_comparisons.append(dataset_comparisons_item)

        _weights_applied = d.pop("weights_applied", UNSET)
        weights_applied: ExperimentDatasetComparisonResultWeightsApplied | Unset
        if isinstance(_weights_applied, Unset):
            weights_applied = UNSET
        else:
            weights_applied = ExperimentDatasetComparisonResultWeightsApplied.from_dict(
                _weights_applied
            )

        experiment_dataset_comparison_result = cls(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            total_datasets=total_datasets,
            dataset_comparisons=dataset_comparisons,
            weights_applied=weights_applied,
        )

        experiment_dataset_comparison_result.additional_properties = d
        return experiment_dataset_comparison_result

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
