from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LegacyKnowledgeBaseBulkDeleteRequest")


@_attrs_define
class LegacyKnowledgeBaseBulkDeleteRequest:
    """
    Attributes:
        kb_ids (list[UUID] | Unset):
    """

    kb_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kb_ids: list[str] | Unset = UNSET
        if not isinstance(self.kb_ids, Unset):
            kb_ids = []
            for kb_ids_item_data in self.kb_ids:
                kb_ids_item = str(kb_ids_item_data)
                kb_ids.append(kb_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if kb_ids is not UNSET:
            field_dict["kb_ids"] = kb_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _kb_ids = d.pop("kb_ids", UNSET)
        kb_ids: list[UUID] | Unset = UNSET
        if _kb_ids is not UNSET:
            kb_ids = []
            for kb_ids_item_data in _kb_ids:
                kb_ids_item = UUID(kb_ids_item_data)

                kb_ids.append(kb_ids_item)

        legacy_knowledge_base_bulk_delete_request = cls(
            kb_ids=kb_ids,
        )

        legacy_knowledge_base_bulk_delete_request.additional_properties = d
        return legacy_knowledge_base_bulk_delete_request

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
