from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_comparison_detail_scores_weight import (
        ExperimentComparisonDetailScoresWeight,
    )
    from ..models.experiment_comparison_metrics import ExperimentComparisonMetrics
    from ..models.experiment_comparison_weights import ExperimentComparisonWeights


T = TypeVar("T", bound="ExperimentComparisonDetail")


@_attrs_define
class ExperimentComparisonDetail:
    """
    Attributes:
        metrics (ExperimentComparisonMetrics):
        weights (ExperimentComparisonWeights):
        scores_weight (ExperimentComparisonDetailScoresWeight | Unset):
        experiment_dataset_id (None | Unset | UUID):
        rank (int | None | Unset):
        rank_suffix (str | Unset):
        overall_rating (float | None | Unset):
    """

    metrics: ExperimentComparisonMetrics
    weights: ExperimentComparisonWeights
    scores_weight: ExperimentComparisonDetailScoresWeight | Unset = UNSET
    experiment_dataset_id: None | Unset | UUID = UNSET
    rank: int | None | Unset = UNSET
    rank_suffix: str | Unset = UNSET
    overall_rating: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metrics = self.metrics.to_dict()

        weights = self.weights.to_dict()

        scores_weight: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scores_weight, Unset):
            scores_weight = self.scores_weight.to_dict()

        experiment_dataset_id: None | str | Unset
        if isinstance(self.experiment_dataset_id, Unset):
            experiment_dataset_id = UNSET
        elif isinstance(self.experiment_dataset_id, UUID):
            experiment_dataset_id = str(self.experiment_dataset_id)
        else:
            experiment_dataset_id = self.experiment_dataset_id

        rank: int | None | Unset
        if isinstance(self.rank, Unset):
            rank = UNSET
        else:
            rank = self.rank

        rank_suffix = self.rank_suffix

        overall_rating: float | None | Unset
        if isinstance(self.overall_rating, Unset):
            overall_rating = UNSET
        else:
            overall_rating = self.overall_rating

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metrics": metrics,
                "weights": weights,
            }
        )
        if scores_weight is not UNSET:
            field_dict["scores_weight"] = scores_weight
        if experiment_dataset_id is not UNSET:
            field_dict["experiment_dataset_id"] = experiment_dataset_id
        if rank is not UNSET:
            field_dict["rank"] = rank
        if rank_suffix is not UNSET:
            field_dict["rank_suffix"] = rank_suffix
        if overall_rating is not UNSET:
            field_dict["overall_rating"] = overall_rating

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_comparison_detail_scores_weight import (
            ExperimentComparisonDetailScoresWeight,
        )
        from ..models.experiment_comparison_metrics import ExperimentComparisonMetrics
        from ..models.experiment_comparison_weights import ExperimentComparisonWeights

        d = dict(src_dict)
        metrics = ExperimentComparisonMetrics.from_dict(d.pop("metrics"))

        weights = ExperimentComparisonWeights.from_dict(d.pop("weights"))

        _scores_weight = d.pop("scores_weight", UNSET)
        scores_weight: ExperimentComparisonDetailScoresWeight | Unset
        if isinstance(_scores_weight, Unset):
            scores_weight = UNSET
        else:
            scores_weight = ExperimentComparisonDetailScoresWeight.from_dict(
                _scores_weight
            )

        def _parse_experiment_dataset_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                experiment_dataset_id_type_0 = UUID(data)

                return experiment_dataset_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        experiment_dataset_id = _parse_experiment_dataset_id(
            d.pop("experiment_dataset_id", UNSET)
        )

        def _parse_rank(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        rank = _parse_rank(d.pop("rank", UNSET))

        rank_suffix = d.pop("rank_suffix", UNSET)

        def _parse_overall_rating(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        overall_rating = _parse_overall_rating(d.pop("overall_rating", UNSET))

        experiment_comparison_detail = cls(
            metrics=metrics,
            weights=weights,
            scores_weight=scores_weight,
            experiment_dataset_id=experiment_dataset_id,
            rank=rank,
            rank_suffix=rank_suffix,
            overall_rating=overall_rating,
        )

        experiment_comparison_detail.additional_properties = d
        return experiment_comparison_detail

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
