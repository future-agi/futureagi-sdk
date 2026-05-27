from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.composite_eval_update_request_aggregation_function import (
    CompositeEvalUpdateRequestAggregationFunction,
)
from ..models.composite_eval_update_request_composite_child_axis import (
    CompositeEvalUpdateRequestCompositeChildAxis,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.composite_eval_update_request_child_weights import (
        CompositeEvalUpdateRequestChildWeights,
    )


T = TypeVar("T", bound="CompositeEvalUpdateRequest")


@_attrs_define
class CompositeEvalUpdateRequest:
    """
    Attributes:
        name (None | str | Unset):
        description (None | str | Unset):
        tags (list[str] | None | Unset):
        aggregation_enabled (bool | None | Unset):
        aggregation_function (CompositeEvalUpdateRequestAggregationFunction | Unset):
        child_template_ids (list[UUID] | None | Unset):
        child_weights (CompositeEvalUpdateRequestChildWeights | Unset):
        composite_child_axis (CompositeEvalUpdateRequestCompositeChildAxis | Unset):
    """

    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    tags: list[str] | None | Unset = UNSET
    aggregation_enabled: bool | None | Unset = UNSET
    aggregation_function: CompositeEvalUpdateRequestAggregationFunction | Unset = UNSET
    child_template_ids: list[UUID] | None | Unset = UNSET
    child_weights: CompositeEvalUpdateRequestChildWeights | Unset = UNSET
    composite_child_axis: CompositeEvalUpdateRequestCompositeChildAxis | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        aggregation_enabled: bool | None | Unset
        if isinstance(self.aggregation_enabled, Unset):
            aggregation_enabled = UNSET
        else:
            aggregation_enabled = self.aggregation_enabled

        aggregation_function: str | Unset = UNSET
        if not isinstance(self.aggregation_function, Unset):
            aggregation_function = self.aggregation_function.value

        child_template_ids: list[str] | None | Unset
        if isinstance(self.child_template_ids, Unset):
            child_template_ids = UNSET
        elif isinstance(self.child_template_ids, list):
            child_template_ids = []
            for child_template_ids_type_0_item_data in self.child_template_ids:
                child_template_ids_type_0_item = str(
                    child_template_ids_type_0_item_data
                )
                child_template_ids.append(child_template_ids_type_0_item)

        else:
            child_template_ids = self.child_template_ids

        child_weights: dict[str, Any] | Unset = UNSET
        if not isinstance(self.child_weights, Unset):
            child_weights = self.child_weights.to_dict()

        composite_child_axis: str | Unset = UNSET
        if not isinstance(self.composite_child_axis, Unset):
            composite_child_axis = self.composite_child_axis.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if tags is not UNSET:
            field_dict["tags"] = tags
        if aggregation_enabled is not UNSET:
            field_dict["aggregation_enabled"] = aggregation_enabled
        if aggregation_function is not UNSET:
            field_dict["aggregation_function"] = aggregation_function
        if child_template_ids is not UNSET:
            field_dict["child_template_ids"] = child_template_ids
        if child_weights is not UNSET:
            field_dict["child_weights"] = child_weights
        if composite_child_axis is not UNSET:
            field_dict["composite_child_axis"] = composite_child_axis

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.composite_eval_update_request_child_weights import (
            CompositeEvalUpdateRequestChildWeights,
        )

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_tags(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = cast(list[str], data)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

        def _parse_aggregation_enabled(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        aggregation_enabled = _parse_aggregation_enabled(
            d.pop("aggregation_enabled", UNSET)
        )

        _aggregation_function = d.pop("aggregation_function", UNSET)
        aggregation_function: CompositeEvalUpdateRequestAggregationFunction | Unset
        if isinstance(_aggregation_function, Unset):
            aggregation_function = UNSET
        else:
            aggregation_function = CompositeEvalUpdateRequestAggregationFunction(
                _aggregation_function
            )

        def _parse_child_template_ids(data: object) -> list[UUID] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                child_template_ids_type_0 = []
                _child_template_ids_type_0 = data
                for child_template_ids_type_0_item_data in _child_template_ids_type_0:
                    child_template_ids_type_0_item = UUID(
                        child_template_ids_type_0_item_data
                    )

                    child_template_ids_type_0.append(child_template_ids_type_0_item)

                return child_template_ids_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[UUID] | None | Unset, data)

        child_template_ids = _parse_child_template_ids(
            d.pop("child_template_ids", UNSET)
        )

        _child_weights = d.pop("child_weights", UNSET)
        child_weights: CompositeEvalUpdateRequestChildWeights | Unset
        if isinstance(_child_weights, Unset):
            child_weights = UNSET
        else:
            child_weights = CompositeEvalUpdateRequestChildWeights.from_dict(
                _child_weights
            )

        _composite_child_axis = d.pop("composite_child_axis", UNSET)
        composite_child_axis: CompositeEvalUpdateRequestCompositeChildAxis | Unset
        if isinstance(_composite_child_axis, Unset):
            composite_child_axis = UNSET
        else:
            composite_child_axis = CompositeEvalUpdateRequestCompositeChildAxis(
                _composite_child_axis
            )

        composite_eval_update_request = cls(
            name=name,
            description=description,
            tags=tags,
            aggregation_enabled=aggregation_enabled,
            aggregation_function=aggregation_function,
            child_template_ids=child_template_ids,
            child_weights=child_weights,
            composite_child_axis=composite_child_axis,
        )

        composite_eval_update_request.additional_properties = d
        return composite_eval_update_request

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
