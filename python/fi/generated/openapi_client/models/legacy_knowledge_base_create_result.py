from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="LegacyKnowledgeBaseCreateResult")


@_attrs_define
class LegacyKnowledgeBaseCreateResult:
    """
    Attributes:
        detail (str):
        kb_id (UUID):
        kb_name (str):
        file_ids (list[UUID]):
    """

    detail: str
    kb_id: UUID
    kb_name: str
    file_ids: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        detail = self.detail

        kb_id = str(self.kb_id)

        kb_name = self.kb_name

        file_ids = []
        for file_ids_item_data in self.file_ids:
            file_ids_item = str(file_ids_item_data)
            file_ids.append(file_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "detail": detail,
                "kb_id": kb_id,
                "kb_name": kb_name,
                "file_ids": file_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        detail = d.pop("detail")

        kb_id = UUID(d.pop("kb_id"))

        kb_name = d.pop("kb_name")

        file_ids = []
        _file_ids = d.pop("file_ids")
        for file_ids_item_data in _file_ids:
            file_ids_item = UUID(file_ids_item_data)

            file_ids.append(file_ids_item)

        legacy_knowledge_base_create_result = cls(
            detail=detail,
            kb_id=kb_id,
            kb_name=kb_name,
            file_ids=file_ids,
        )

        legacy_knowledge_base_create_result.additional_properties = d
        return legacy_knowledge_base_create_result

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
