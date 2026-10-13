from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.trace_annotation_note_response import TraceAnnotationNoteResponse
    from ..models.trace_annotation_value_response import TraceAnnotationValueResponse


T = TypeVar("T", bound="GetTraceAnnotationValuesResult")


@_attrs_define
class GetTraceAnnotationValuesResult:
    """
    Attributes:
        annotations (list[TraceAnnotationValueResponse]):
        notes (list[TraceAnnotationNoteResponse]):
    """

    annotations: list[TraceAnnotationValueResponse]
    notes: list[TraceAnnotationNoteResponse]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        annotations = []
        for annotations_item_data in self.annotations:
            annotations_item = annotations_item_data.to_dict()
            annotations.append(annotations_item)

        notes = []
        for notes_item_data in self.notes:
            notes_item = notes_item_data.to_dict()
            notes.append(notes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "annotations": annotations,
                "notes": notes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_annotation_note_response import TraceAnnotationNoteResponse
        from ..models.trace_annotation_value_response import (
            TraceAnnotationValueResponse,
        )

        d = dict(src_dict)
        annotations = []
        _annotations = d.pop("annotations")
        for annotations_item_data in _annotations:
            annotations_item = TraceAnnotationValueResponse.from_dict(
                annotations_item_data
            )

            annotations.append(annotations_item)

        notes = []
        _notes = d.pop("notes")
        for notes_item_data in _notes:
            notes_item = TraceAnnotationNoteResponse.from_dict(notes_item_data)

            notes.append(notes_item)

        get_trace_annotation_values_result = cls(
            annotations=annotations,
            notes=notes,
        )

        get_trace_annotation_values_result.additional_properties = d
        return get_trace_annotation_values_result

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
