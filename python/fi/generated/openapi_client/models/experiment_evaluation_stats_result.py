from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.experiment_evaluation_column_stats import (
        ExperimentEvaluationColumnStats,
    )


T = TypeVar("T", bound="ExperimentEvaluationStatsResult")


@_attrs_define
class ExperimentEvaluationStatsResult:
    """
    Attributes:
        experiment_id (UUID):
        experiment_name (str):
        evaluation_id (UUID):
        evaluation_name (str):
        evaluation_template_id (UUID):
        dataset_id (UUID):
        dataset_name (str):
        evaluation_columns (list[ExperimentEvaluationColumnStats]):
    """

    experiment_id: UUID
    experiment_name: str
    evaluation_id: UUID
    evaluation_name: str
    evaluation_template_id: UUID
    dataset_id: UUID
    dataset_name: str
    evaluation_columns: list[ExperimentEvaluationColumnStats]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        experiment_id = str(self.experiment_id)

        experiment_name = self.experiment_name

        evaluation_id = str(self.evaluation_id)

        evaluation_name = self.evaluation_name

        evaluation_template_id = str(self.evaluation_template_id)

        dataset_id = str(self.dataset_id)

        dataset_name = self.dataset_name

        evaluation_columns = []
        for evaluation_columns_item_data in self.evaluation_columns:
            evaluation_columns_item = evaluation_columns_item_data.to_dict()
            evaluation_columns.append(evaluation_columns_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "experiment_id": experiment_id,
                "experiment_name": experiment_name,
                "evaluation_id": evaluation_id,
                "evaluation_name": evaluation_name,
                "evaluation_template_id": evaluation_template_id,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "evaluation_columns": evaluation_columns,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_evaluation_column_stats import (
            ExperimentEvaluationColumnStats,
        )

        d = dict(src_dict)
        experiment_id = UUID(d.pop("experiment_id"))

        experiment_name = d.pop("experiment_name")

        evaluation_id = UUID(d.pop("evaluation_id"))

        evaluation_name = d.pop("evaluation_name")

        evaluation_template_id = UUID(d.pop("evaluation_template_id"))

        dataset_id = UUID(d.pop("dataset_id"))

        dataset_name = d.pop("dataset_name")

        evaluation_columns = []
        _evaluation_columns = d.pop("evaluation_columns")
        for evaluation_columns_item_data in _evaluation_columns:
            evaluation_columns_item = ExperimentEvaluationColumnStats.from_dict(
                evaluation_columns_item_data
            )

            evaluation_columns.append(evaluation_columns_item)

        experiment_evaluation_stats_result = cls(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            evaluation_id=evaluation_id,
            evaluation_name=evaluation_name,
            evaluation_template_id=evaluation_template_id,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            evaluation_columns=evaluation_columns,
        )

        experiment_evaluation_stats_result.additional_properties = d
        return experiment_evaluation_stats_result

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
