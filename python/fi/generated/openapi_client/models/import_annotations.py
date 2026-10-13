from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.import_annotation_entry import ImportAnnotationEntry


T = TypeVar("T", bound="ImportAnnotations")


@_attrs_define
class ImportAnnotations:
    """
    Attributes:
        annotations (list[ImportAnnotationEntry]):
        annotator_id (UUID | Unset):
    """

    annotations: list[ImportAnnotationEntry]
    annotator_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        annotations = []
        for annotations_item_data in self.annotations:
            annotations_item = annotations_item_data.to_dict()
            annotations.append(annotations_item)

        annotator_id: str | Unset = UNSET
        if not isinstance(self.annotator_id, Unset):
            annotator_id = str(self.annotator_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "annotations": annotations,
            }
        )
        if annotator_id is not UNSET:
            field_dict["annotator_id"] = annotator_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.import_annotation_entry import ImportAnnotationEntry

        d = dict(src_dict)
        annotations = []
        _annotations = d.pop("annotations")
        for annotations_item_data in _annotations:
            annotations_item = ImportAnnotationEntry.from_dict(annotations_item_data)

            annotations.append(annotations_item)

        _annotator_id = d.pop("annotator_id", UNSET)
        annotator_id: UUID | Unset
        if isinstance(_annotator_id, Unset):
            annotator_id = UNSET
        else:
            annotator_id = UUID(_annotator_id)

        import_annotations = cls(
            annotations=annotations,
            annotator_id=annotator_id,
        )

        import_annotations.additional_properties = d
        return import_annotations

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
