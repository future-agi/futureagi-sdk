from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="TraceAnnotationNoteResponse")


@_attrs_define
class TraceAnnotationNoteResponse:
    """
    Attributes:
        id (UUID):
        notes (str):
        created_by_annotator (str):
        created_by_user (str):
        created_by_user_id (UUID):
        updated_at (datetime.datetime):
    """

    id: UUID
    notes: str
    created_by_annotator: str
    created_by_user: str
    created_by_user_id: UUID
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        notes = self.notes

        created_by_annotator = self.created_by_annotator

        created_by_user = self.created_by_user

        created_by_user_id = str(self.created_by_user_id)

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "notes": notes,
                "created_by_annotator": created_by_annotator,
                "created_by_user": created_by_user,
                "created_by_user_id": created_by_user_id,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        notes = d.pop("notes")

        created_by_annotator = d.pop("created_by_annotator")

        created_by_user = d.pop("created_by_user")

        created_by_user_id = UUID(d.pop("created_by_user_id"))

        updated_at = isoparse(d.pop("updated_at"))

        trace_annotation_note_response = cls(
            id=id,
            notes=notes,
            created_by_annotator=created_by_annotator,
            created_by_user=created_by_user,
            created_by_user_id=created_by_user_id,
            updated_at=updated_at,
        )

        trace_annotation_note_response.additional_properties = d
        return trace_annotation_note_response

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
