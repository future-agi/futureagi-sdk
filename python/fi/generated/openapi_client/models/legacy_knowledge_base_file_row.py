from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="LegacyKnowledgeBaseFileRow")


@_attrs_define
class LegacyKnowledgeBaseFileRow:
    """
    Attributes:
        id (UUID):
        name (str):
        file_size (int):
        status (str):
        updated (datetime.datetime):
        updated_by (None | str):
        error (None | str | Unset):
    """

    id: UUID
    name: str
    file_size: int
    status: str
    updated: datetime.datetime
    updated_by: None | str
    error: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        file_size = self.file_size

        status = self.status

        updated = self.updated.isoformat()

        updated_by: None | str
        updated_by = self.updated_by

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "file_size": file_size,
                "status": status,
                "updated": updated,
                "updated_by": updated_by,
            }
        )
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        file_size = d.pop("file_size")

        status = d.pop("status")

        updated = isoparse(d.pop("updated"))

        def _parse_updated_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        updated_by = _parse_updated_by(d.pop("updated_by"))

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        legacy_knowledge_base_file_row = cls(
            id=id,
            name=name,
            file_size=file_size,
            status=status,
            updated=updated,
            updated_by=updated_by,
            error=error,
        )

        legacy_knowledge_base_file_row.additional_properties = d
        return legacy_knowledge_base_file_row

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
