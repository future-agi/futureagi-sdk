from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_comparison_column_metric import (
        ExperimentComparisonColumnMetric,
    )
    from ..models.experiment_comparison_dataset_metric_normalized_scores import (
        ExperimentComparisonDatasetMetricNormalizedScores,
    )


T = TypeVar("T", bound="ExperimentComparisonDatasetMetric")


@_attrs_define
class ExperimentComparisonDatasetMetric:
    """
    Attributes:
        dataset_id (UUID):
        avg_completion_tokens (float | None | Unset):
        avg_total_tokens (float | None | Unset):
        avg_response_time (float | None | Unset):
        avg_score (float | None | Unset):
        columns (list[ExperimentComparisonColumnMetric] | Unset):
        normalized_scores (ExperimentComparisonDatasetMetricNormalizedScores | Unset):
        overall_rating (float | None | Unset):
        rank (int | None | Unset):
        rank_suffix (str | Unset):
        total_datasets (int | Unset):
    """

    dataset_id: UUID
    avg_completion_tokens: float | None | Unset = UNSET
    avg_total_tokens: float | None | Unset = UNSET
    avg_response_time: float | None | Unset = UNSET
    avg_score: float | None | Unset = UNSET
    columns: list[ExperimentComparisonColumnMetric] | Unset = UNSET
    normalized_scores: ExperimentComparisonDatasetMetricNormalizedScores | Unset = UNSET
    overall_rating: float | None | Unset = UNSET
    rank: int | None | Unset = UNSET
    rank_suffix: str | Unset = UNSET
    total_datasets: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = str(self.dataset_id)

        avg_completion_tokens: float | None | Unset
        if isinstance(self.avg_completion_tokens, Unset):
            avg_completion_tokens = UNSET
        else:
            avg_completion_tokens = self.avg_completion_tokens

        avg_total_tokens: float | None | Unset
        if isinstance(self.avg_total_tokens, Unset):
            avg_total_tokens = UNSET
        else:
            avg_total_tokens = self.avg_total_tokens

        avg_response_time: float | None | Unset
        if isinstance(self.avg_response_time, Unset):
            avg_response_time = UNSET
        else:
            avg_response_time = self.avg_response_time

        avg_score: float | None | Unset
        if isinstance(self.avg_score, Unset):
            avg_score = UNSET
        else:
            avg_score = self.avg_score

        columns: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.columns, Unset):
            columns = []
            for columns_item_data in self.columns:
                columns_item = columns_item_data.to_dict()
                columns.append(columns_item)

        normalized_scores: dict[str, Any] | Unset = UNSET
        if not isinstance(self.normalized_scores, Unset):
            normalized_scores = self.normalized_scores.to_dict()

        overall_rating: float | None | Unset
        if isinstance(self.overall_rating, Unset):
            overall_rating = UNSET
        else:
            overall_rating = self.overall_rating

        rank: int | None | Unset
        if isinstance(self.rank, Unset):
            rank = UNSET
        else:
            rank = self.rank

        rank_suffix = self.rank_suffix

        total_datasets = self.total_datasets

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
            }
        )
        if avg_completion_tokens is not UNSET:
            field_dict["avg_completion_tokens"] = avg_completion_tokens
        if avg_total_tokens is not UNSET:
            field_dict["avg_total_tokens"] = avg_total_tokens
        if avg_response_time is not UNSET:
            field_dict["avg_response_time"] = avg_response_time
        if avg_score is not UNSET:
            field_dict["avg_score"] = avg_score
        if columns is not UNSET:
            field_dict["columns"] = columns
        if normalized_scores is not UNSET:
            field_dict["normalized_scores"] = normalized_scores
        if overall_rating is not UNSET:
            field_dict["overall_rating"] = overall_rating
        if rank is not UNSET:
            field_dict["rank"] = rank
        if rank_suffix is not UNSET:
            field_dict["rank_suffix"] = rank_suffix
        if total_datasets is not UNSET:
            field_dict["total_datasets"] = total_datasets

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_comparison_column_metric import (
            ExperimentComparisonColumnMetric,
        )
        from ..models.experiment_comparison_dataset_metric_normalized_scores import (
            ExperimentComparisonDatasetMetricNormalizedScores,
        )

        d = dict(src_dict)
        dataset_id = UUID(d.pop("dataset_id"))

        def _parse_avg_completion_tokens(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_completion_tokens = _parse_avg_completion_tokens(
            d.pop("avg_completion_tokens", UNSET)
        )

        def _parse_avg_total_tokens(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_total_tokens = _parse_avg_total_tokens(d.pop("avg_total_tokens", UNSET))

        def _parse_avg_response_time(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_response_time = _parse_avg_response_time(d.pop("avg_response_time", UNSET))

        def _parse_avg_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_score = _parse_avg_score(d.pop("avg_score", UNSET))

        _columns = d.pop("columns", UNSET)
        columns: list[ExperimentComparisonColumnMetric] | Unset = UNSET
        if _columns is not UNSET:
            columns = []
            for columns_item_data in _columns:
                columns_item = ExperimentComparisonColumnMetric.from_dict(
                    columns_item_data
                )

                columns.append(columns_item)

        _normalized_scores = d.pop("normalized_scores", UNSET)
        normalized_scores: ExperimentComparisonDatasetMetricNormalizedScores | Unset
        if isinstance(_normalized_scores, Unset):
            normalized_scores = UNSET
        else:
            normalized_scores = (
                ExperimentComparisonDatasetMetricNormalizedScores.from_dict(
                    _normalized_scores
                )
            )

        def _parse_overall_rating(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        overall_rating = _parse_overall_rating(d.pop("overall_rating", UNSET))

        def _parse_rank(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        rank = _parse_rank(d.pop("rank", UNSET))

        rank_suffix = d.pop("rank_suffix", UNSET)

        total_datasets = d.pop("total_datasets", UNSET)

        experiment_comparison_dataset_metric = cls(
            dataset_id=dataset_id,
            avg_completion_tokens=avg_completion_tokens,
            avg_total_tokens=avg_total_tokens,
            avg_response_time=avg_response_time,
            avg_score=avg_score,
            columns=columns,
            normalized_scores=normalized_scores,
            overall_rating=overall_rating,
            rank=rank,
            rank_suffix=rank_suffix,
            total_datasets=total_datasets,
        )

        experiment_comparison_dataset_metric.additional_properties = d
        return experiment_comparison_dataset_metric

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
