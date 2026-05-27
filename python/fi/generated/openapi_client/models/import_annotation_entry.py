from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.import_annotation_entry_value import ImportAnnotationEntryValue


T = TypeVar("T", bound="ImportAnnotationEntry")


@_attrs_define
class ImportAnnotationEntry:
    """
    Attributes:
        label_id (UUID):
        value (ImportAnnotationEntryValue):
        notes (str | Unset):
        score_source (str | Unset):
    """

    label_id: UUID
    value: ImportAnnotationEntryValue
    notes: str | Unset = UNSET
    score_source: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        label_id = str(self.label_id)

        value = self.value.to_dict()

        notes = self.notes

        score_source = self.score_source

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "label_id": label_id,
                "value": value,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if score_source is not UNSET:
            field_dict["score_source"] = score_source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.import_annotation_entry_value import ImportAnnotationEntryValue

        d = dict(src_dict)
        label_id = UUID(d.pop("label_id"))

        value = ImportAnnotationEntryValue.from_dict(d.pop("value"))

        notes = d.pop("notes", UNSET)

        score_source = d.pop("score_source", UNSET)

        import_annotation_entry = cls(
            label_id=label_id,
            value=value,
            notes=notes,
            score_source=score_source,
        )

        import_annotation_entry.additional_properties = d
        return import_annotation_entry

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
