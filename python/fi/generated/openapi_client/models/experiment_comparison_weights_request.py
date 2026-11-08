from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_comparison_weights_request_weights import (
        ExperimentComparisonWeightsRequestWeights,
    )


T = TypeVar("T", bound="ExperimentComparisonWeightsRequest")


@_attrs_define
class ExperimentComparisonWeightsRequest:
    """
    Attributes:
        eval_template_ids (list[UUID] | Unset):
        weights (ExperimentComparisonWeightsRequestWeights | Unset):
    """

    eval_template_ids: list[UUID] | Unset = UNSET
    weights: ExperimentComparisonWeightsRequestWeights | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_template_ids: list[str] | Unset = UNSET
        if not isinstance(self.eval_template_ids, Unset):
            eval_template_ids = []
            for eval_template_ids_item_data in self.eval_template_ids:
                eval_template_ids_item = str(eval_template_ids_item_data)
                eval_template_ids.append(eval_template_ids_item)

        weights: dict[str, Any] | Unset = UNSET
        if not isinstance(self.weights, Unset):
            weights = self.weights.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if eval_template_ids is not UNSET:
            field_dict["eval_template_ids"] = eval_template_ids
        if weights is not UNSET:
            field_dict["weights"] = weights

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_comparison_weights_request_weights import (
            ExperimentComparisonWeightsRequestWeights,
        )

        d = dict(src_dict)
        _eval_template_ids = d.pop("eval_template_ids", UNSET)
        eval_template_ids: list[UUID] | Unset = UNSET
        if _eval_template_ids is not UNSET:
            eval_template_ids = []
            for eval_template_ids_item_data in _eval_template_ids:
                eval_template_ids_item = UUID(eval_template_ids_item_data)

                eval_template_ids.append(eval_template_ids_item)

        _weights = d.pop("weights", UNSET)
        weights: ExperimentComparisonWeightsRequestWeights | Unset
        if isinstance(_weights, Unset):
            weights = UNSET
        else:
            weights = ExperimentComparisonWeightsRequestWeights.from_dict(_weights)

        experiment_comparison_weights_request = cls(
            eval_template_ids=eval_template_ids,
            weights=weights,
        )

        experiment_comparison_weights_request.additional_properties = d
        return experiment_comparison_weights_request

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
