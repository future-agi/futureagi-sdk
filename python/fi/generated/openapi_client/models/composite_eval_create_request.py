from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.composite_eval_create_request_aggregation_function import (
    CompositeEvalCreateRequestAggregationFunction,
)
from ..models.composite_eval_create_request_composite_child_axis import (
    CompositeEvalCreateRequestCompositeChildAxis,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.composite_eval_create_request_child_weights import (
        CompositeEvalCreateRequestChildWeights,
    )


T = TypeVar("T", bound="CompositeEvalCreateRequest")


@_attrs_define
class CompositeEvalCreateRequest:
    """
    Attributes:
        name (str):
        child_template_ids (list[UUID]):
        description (None | str | Unset):
        tags (list[str] | Unset):
        aggregation_enabled (bool | Unset):  Default: True.
        aggregation_function (CompositeEvalCreateRequestAggregationFunction | Unset):  Default:
            CompositeEvalCreateRequestAggregationFunction.WEIGHTED_AVG.
        child_weights (CompositeEvalCreateRequestChildWeights | Unset):
        composite_child_axis (CompositeEvalCreateRequestCompositeChildAxis | Unset):  Default:
            CompositeEvalCreateRequestCompositeChildAxis.VALUE_0.
    """

    name: str
    child_template_ids: list[UUID]
    description: None | str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    aggregation_enabled: bool | Unset = True
    aggregation_function: CompositeEvalCreateRequestAggregationFunction | Unset = (
        CompositeEvalCreateRequestAggregationFunction.WEIGHTED_AVG
    )
    child_weights: CompositeEvalCreateRequestChildWeights | Unset = UNSET
    composite_child_axis: CompositeEvalCreateRequestCompositeChildAxis | Unset = (
        CompositeEvalCreateRequestCompositeChildAxis.VALUE_0
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        child_template_ids = []
        for child_template_ids_item_data in self.child_template_ids:
            child_template_ids_item = str(child_template_ids_item_data)
            child_template_ids.append(child_template_ids_item)

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        aggregation_enabled = self.aggregation_enabled

        aggregation_function: str | Unset = UNSET
        if not isinstance(self.aggregation_function, Unset):
            aggregation_function = self.aggregation_function.value

        child_weights: dict[str, Any] | Unset = UNSET
        if not isinstance(self.child_weights, Unset):
            child_weights = self.child_weights.to_dict()

        composite_child_axis: str | Unset = UNSET
        if not isinstance(self.composite_child_axis, Unset):
            composite_child_axis = self.composite_child_axis.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "child_template_ids": child_template_ids,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if tags is not UNSET:
            field_dict["tags"] = tags
        if aggregation_enabled is not UNSET:
            field_dict["aggregation_enabled"] = aggregation_enabled
        if aggregation_function is not UNSET:
            field_dict["aggregation_function"] = aggregation_function
        if child_weights is not UNSET:
            field_dict["child_weights"] = child_weights
        if composite_child_axis is not UNSET:
            field_dict["composite_child_axis"] = composite_child_axis

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.composite_eval_create_request_child_weights import (
            CompositeEvalCreateRequestChildWeights,
        )

        d = dict(src_dict)
        name = d.pop("name")

        child_template_ids = []
        _child_template_ids = d.pop("child_template_ids")
        for child_template_ids_item_data in _child_template_ids:
            child_template_ids_item = UUID(child_template_ids_item_data)

            child_template_ids.append(child_template_ids_item)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        tags = cast(list[str], d.pop("tags", UNSET))

        aggregation_enabled = d.pop("aggregation_enabled", UNSET)

        _aggregation_function = d.pop("aggregation_function", UNSET)
        aggregation_function: CompositeEvalCreateRequestAggregationFunction | Unset
        if isinstance(_aggregation_function, Unset):
            aggregation_function = UNSET
        else:
            aggregation_function = CompositeEvalCreateRequestAggregationFunction(
                _aggregation_function
            )

        _child_weights = d.pop("child_weights", UNSET)
        child_weights: CompositeEvalCreateRequestChildWeights | Unset
        if isinstance(_child_weights, Unset):
            child_weights = UNSET
        else:
            child_weights = CompositeEvalCreateRequestChildWeights.from_dict(
                _child_weights
            )

        _composite_child_axis = d.pop("composite_child_axis", UNSET)
        composite_child_axis: CompositeEvalCreateRequestCompositeChildAxis | Unset
        if isinstance(_composite_child_axis, Unset):
            composite_child_axis = UNSET
        else:
            composite_child_axis = CompositeEvalCreateRequestCompositeChildAxis(
                _composite_child_axis
            )

        composite_eval_create_request = cls(
            name=name,
            child_template_ids=child_template_ids,
            description=description,
            tags=tags,
            aggregation_enabled=aggregation_enabled,
            aggregation_function=aggregation_function,
            child_weights=child_weights,
            composite_child_axis=composite_child_axis,
        )

        composite_eval_create_request.additional_properties = d
        return composite_eval_create_request

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
