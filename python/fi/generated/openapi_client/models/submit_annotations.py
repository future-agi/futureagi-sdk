from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.submit_annotation_entry import SubmitAnnotationEntry


T = TypeVar("T", bound="SubmitAnnotations")


@_attrs_define
class SubmitAnnotations:
    """
    Attributes:
        annotations (list[SubmitAnnotationEntry]):
        notes (str | Unset):  Default: ''.
        item_notes (None | str | Unset):
    """

    annotations: list[SubmitAnnotationEntry]
    notes: str | Unset = ""
    item_notes: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        annotations = []
        for annotations_item_data in self.annotations:
            annotations_item = annotations_item_data.to_dict()
            annotations.append(annotations_item)

        notes = self.notes

        item_notes: None | str | Unset
        if isinstance(self.item_notes, Unset):
            item_notes = UNSET
        else:
            item_notes = self.item_notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "annotations": annotations,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if item_notes is not UNSET:
            field_dict["item_notes"] = item_notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.submit_annotation_entry import SubmitAnnotationEntry

        d = dict(src_dict)
        annotations = []
        _annotations = d.pop("annotations")
        for annotations_item_data in _annotations:
            annotations_item = SubmitAnnotationEntry.from_dict(annotations_item_data)

            annotations.append(annotations_item)

        notes = d.pop("notes", UNSET)

        def _parse_item_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        item_notes = _parse_item_notes(d.pop("item_notes", UNSET))

        submit_annotations = cls(
            annotations=annotations,
            notes=notes,
            item_notes=item_notes,
        )

        submit_annotations.additional_properties = d
        return submit_annotations

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
