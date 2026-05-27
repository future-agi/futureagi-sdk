from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.composite_child_result import CompositeChildResult
    from ..models.composite_eval_execute_response_result_error_localizer_results import (
        CompositeEvalExecuteResponseResultErrorLocalizerResults,
    )


T = TypeVar("T", bound="CompositeEvalExecuteResponseResult")


@_attrs_define
class CompositeEvalExecuteResponseResult:
    """
    Attributes:
        composite_name (str):
        aggregation_enabled (bool):
        children (list[CompositeChildResult]):
        total_children (int):
        completed_children (int):
        failed_children (int):
        composite_id (None | str | Unset):
        aggregation_function (None | str | Unset):
        aggregate_score (float | None | Unset):
        aggregate_pass (bool | None | Unset):
        summary (None | str | Unset):
        error_localizer_results (CompositeEvalExecuteResponseResultErrorLocalizerResults | Unset):
        evaluation_id (None | str | Unset):
    """

    composite_name: str
    aggregation_enabled: bool
    children: list[CompositeChildResult]
    total_children: int
    completed_children: int
    failed_children: int
    composite_id: None | str | Unset = UNSET
    aggregation_function: None | str | Unset = UNSET
    aggregate_score: float | None | Unset = UNSET
    aggregate_pass: bool | None | Unset = UNSET
    summary: None | str | Unset = UNSET
    error_localizer_results: (
        CompositeEvalExecuteResponseResultErrorLocalizerResults | Unset
    ) = UNSET
    evaluation_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        composite_name = self.composite_name

        aggregation_enabled = self.aggregation_enabled

        children = []
        for children_item_data in self.children:
            children_item = children_item_data.to_dict()
            children.append(children_item)

        total_children = self.total_children

        completed_children = self.completed_children

        failed_children = self.failed_children

        composite_id: None | str | Unset
        if isinstance(self.composite_id, Unset):
            composite_id = UNSET
        else:
            composite_id = self.composite_id

        aggregation_function: None | str | Unset
        if isinstance(self.aggregation_function, Unset):
            aggregation_function = UNSET
        else:
            aggregation_function = self.aggregation_function

        aggregate_score: float | None | Unset
        if isinstance(self.aggregate_score, Unset):
            aggregate_score = UNSET
        else:
            aggregate_score = self.aggregate_score

        aggregate_pass: bool | None | Unset
        if isinstance(self.aggregate_pass, Unset):
            aggregate_pass = UNSET
        else:
            aggregate_pass = self.aggregate_pass

        summary: None | str | Unset
        if isinstance(self.summary, Unset):
            summary = UNSET
        else:
            summary = self.summary

        error_localizer_results: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error_localizer_results, Unset):
            error_localizer_results = self.error_localizer_results.to_dict()

        evaluation_id: None | str | Unset
        if isinstance(self.evaluation_id, Unset):
            evaluation_id = UNSET
        else:
            evaluation_id = self.evaluation_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "composite_name": composite_name,
                "aggregation_enabled": aggregation_enabled,
                "children": children,
                "total_children": total_children,
                "completed_children": completed_children,
                "failed_children": failed_children,
            }
        )
        if composite_id is not UNSET:
            field_dict["composite_id"] = composite_id
        if aggregation_function is not UNSET:
            field_dict["aggregation_function"] = aggregation_function
        if aggregate_score is not UNSET:
            field_dict["aggregate_score"] = aggregate_score
        if aggregate_pass is not UNSET:
            field_dict["aggregate_pass"] = aggregate_pass
        if summary is not UNSET:
            field_dict["summary"] = summary
        if error_localizer_results is not UNSET:
            field_dict["error_localizer_results"] = error_localizer_results
        if evaluation_id is not UNSET:
            field_dict["evaluation_id"] = evaluation_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.composite_child_result import CompositeChildResult
        from ..models.composite_eval_execute_response_result_error_localizer_results import (
            CompositeEvalExecuteResponseResultErrorLocalizerResults,
        )

        d = dict(src_dict)
        composite_name = d.pop("composite_name")

        aggregation_enabled = d.pop("aggregation_enabled")

        children = []
        _children = d.pop("children")
        for children_item_data in _children:
            children_item = CompositeChildResult.from_dict(children_item_data)

            children.append(children_item)

        total_children = d.pop("total_children")

        completed_children = d.pop("completed_children")

        failed_children = d.pop("failed_children")

        def _parse_composite_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        composite_id = _parse_composite_id(d.pop("composite_id", UNSET))

        def _parse_aggregation_function(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        aggregation_function = _parse_aggregation_function(
            d.pop("aggregation_function", UNSET)
        )

        def _parse_aggregate_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        aggregate_score = _parse_aggregate_score(d.pop("aggregate_score", UNSET))

        def _parse_aggregate_pass(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        aggregate_pass = _parse_aggregate_pass(d.pop("aggregate_pass", UNSET))

        def _parse_summary(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        summary = _parse_summary(d.pop("summary", UNSET))

        _error_localizer_results = d.pop("error_localizer_results", UNSET)
        error_localizer_results: (
            CompositeEvalExecuteResponseResultErrorLocalizerResults | Unset
        )
        if isinstance(_error_localizer_results, Unset):
            error_localizer_results = UNSET
        else:
            error_localizer_results = (
                CompositeEvalExecuteResponseResultErrorLocalizerResults.from_dict(
                    _error_localizer_results
                )
            )

        def _parse_evaluation_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        evaluation_id = _parse_evaluation_id(d.pop("evaluation_id", UNSET))

        composite_eval_execute_response_result = cls(
            composite_name=composite_name,
            aggregation_enabled=aggregation_enabled,
            children=children,
            total_children=total_children,
            completed_children=completed_children,
            failed_children=failed_children,
            composite_id=composite_id,
            aggregation_function=aggregation_function,
            aggregate_score=aggregate_score,
            aggregate_pass=aggregate_pass,
            summary=summary,
            error_localizer_results=error_localizer_results,
            evaluation_id=evaluation_id,
        )

        composite_eval_execute_response_result.additional_properties = d
        return composite_eval_execute_response_result

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
