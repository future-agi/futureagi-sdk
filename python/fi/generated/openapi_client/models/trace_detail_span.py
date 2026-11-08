from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_rollup import EvalRollup
    from ..models.trace_detail_span_annotations_item import (
        TraceDetailSpanAnnotationsItem,
    )
    from ..models.trace_detail_span_children_item import TraceDetailSpanChildrenItem
    from ..models.trace_detail_span_eval_scores_item import (
        TraceDetailSpanEvalScoresItem,
    )
    from ..models.trace_detail_span_observation_span import (
        TraceDetailSpanObservationSpan,
    )


T = TypeVar("T", bound="TraceDetailSpan")


@_attrs_define
class TraceDetailSpan:
    """
    Attributes:
        observation_span (TraceDetailSpanObservationSpan):
        children (list[TraceDetailSpanChildrenItem] | Unset):
        eval_scores (list[TraceDetailSpanEvalScoresItem] | Unset): Raw eval rows retained for backwards-compatible array
            consumers.
        eval_rollup (EvalRollup | Unset):
        annotations (list[TraceDetailSpanAnnotationsItem] | Unset):
    """

    observation_span: TraceDetailSpanObservationSpan
    children: list[TraceDetailSpanChildrenItem] | Unset = UNSET
    eval_scores: list[TraceDetailSpanEvalScoresItem] | Unset = UNSET
    eval_rollup: EvalRollup | Unset = UNSET
    annotations: list[TraceDetailSpanAnnotationsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        observation_span = self.observation_span.to_dict()

        children: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.children, Unset):
            children = []
            for children_item_data in self.children:
                children_item = children_item_data.to_dict()
                children.append(children_item)

        eval_scores: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.eval_scores, Unset):
            eval_scores = []
            for eval_scores_item_data in self.eval_scores:
                eval_scores_item = eval_scores_item_data.to_dict()
                eval_scores.append(eval_scores_item)

        eval_rollup: dict[str, Any] | Unset = UNSET
        if not isinstance(self.eval_rollup, Unset):
            eval_rollup = self.eval_rollup.to_dict()

        annotations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.annotations, Unset):
            annotations = []
            for annotations_item_data in self.annotations:
                annotations_item = annotations_item_data.to_dict()
                annotations.append(annotations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observation_span": observation_span,
            }
        )
        if children is not UNSET:
            field_dict["children"] = children
        if eval_scores is not UNSET:
            field_dict["eval_scores"] = eval_scores
        if eval_rollup is not UNSET:
            field_dict["eval_rollup"] = eval_rollup
        if annotations is not UNSET:
            field_dict["annotations"] = annotations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_rollup import EvalRollup
        from ..models.trace_detail_span_annotations_item import (
            TraceDetailSpanAnnotationsItem,
        )
        from ..models.trace_detail_span_children_item import TraceDetailSpanChildrenItem
        from ..models.trace_detail_span_eval_scores_item import (
            TraceDetailSpanEvalScoresItem,
        )
        from ..models.trace_detail_span_observation_span import (
            TraceDetailSpanObservationSpan,
        )

        d = dict(src_dict)
        observation_span = TraceDetailSpanObservationSpan.from_dict(
            d.pop("observation_span")
        )

        _children = d.pop("children", UNSET)
        children: list[TraceDetailSpanChildrenItem] | Unset = UNSET
        if _children is not UNSET:
            children = []
            for children_item_data in _children:
                children_item = TraceDetailSpanChildrenItem.from_dict(
                    children_item_data
                )

                children.append(children_item)

        _eval_scores = d.pop("eval_scores", UNSET)
        eval_scores: list[TraceDetailSpanEvalScoresItem] | Unset = UNSET
        if _eval_scores is not UNSET:
            eval_scores = []
            for eval_scores_item_data in _eval_scores:
                eval_scores_item = TraceDetailSpanEvalScoresItem.from_dict(
                    eval_scores_item_data
                )

                eval_scores.append(eval_scores_item)

        _eval_rollup = d.pop("eval_rollup", UNSET)
        eval_rollup: EvalRollup | Unset
        if isinstance(_eval_rollup, Unset):
            eval_rollup = UNSET
        else:
            eval_rollup = EvalRollup.from_dict(_eval_rollup)

        _annotations = d.pop("annotations", UNSET)
        annotations: list[TraceDetailSpanAnnotationsItem] | Unset = UNSET
        if _annotations is not UNSET:
            annotations = []
            for annotations_item_data in _annotations:
                annotations_item = TraceDetailSpanAnnotationsItem.from_dict(
                    annotations_item_data
                )

                annotations.append(annotations_item)

        trace_detail_span = cls(
            observation_span=observation_span,
            children=children,
            eval_scores=eval_scores,
            eval_rollup=eval_rollup,
            annotations=annotations,
        )

        trace_detail_span.additional_properties = d
        return trace_detail_span

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
