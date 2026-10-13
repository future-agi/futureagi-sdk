from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_evaluation_column_stats_avg_score import (
        ExperimentEvaluationColumnStatsAvgScore,
    )
    from ..models.experiment_evaluation_token_usage import (
        ExperimentEvaluationTokenUsage,
    )


T = TypeVar("T", bound="ExperimentEvaluationColumnStats")


@_attrs_define
class ExperimentEvaluationColumnStats:
    """
    Attributes:
        column_name (str):
        column_id (UUID):
        total_rows (int):
        success_rate (float):
        avg_response_time (float):
        token_usage (ExperimentEvaluationTokenUsage):
        avg_score (ExperimentEvaluationColumnStatsAvgScore | Unset):
    """

    column_name: str
    column_id: UUID
    total_rows: int
    success_rate: float
    avg_response_time: float
    token_usage: ExperimentEvaluationTokenUsage
    avg_score: ExperimentEvaluationColumnStatsAvgScore | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        column_name = self.column_name

        column_id = str(self.column_id)

        total_rows = self.total_rows

        success_rate = self.success_rate

        avg_response_time = self.avg_response_time

        token_usage = self.token_usage.to_dict()

        avg_score: dict[str, Any] | Unset = UNSET
        if not isinstance(self.avg_score, Unset):
            avg_score = self.avg_score.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "column_name": column_name,
                "column_id": column_id,
                "total_rows": total_rows,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "token_usage": token_usage,
            }
        )
        if avg_score is not UNSET:
            field_dict["avg_score"] = avg_score

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_evaluation_column_stats_avg_score import (
            ExperimentEvaluationColumnStatsAvgScore,
        )
        from ..models.experiment_evaluation_token_usage import (
            ExperimentEvaluationTokenUsage,
        )

        d = dict(src_dict)
        column_name = d.pop("column_name")

        column_id = UUID(d.pop("column_id"))

        total_rows = d.pop("total_rows")

        success_rate = d.pop("success_rate")

        avg_response_time = d.pop("avg_response_time")

        token_usage = ExperimentEvaluationTokenUsage.from_dict(d.pop("token_usage"))

        _avg_score = d.pop("avg_score", UNSET)
        avg_score: ExperimentEvaluationColumnStatsAvgScore | Unset
        if isinstance(_avg_score, Unset):
            avg_score = UNSET
        else:
            avg_score = ExperimentEvaluationColumnStatsAvgScore.from_dict(_avg_score)

        experiment_evaluation_column_stats = cls(
            column_name=column_name,
            column_id=column_id,
            total_rows=total_rows,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            token_usage=token_usage,
            avg_score=avg_score,
        )

        experiment_evaluation_column_stats.additional_properties = d
        return experiment_evaluation_column_stats

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
