from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bulk_annotation_annotation_request import (
        BulkAnnotationAnnotationRequest,
    )
    from ..models.bulk_annotation_note_request import BulkAnnotationNoteRequest


T = TypeVar("T", bound="BulkAnnotationRecordRequest")


@_attrs_define
class BulkAnnotationRecordRequest:
    """
    Attributes:
        observation_span_id (str):
        annotations (list[BulkAnnotationAnnotationRequest] | Unset):
        notes (list[BulkAnnotationNoteRequest] | Unset):
    """

    observation_span_id: str
    annotations: list[BulkAnnotationAnnotationRequest] | Unset = UNSET
    notes: list[BulkAnnotationNoteRequest] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        observation_span_id = self.observation_span_id

        annotations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.annotations, Unset):
            annotations = []
            for annotations_item_data in self.annotations:
                annotations_item = annotations_item_data.to_dict()
                annotations.append(annotations_item)

        notes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.notes, Unset):
            notes = []
            for notes_item_data in self.notes:
                notes_item = notes_item_data.to_dict()
                notes.append(notes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observation_span_id": observation_span_id,
            }
        )
        if annotations is not UNSET:
            field_dict["annotations"] = annotations
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bulk_annotation_annotation_request import (
            BulkAnnotationAnnotationRequest,
        )
        from ..models.bulk_annotation_note_request import BulkAnnotationNoteRequest

        d = dict(src_dict)
        observation_span_id = d.pop("observation_span_id")

        _annotations = d.pop("annotations", UNSET)
        annotations: list[BulkAnnotationAnnotationRequest] | Unset = UNSET
        if _annotations is not UNSET:
            annotations = []
            for annotations_item_data in _annotations:
                annotations_item = BulkAnnotationAnnotationRequest.from_dict(
                    annotations_item_data
                )

                annotations.append(annotations_item)

        _notes = d.pop("notes", UNSET)
        notes: list[BulkAnnotationNoteRequest] | Unset = UNSET
        if _notes is not UNSET:
            notes = []
            for notes_item_data in _notes:
                notes_item = BulkAnnotationNoteRequest.from_dict(notes_item_data)

                notes.append(notes_item)

        bulk_annotation_record_request = cls(
            observation_span_id=observation_span_id,
            annotations=annotations,
            notes=notes,
        )

        bulk_annotation_record_request.additional_properties = d
        return bulk_annotation_record_request

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
