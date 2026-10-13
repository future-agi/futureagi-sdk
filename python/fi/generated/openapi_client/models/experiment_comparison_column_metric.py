from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_comparison_column_metric_avg_score import (
        ExperimentComparisonColumnMetricAvgScore,
    )


T = TypeVar("T", bound="ExperimentComparisonColumnMetric")


@_attrs_define
class ExperimentComparisonColumnMetric:
    """
    Attributes:
        column_id (UUID):
        column_name (str):
        avg_completion_tokens (float):
        avg_total_tokens (float):
        avg_response_time (float):
        avg_score (ExperimentComparisonColumnMetricAvgScore | Unset):
    """

    column_id: UUID
    column_name: str
    avg_completion_tokens: float
    avg_total_tokens: float
    avg_response_time: float
    avg_score: ExperimentComparisonColumnMetricAvgScore | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_id = str(self.column_id)

        column_name = self.column_name

        avg_completion_tokens = self.avg_completion_tokens

        avg_total_tokens = self.avg_total_tokens

        avg_response_time = self.avg_response_time

        avg_score: dict[str, Any] | Unset = UNSET
        if not isinstance(self.avg_score, Unset):
            avg_score = self.avg_score.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_id": column_id,
                "column_name": column_name,
                "avg_completion_tokens": avg_completion_tokens,
                "avg_total_tokens": avg_total_tokens,
                "avg_response_time": avg_response_time,
            }
        )
        if avg_score is not UNSET:
            field_dict["avg_score"] = avg_score

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_comparison_column_metric_avg_score import (
            ExperimentComparisonColumnMetricAvgScore,
        )

        d = dict(src_dict)
        column_id = UUID(d.pop("column_id"))

        column_name = d.pop("column_name")

        avg_completion_tokens = d.pop("avg_completion_tokens")

        avg_total_tokens = d.pop("avg_total_tokens")

        avg_response_time = d.pop("avg_response_time")

        _avg_score = d.pop("avg_score", UNSET)
        avg_score: ExperimentComparisonColumnMetricAvgScore | Unset
        if isinstance(_avg_score, Unset):
            avg_score = UNSET
        else:
            avg_score = ExperimentComparisonColumnMetricAvgScore.from_dict(_avg_score)

        experiment_comparison_column_metric = cls(
            column_id=column_id,
            column_name=column_name,
            avg_completion_tokens=avg_completion_tokens,
            avg_total_tokens=avg_total_tokens,
            avg_response_time=avg_response_time,
            avg_score=avg_score,
        )

        experiment_comparison_column_metric.additional_properties = d
        return experiment_comparison_column_metric

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
