from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.annotation_summary_header import AnnotationSummaryHeader
    from ..models.annotation_summary_result_annotators_item import (
        AnnotationSummaryResultAnnotatorsItem,
    )
    from ..models.annotation_summary_result_labels_item import (
        AnnotationSummaryResultLabelsItem,
    )


T = TypeVar("T", bound="AnnotationSummaryResult")


@_attrs_define
class AnnotationSummaryResult:
    """
    Attributes:
        labels (list[AnnotationSummaryResultLabelsItem] | Unset):
        annotators (list[AnnotationSummaryResultAnnotatorsItem] | Unset):
        header (AnnotationSummaryHeader | Unset):
    """

    labels: list[AnnotationSummaryResultLabelsItem] | Unset = UNSET
    annotators: list[AnnotationSummaryResultAnnotatorsItem] | Unset = UNSET
    header: AnnotationSummaryHeader | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        labels: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.labels, Unset):
            labels = []
            for labels_item_data in self.labels:
                labels_item = labels_item_data.to_dict()
                labels.append(labels_item)

        annotators: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.annotators, Unset):
            annotators = []
            for annotators_item_data in self.annotators:
                annotators_item = annotators_item_data.to_dict()
                annotators.append(annotators_item)

        header: dict[str, Any] | Unset = UNSET
        if not isinstance(self.header, Unset):
            header = self.header.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if labels is not UNSET:
            field_dict["labels"] = labels
        if annotators is not UNSET:
            field_dict["annotators"] = annotators
        if header is not UNSET:
            field_dict["header"] = header

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.annotation_summary_header import AnnotationSummaryHeader
        from ..models.annotation_summary_result_annotators_item import (
            AnnotationSummaryResultAnnotatorsItem,
        )
        from ..models.annotation_summary_result_labels_item import (
            AnnotationSummaryResultLabelsItem,
        )

        d = dict(src_dict)
        _labels = d.pop("labels", UNSET)
        labels: list[AnnotationSummaryResultLabelsItem] | Unset = UNSET
        if _labels is not UNSET:
            labels = []
            for labels_item_data in _labels:
                labels_item = AnnotationSummaryResultLabelsItem.from_dict(
                    labels_item_data
                )

                labels.append(labels_item)

        _annotators = d.pop("annotators", UNSET)
        annotators: list[AnnotationSummaryResultAnnotatorsItem] | Unset = UNSET
        if _annotators is not UNSET:
            annotators = []
            for annotators_item_data in _annotators:
                annotators_item = AnnotationSummaryResultAnnotatorsItem.from_dict(
                    annotators_item_data
                )

                annotators.append(annotators_item)

        _header = d.pop("header", UNSET)
        header: AnnotationSummaryHeader | Unset
        if isinstance(_header, Unset):
            header = UNSET
        else:
            header = AnnotationSummaryHeader.from_dict(_header)

        annotation_summary_result = cls(
            labels=labels,
            annotators=annotators,
            header=header,
        )

        annotation_summary_result.additional_properties = d
        return annotation_summary_result

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
