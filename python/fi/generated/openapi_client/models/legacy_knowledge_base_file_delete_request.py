from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LegacyKnowledgeBaseFileDeleteRequest")


@_attrs_define
class LegacyKnowledgeBaseFileDeleteRequest:
    """
    Attributes:
        kb_id (None | Unset | UUID):
        delete_all (bool | Unset):  Default: False.
        file_ids (list[UUID] | Unset):
        excluded_file_ids (list[UUID] | Unset):
        file_names (list[str] | Unset):
    """

    kb_id: None | Unset | UUID = UNSET
    delete_all: bool | Unset = False
    file_ids: list[UUID] | Unset = UNSET
    excluded_file_ids: list[UUID] | Unset = UNSET
    file_names: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kb_id: None | str | Unset
        if isinstance(self.kb_id, Unset):
            kb_id = UNSET
        elif isinstance(self.kb_id, UUID):
            kb_id = str(self.kb_id)
        else:
            kb_id = self.kb_id

        delete_all = self.delete_all

        file_ids: list[str] | Unset = UNSET
        if not isinstance(self.file_ids, Unset):
            file_ids = []
            for file_ids_item_data in self.file_ids:
                file_ids_item = str(file_ids_item_data)
                file_ids.append(file_ids_item)

        excluded_file_ids: list[str] | Unset = UNSET
        if not isinstance(self.excluded_file_ids, Unset):
            excluded_file_ids = []
            for excluded_file_ids_item_data in self.excluded_file_ids:
                excluded_file_ids_item = str(excluded_file_ids_item_data)
                excluded_file_ids.append(excluded_file_ids_item)

        file_names: list[str] | Unset = UNSET
        if not isinstance(self.file_names, Unset):
            file_names = self.file_names

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if kb_id is not UNSET:
            field_dict["kb_id"] = kb_id
        if delete_all is not UNSET:
            field_dict["delete_all"] = delete_all
        if file_ids is not UNSET:
            field_dict["file_ids"] = file_ids
        if excluded_file_ids is not UNSET:
            field_dict["excluded_file_ids"] = excluded_file_ids
        if file_names is not UNSET:
            field_dict["file_names"] = file_names

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_kb_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                kb_id_type_0 = UUID(data)

                return kb_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        kb_id = _parse_kb_id(d.pop("kb_id", UNSET))

        delete_all = d.pop("delete_all", UNSET)

        _file_ids = d.pop("file_ids", UNSET)
        file_ids: list[UUID] | Unset = UNSET
        if _file_ids is not UNSET:
            file_ids = []
            for file_ids_item_data in _file_ids:
                file_ids_item = UUID(file_ids_item_data)

                file_ids.append(file_ids_item)

        _excluded_file_ids = d.pop("excluded_file_ids", UNSET)
        excluded_file_ids: list[UUID] | Unset = UNSET
        if _excluded_file_ids is not UNSET:
            excluded_file_ids = []
            for excluded_file_ids_item_data in _excluded_file_ids:
                excluded_file_ids_item = UUID(excluded_file_ids_item_data)

                excluded_file_ids.append(excluded_file_ids_item)

        file_names = cast(list[str], d.pop("file_names", UNSET))

        legacy_knowledge_base_file_delete_request = cls(
            kb_id=kb_id,
            delete_all=delete_all,
            file_ids=file_ids,
            excluded_file_ids=excluded_file_ids,
            file_names=file_names,
        )

        legacy_knowledge_base_file_delete_request.additional_properties = d
        return legacy_knowledge_base_file_delete_request

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
