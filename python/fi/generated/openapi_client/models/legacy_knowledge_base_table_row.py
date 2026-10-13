from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="LegacyKnowledgeBaseTableRow")


@_attrs_define
class LegacyKnowledgeBaseTableRow:
    """
    Attributes:
        id (UUID):
        name (str):
        files_uploaded (int):
        status (str):
        updated_at (datetime.datetime):
        created_by (None | str):
        error (None | str | Unset):
    """

    id: UUID
    name: str
    files_uploaded: int
    status: str
    updated_at: datetime.datetime
    created_by: None | str
    error: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        files_uploaded = self.files_uploaded

        status = self.status

        updated_at = self.updated_at.isoformat()

        created_by: None | str
        created_by = self.created_by

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
                "files_uploaded": files_uploaded,
                "status": status,
                "updated_at": updated_at,
                "created_by": created_by,
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

        files_uploaded = d.pop("files_uploaded")

        status = d.pop("status")

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_created_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        created_by = _parse_created_by(d.pop("created_by"))

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        legacy_knowledge_base_table_row = cls(
            id=id,
            name=name,
            files_uploaded=files_uploaded,
            status=status,
            updated_at=updated_at,
            created_by=created_by,
            error=error,
        )

        legacy_knowledge_base_table_row.additional_properties = d
        return legacy_knowledge_base_table_row

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
