from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="LegacyKnowledgeBaseMutationResult")


@_attrs_define
class LegacyKnowledgeBaseMutationResult:
    """
    Attributes:
        id (UUID):
        name (str):
        organization (UUID):
        status (str):
        files (list[UUID]):
        updated_at (datetime.datetime):
        created_by (None | str):
        last_error (None | str):
    """

    id: UUID
    name: str
    organization: UUID
    status: str
    files: list[UUID]
    updated_at: datetime.datetime
    created_by: None | str
    last_error: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        organization = str(self.organization)

        status = self.status

        files = []
        for files_item_data in self.files:
            files_item = str(files_item_data)
            files.append(files_item)

        updated_at = self.updated_at.isoformat()

        created_by: None | str
        created_by = self.created_by

        last_error: None | str
        last_error = self.last_error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "organization": organization,
                "status": status,
                "files": files,
                "updated_at": updated_at,
                "created_by": created_by,
                "last_error": last_error,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        organization = UUID(d.pop("organization"))

        status = d.pop("status")

        files = []
        _files = d.pop("files")
        for files_item_data in _files:
            files_item = UUID(files_item_data)

            files.append(files_item)

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_created_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        created_by = _parse_created_by(d.pop("created_by"))

        def _parse_last_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        last_error = _parse_last_error(d.pop("last_error"))

        legacy_knowledge_base_mutation_result = cls(
            id=id,
            name=name,
            organization=organization,
            status=status,
            files=files,
            updated_at=updated_at,
            created_by=created_by,
            last_error=last_error,
        )

        legacy_knowledge_base_mutation_result.additional_properties = d
        return legacy_knowledge_base_mutation_result

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
